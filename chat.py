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
        'remember also to put \\ before each single quote \''
    ],
}


MD_MODEL = {
    'role': 'model',
    'parts': [
        "\n```markdown\nUnderstood, I'll write"
        "my responses everything markdown style\n```\n"
    ]
}


class MessageHandler(FileSystemEventHandler):
    def __init__(self, input, output, conv, chat, markdown):
        super().__init__()
        self.input = input
        self.output = output
        self.conv = conv
        self.chat = chat
        self.markdown = markdown
        if self.markdown:
            self.remember_about_markdown()
        log(f'input:  {args.root}/tmp/{args.name}_question.txt')
        log(f'output: {args.root}/tmp/{args.name}_response.txt')
        log(f'conv:   {args.root}/conv/{args.conv}.conv')

    def remember_about_markdown(self):
        log('Adding markdown instructions.')
        self.chat.history.append(MD_USER)
        self.chat.history.append(MD_MODEL)
        log('done.')
        # with open(self.conv, 'a') as f:
        #    f.write('\n' + json.dumps(MD_USER) + ',')
        #    f.write('\n' + json.dumps(MD_MODEL) + ',')

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

    def on_modified(self, event):
        # log(f'Type event: {type(event)}')
        if (isinstance(event, FileModifiedEvent)
                and event.src_path == self.input):
            log("Sending message activated.")
            try:
                with open(event.src_path, 'r') as f:
                    message = f.read().strip()

                if message == '__test_message__':
                    log("TEST Sending message.")
                    response = chat.send_message('Do you copy?')
                    log(f'response: \n {response.text}')
                    log(f'unmarkdown: {self.unmarkdown(response.text.strip())}')
                    log("TEST done.")
                    return

                response = chat.send_message(message)
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
                os.remove(self.input)
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
    model = genai.GenerativeModel(
        # "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
    )
    chat = model.start_chat(history=history)
    log('done.')
    
    log('Making handler.')
    event_handler = MessageHandler(
        f'{args.root}/tmp/{args.name}_question.txt',
        f'{args.root}/tmp/{args.name}_response.txt',
        f'{args.root}/conv/{args.conv}.conv',
        chat,
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
