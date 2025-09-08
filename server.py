#!/home/bodo/.pyenv/versions/common/bin/python
import os
import json
import argparse 
import google.generativeai as genai
from flask import Flask, request, jsonify
import logging


app = Flask(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--key', type=str, help='key')
    parser.add_argument('--root', type=str, help='root of config')
    parser.add_argument(
        '--prompt',
        default="prompt.prompt",
        type=str,
        help='prompt file',
    )
    parser.add_argument(
        '--conv',
        default='default',
        type=str,
        help='conversation',
    )
    parser.add_argument(
        '--port',
        type=int,
        default=65432,
        help='port',
    )
    args = parser.parse_args()
    return args


class Context:
    def __init__(self, args):
        self.conv = f'{args.root}/conv/{args.conv}.conv'
        genai.configure(api_key=args.key)
        self.chats = {
            n: (genai.GenerativeModel(name)
                .start_chat(history=self.load_history()))
            for n, name in [
                ('1.5', "gemini-1.5-flash"),
                ('2', "gemini-2.0-flash-exp"),
                ('2.pro', "gemini-exp-1206"),
                ('1.5.pro', "gemini-1.5-pro"),
                ('2.5.pro', 'gemini-2.5-pro'),
                ('2.5.flash', 'gemini-2.5-flash'),
            ]
        }
        self.chat = self.chats['2.5.flash']
        self.chat_name = '2.5.flash'
        with open(f'{args.root}/prompts/{args.prompt}', 'r') as f:
            self.prompt = f.read()
        self.remember_about_prompt()

    def remember_about_prompt(self):
        logging.info('Adding prompt instructions.')
        self.chat.history.append({
            'role': 'user',
            'parts': [self.prompt],
        })
        self.chat.history.append({
            'role': 'model',
            'parts': [
                "\n```markdown\nUnderstood, I'll write"
                "my responses as requested\n```\n"
            ]
        })
        logging.info('done.')

    def handle_remember(self):
        self.remember_about_prompt()
        return 'ok'

    def unmarkdown(self, text):
        # log(f"text: {text}")
        while len(text) != 0 and text[0] == '\n':
            text = text[1:]
        lhs = text[:11] != '```markdown'
        rhs = text[-3:] != '```'
        if lhs or rhs:
            logging.warning('No markdown detected.')
            self.remember_about_prompt()
            return text
        text = text[11:]
        text = text[:-3]
        return text

    def save_conversation(self, user_message, model_message):
        with open(self.conv, 'a') as f:
            f.write('\n' + json.dumps(user_message) + ',')
            f.write('\n' + json.dumps(model_message) + ',')

    def load_history(self):
        logging.info('Loading history.')
        if not os.path.exists(self.conv):
            logging.info('Creating history file.')
            with open(self.conv, 'a') as f:
                os.utime(self.conv, None)
        with open(self.conv, 'r') as f:
            history = f.read()
            if len(history) > 0 and history[-1] == ',':
                history = history[:-1]
            self.history = json.loads('[' + history + ']')
        logging.info('Done loading history.')

    def handle_chat(self, message):
        logging.info(f'Sending message: {message}')
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
        return self.chat.history[-length:]
    
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
    
    def handle_model_post(self, message):
        if message in self.chats:
            history = self.chat.history
            self.chat.history = None
            self.chat = self.chats[message]
            self.chat.history = history
            self.chat_name = message
        else:
            logging.error(
                f'No such chat. Tried to change to {message}.'
            )
        return 'changed_model'

    def handle_model_get(self):
        return self.chat_name


CONTEXT = None


def process_message(func):
    logging.info('Processing message.')
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Invalid data format"}), 400
    message = data["message"]
    logging.info(f'message: {message}')
    return func(message)


@app.route('/chat', methods=['POST'])
def handle_chat():
    return jsonify(response=process_message(CONTEXT.handle_chat))


@app.route('/history', methods=['POST'])
def handle_history():
    return jsonify(response=process_message(CONTEXT.handle_history))


@app.route('/context', methods=['POST'])
def handle_context():
    return jsonify(response=process_message(CONTEXT.handle_context))


@app.route('/model', methods=['POST'])
def handle_model_post():
    return jsonify(response=process_message(CONTEXT.handle_model_post))


@app.route('/model', methods=['GET'])
def handle_model_get():
    return jsonify(response=CONTEXT.handle_model_get())


@app.route('/remember', methods=['POST'])
def handle_remember():
    return jsonify(response=process_message(CONTEXT.handle_remember()))


if __name__ == "__main__":
    args = parse_args()

    if args.key is None:
        if os.path.exists(f'{args.root}/gemini.key'):
            with open(f'{args.root}/gemini.key', 'r') as f:
                args.key = f.read().strip()
        else:
            raise Exception('No key detected!')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s'
               ' - %(name)s - %(message)s'
    )

    logging.info(
        f'Activating chat: root={args.root} conv={args.conv} '
        f'port={args.port} prompt={args.prompt}')

    logging.info('Creating context.')
    CONTEXT = Context(args)

    logging.info('Running server.')
    app.run(
        debug=True,
        host='127.0.0.1',
        port=args.port,
    )
