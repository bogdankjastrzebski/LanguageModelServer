#!/home/bodo/.pyenv/versions/common/bin/python
import os
import json
import argparse 
import google.generativeai as genai

from flask import Flask, request, jsonify


app = Flask(__name__)
PATH = '/home/bodo/.config/chatbot'
LOG_FILE = []


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, help='profile')
    parser.add_argument('--key',  type=str, help='key')
    parser.add_argument('--root', type=str, help='input file')
    parser.add_argument('--conv', type=str, help='conversation')
    parser.add_argument(
        '--port',
        type=int,
        default=65432,
        help='port',
    )
    parser.add_argument(
        '--nomarkdown',
        action='store_false',
        default=True,
        help="Disable markdown mode."
    )
    args = parser.parse_args()
    return args


def reset_log():
    with open(LOG_FILE[0], 'w') as f:
        f.write('start')


def log(message):
    with open(LOG_FILE[0], 'a') as f:
        f.write(message + '\n')


class Context:
    def __init__(self, args):
        self.markdown = not args.markdown
        self.conv = f'{args.root}/conv/{args.conv}.conv',
        genai.configure(api_key=args.key)
        self.chats = {
            n: (genai.GenerativeModel(name)
                .start_chat(history=self.load_history()))
            for n, name in [
                ('1.5', "gemini-1.5-flash"),
                ('2', "gemini-2.0-flash-exp"),
                ('2.pro', "gemini-exp-1206"),
                ('1.5.pro', "gemini-1.5-pro"),
            ]
        }
        self.chat = self.chats['2']
        if self.markdown:
            self.remember_about_markdown()

    def remember_about_markdown(self):
        log('Adding markdown instructions.')
        self.chat.history.append({
            'role': 'user',
            'parts': [
                'reply from now on markdown style, '
                'beginning with ```markdown and ending with ```. '
            ],
        })
        self.chat.history.append({
            'role': 'model',
            'parts': [
                "\n```markdown\nUnderstood, I'll write"
                "my responses everything markdown style\n```\n"
            ]
        })
        log('done.')

    def unmarkdown(self, text):
        # log(f"text: {text}")
        while len(text) != 0 and text[0] == '\n':
            text = text[1:]
        lhs = text[:11] != '```markdown'
        rhs = text[-3:] != '```'
        if lhs or rhs:
            log('No markdown detected.')
            self.remember_about_markdown()
            return text
        text = text[11:]
        text = text[:-3]
        return text

    def save_conversation(self, user_message, model_message):
        with open(self.conv, 'a') as f:
            f.write('\n' + json.dumps(user_message) + ',')
            f.write('\n' + json.dumps(model_message) + ',')

    def load_history(self):
        log('Loading history.')
        if not os.path.exists(self.conv):
            with open(self.conv, 'a') as f:
                os.utime(self.conv, None)
        with open(self.conv, 'r') as f:
            history = f.read()
            if len(history) > 0 and history[-1] == ',':
                history = history[:-1]
            self.history = json.loads('[' + history + ']')
        log('done.')

    def handle_chat(self, message):
        response = self.chat.send_message(message).text.strip()
        with open(self.conv, 'a') as f:
            f.write('\n' + json.dumps({
                'role': 'user',
                'parts': [message],
            }) + ',')
            f.write('\n' + json.dumps({
                'role': 'model',
                'parts': [response],
            }) + ',')
        return self.unmarkdown(response)

    def handle_history(self, message):
        try:
            length = int(message.strip())
        except:
            length = 5
        return jsonify(self.chat.history[-length:])
    
    def handle_context(self, message):
        user_message = {
            'role': 'user',
            'parts': [message],
        }
        model_message = {
            'role': 'model',
            'parts': [
                'Noted terminal output,'
                'awaiting instructions.'
            ],
        }
        self.chat.history.append(user_message)
        self.chat.history.append(model_message)
        self.save_conversation(user_message, model_message)
        return 'appended'
    
    def handle_model(self, message):
        if message in self.chats:
            history = self.chat.history
            self.chat.history = None
            self.chat = self.chats[message]
            self.chat.history = history
        else:
            log(f'No such chat. Tried to change to {message}.')
        return 'changed_model'


CONTEXT = None


def process_message(func):
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Invalid data format"}), 400
    message = data["message"]
    return jsonify(response=func(message))


@app.route('/chat', methods=['POST'])
def handle_chat():
    return process_message(CONTEXT.handle_chat)


@app.route('/history', methods=['POST'])
def handle_history():
    return process_message(CONTEXT.handle_history)


@app.route('/context', methods=['POST'])
def handle_context():
    return process_message(CONTEXT.handle_history)


@app.route('/model', methods=['POST'])
def handle_model():
    return process_message(CONTEXT.handle_model)


if __name__ == "__main__":
    args = parse_args()
    
    CONTEXT = Context(args)

    # Verbose:
    LOG_FILE.append(f'{PATH}/log/{args.name}_{args.conv}.log')
    reset_log()
    log(f'Activating chat: {args}')
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=args.port,
    )
