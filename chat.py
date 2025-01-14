#!/home/bodo/.pyenv/versions/common/bin/python
import os
import json
import argparse 
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


PATH = '/home/bodo/.config/chatbot'
LOG_FILE = []


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, help='profile')
    parser.add_argument('--key', type=str, help='key')
    parser.add_argument('--root', type=str, help='input file')
    parser.add_argument('--conv', type=str, help='conversation')
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


MD_USER = {
    'role': 'user',
    'parts': [
        'reply from now on markdown style, '
        'beginning with ```markdown and ending with ```. '
    ],
}

# 'remember also to put \\ before each single quote \''

MD_MODEL = {
    'role': 'model',
    'parts': [
        "\n```markdown\nUnderstood, I'll write"
        "my responses everything markdown style\n```\n"
    ]
}


class MessageHandler(FileSystemEventHandler):
    def __init__(self,
                 input,
                 output,
                 context,
                 model,
                 conv,
                 chats,
                 markdown):
        super().__init__()
        log(f'a')
        # Paths
        self.input = input
        self.output = output
        self.context = context
        self.model = model
        # 
        log(f'b')
        self.conv = conv
        self.chats = chats
        self.chat = chats['2']
        self.markdown = markdown
        log(f'c')
        if self.markdown:
            self.remember_about_markdown()
        log(f'input:  {input}')
        log(f'output: {output}')
        log(f'context: {context}')
        log(f'model:   {model}')
        log(f'conv:   {conv}')

    def remember_about_markdown(self):
        log('Adding markdown instructions.')
        self.chat.history.append(MD_USER)
        self.chat.history.append(MD_MODEL)
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

    def handle_model(self, message):
        if message in self.chats:
            history = self.chat.history
            self.chat.history = None
            self.chat = self.chats[message]
            self.chat.history = history
        else:
            log(f'No such chat. Tried to change to {message}.')
        with open(self.output, 'w') as f:
            f.write('changed_model')

    def handle_chat(self, message):
        response = self.chat.send_message(message)
        with open(self.conv, 'a') as f:
            f.write('\n' + json.dumps({
                'role': 'user',
                'parts': [message],
            }) + ',')
            f.write('\n' + json.dumps({
                'role': 'model',
                'parts': [response.text.strip()],
            }) + ',')
        text = response.text.strip()
        # if self.markdown:
        text = self.unmarkdown(text)
        with open(self.output, 'w') as f:
            f.write(text)

    def handle_context(self, message):
        user_message = {
            'role': 'user',
            'parts': [message],
        }
        model_message = {
            'role': 'model',
            'parts': ['Noted terminal output, awaiting instructions.'],
        }
        self.chat.history.append(user_message)
        self.chat.history.append(model_message)
        with open(self.conv, 'a') as f:
            f.write('\n' + json.dumps(user_message) + ',')
            f.write('\n' + json.dumps(model_message) + ',')
        with open(self.output, 'w') as f:
            f.write('appended')

    def on_modified(self, event):
        # log(f'Type event: {type(event)}')
        if not isinstance(event, FileModifiedEvent):
            return
        log('A')
        if event.src_path not in [
                    self.input,
                    self.context,
                    self.model,
                ]:
            return
        log('B')

        log(f"Sending message activated: {event.src_path}")
        try:
            with open(event.src_path, 'r') as f:
                message = f.read().strip()
            log('C')

            if message == '__test_message__':
                log("TEST Sending message.")
                response = self.chat.send_message('Do you copy?')
                log(f'response: \n {response.text}')
                log(f'unmarkdown: {self.unmarkdown(response.text.strip())}')
                log("TEST done.")
                return
            
            log('D')
            match event.src_path:
                case self.input:
                    log('E')
                    self.handle_chat(message)
                    os.remove(self.input)
                case self.context:
                    log('F')
                    self.handle_context(message)
                    os.remove(self.context)
                case self.model:
                    log('G')
                    self.handle_model(message)
                    # os.remove(self.model) # for reading
                case unk:
                    raise Exception(f"unexpected path: {unk}")
            
        except Exception as e:
            log(f"Exception while sending message: {e}")
        log('Done sending message.')


if __name__ == "__main__":
    args = parse_args()

    # Verbose:
    LOG_FILE.append(f'{PATH}/log/{args.name}_{args.conv}.log')
    reset_log()
    log(f'Activating chat: {args}')

    # History
    log('Loading history.')
    conv_path = f'{args.root}/conv/{args.conv}.conv'
    if not os.path.exists(conv_path):
        with open(conv_path, 'a') as f:
            os.utime(conv_path, None)
    with open(conv_path, 'r') as f:
        history = f.read()
        if len(history) > 0 and history[-1] == ',':
            history = history[:-1]
        history = json.loads('[' + history + ']')
    log('done.')
          
    # Chat
    log('Creating chat. GEMINI 2.0')
    genai.configure(api_key=args.key)
    models = [
        (n, genai.GenerativeModel(name))
        for n, name in [
            ('1.5', "gemini-1.5-flash"),
            ('2', "gemini-2.0-flash-exp"),
            ('pro', "gemini-exp-1206"),
        ]
    ]
    chats = {
        n: model.start_chat(history=history)
        for (n, model) in models
    }
    log('done.')
    
    log('Making handler.')
    event_handler = MessageHandler(
        f'{args.root}/tmp/{args.name}_question.txt',
        f'{args.root}/tmp/{args.name}_response.txt',
        f'{args.root}/tmp/{args.name}_context.txt',
        f'{args.root}/tmp/{args.name}_model.type',
        f'{args.root}/conv/{args.conv}.conv',
        chats,
        not args.nomarkdown,
    )
    log('done.')
    
    log('Making observer.')
    observer = Observer()
    observer.schedule(
        event_handler,
        path=f'{args.root}/tmp',
        recursive=False,
    )
    log('done.')
    
    log('Starting observer.')
    observer.start()
    log('done.')
    log('Observer join.')
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    log('done.')
