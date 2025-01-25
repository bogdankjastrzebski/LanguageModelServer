#!/home/bodo/.pyenv/versions/common/bin/python
import os
import argparse 
import signal
import subprocess
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from PyPDF2 import PdfReader
from io import BytesIO


PYENV = '/home/bodo/.pyenv/versions/common/bin/python'
PATH = '/home/bodo/.config/chatbot'


HELP = """
activate: activates chat
deactivate: deactivates chat
list: open list
make-conversation: makes a new conversation
test: ping server
whoru: returns running model name
repl: open repl
model <name>: changes model to <name> 
search <query>: appends results from the internet to context
append <message>: appends <message> to context
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'message',
        nargs='?',
        default='',
        type=str,
        help='message',
    )
    parser.add_argument(
        '--name',
        default='watcher',
        type=str,
        help='profile',
    )
    parser.add_argument(
        '--key',
        default='gemini.key',
        type=str,
        help='key',
    )
    parser.add_argument(
        '--root',
        default=f'{PATH}',
        type=str, help='question file')
    parser.add_argument(
        '--conversation',
        default='default',
        type=str, help='conversation file'
    )
    parser.add_argument(
        '--nomarkdown',
        action='store_false',
        default=True,
        help="Disable markdown mode"
    )
    parser.add_argument(
        '--nomarkdown',
        action='store_false',
        default=True,
        help="Disable markdown mode"
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        type=str,
        help="Host."
    )
    parser.add_argument(
        '--port',
        default=65432,
        type=int,
        help="Port."
    )
    args = parser.parse_args()
    return args


def extract_text_from_url(url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type')
        if 'html' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = ' '.join(soup.get_text(separator=' ', strip=True).split())
        elif 'pdf' in content_type:
            pdf_file = BytesIO(response.content)
            pdf_reader = PdfReader(pdf_file)
            text = ''
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text = text + page_text
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None


def search(search_query, num_results=4, timeout=5):
    result = DDGS().text(
        keywords=search_query,
        region='wt-wt',
        safesearch='off',
        timelimit='1m',
        max_results=num_results,
    )
    rest = [
        extract_text_from_url(res['href'], timeout)
        for res in result
    ]
    return rest


def search_web(args, message, limit=50000):
    texts = search(message[7:])
    for text in texts:
        append_message(args, text[:limit])


def send(args, endpoint, message):
    url = f"http://{args.host}:{args.port}/{endpoint}"
    headers = {'Content-type': 'application/json'}
    response = requests.post(
        url,
        json={'message': message},
        headers=headers,
    ) 
    return response.json()  # ['message']


def change_model(args, message):
    assert send(args, 'model', message.split()[1]) == 'changed_model'

#     try:
#         # assert model_name in ['1.5.pro', '1.5.pro', '2', '2.pro']
#     except Exception as e:
#         print('Error: Provide model name: 1.5.pro, 2.pro, 1.5 or 2')
#         print(e)


def print_history(args, message):
    twople = message.split()
    if len(twople) == 2:
        history_length = twople[1]
    else:
        history_length = '5'
    return send(args, 'history', history_length)


def append_message(args, message):
    text = send(args, 'context', message.split()[1])
    assert text == 'appended'


def send_message(args, message):
    return send(args, 'context', message)


if __name__ == '__main__':
    args = parse_args()

    assert args.name != '', 'Enter name.'
    assert args.conversation != '', 'Enter conversation file.'

    name = args.name

    match args.message.strip():
        case 'activate':
            print('Activating... ', end='')
            if os.path.exists(f'{args.root}/tmp/{name}.pid'):
                print('already active.')
                exit(1)
            with open(f'{args.root}/{args.key}', 'r') as f:
                key = f.read()
            command = f"""{PYENV} {args.root}/chat.py
                --name={name}
                --key={key}
                --root={args.root}
                --conv={args.conversation}
                --port={args.port}
            """.split()
            if args.nomarkdown:
                command.append('--nomarkdown')
            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=None,
            )
            if process:
                pid = process.pid
                with open(f'{args.root}/tmp/{name}.pid', 'w') as f:
                    f.write(str(pid))
                print(f'done. (pid: {pid})')
            else:
                print('failed.')
        case 'deactivate':
            print('Deactivating... ', end='')
            if not os.path.exists(f'{args.root}/tmp/{name}.pid'):
                print('nothing to deactivate.')
                exit(1)
            with open(f'{args.root}/tmp/{name}.pid', 'r') as f:
                pid = int(f.read())
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            os.remove(f'{args.root}/tmp/{name}.pid')
            print('done.')
        case 'list':
            print('NAME\tPID')
            for file in os.listdir(f'{args.root}/tmp'):
                if file[-4:] == '.pid':
                    with open(f'{args.root}/tmp/{file}', 'r') as f:
                        pid = f.read()
                    print(f'{file[:-4]}\t{pid}')

        case 'make-conversation':
            print("Conversation name:", end='')
            name = input()
            assert len(name) > 3, \
                "should be more than 3 characters"
            path = f'{args.root}/conv/{name}.conv'
            assert not os.path.exists(path), \
                "conversation already exists"
        case 'test':
            print("begin 1. TEST")
            print(send_message(args, '__test_message__'))
            print("end 1. TEST")
        case 'whoru':
            path = f'{args.root}/tmp/{name}_model.type'
            if os.path.exists(path):
                with open(path, 'r') as f:
                    print(f.read())
            else:
                print('default (2)')
        case 'repl':
            while True:
                try:
                    message = input()
                    reply = send_message(args, message)
                    print(reply)
                except KeyboardInterrupt:
                    exit(1)
                except Exception:
                    continue
        case 'help':
            print(HELP)
        case message if message.startswith('model'):
            change_model(args, message)
        case message if message.startswith('append'):
            append_message(args, message)
        case message if message.startswith('search'):
            search_web(args, message)
        case message if message.startswith('history'):
            print(print_history(args, message))
        case message:
            print(send_message(args, message))


