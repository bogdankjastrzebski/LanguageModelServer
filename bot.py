#!/home/bodo/.pyenv/versions/common/bin/python
import os
import sys
import argparse 
import time
import signal
import subprocess

PYENV = '/home/bodo/.pyenv/versions/common/bin/python'
PATH = '/home/bodo/.config/chatbot'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('message', nargs='?', default='', type=str, help='message')
    parser.add_argument('--name', default='watcher', type=str, help='profile')
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
    args = parser.parse_args()
    return args
    

def send_message(args, message):
    name = args.name
    question = f'{args.root}/tmp/{name}_question.txt'
    response = f'{args.root}/tmp/{name}_response.txt'
    if os.path.exists(response):
        os.remove(response)
    with open(question, 'w') as f:
        f.write(message)
    if message == '__test_message__':
        return

    try:
        while not os.path.exists(response):
            time.sleep(0.1)
        with open(response, 'r') as f:
            text = f.read()
        # os.remove(response)
        return text

    except KeyboardInterrupt:
        exit(1)


if __name__ == '__main__':
    args = parse_args()
    
    assert args.name != '', 'Enter name.'
    assert args.conversation != '', 'Enter conversation file.'
    # if len(args.message) > 0:
    #     message = ' '.join(args.message)
    # else:
    #     message = sys.stdin.read().strip()
    # if len(args.message) == 0:
    #     message = sys.stdin.read().strip()

    name = args.name

    match args.message:
        case 'activate':
            print('Activating... ', end='')
            if os.path.exists(f'{args.root}/tmp/{name}.pid'):
                print('already active.')
                exit(1)
            with open(f'{args.root}/{args.key}', 'r') as f:
                key = f.read()

            # if len(args.name) < 3:
            #     raise Exception(
            #         f"The name should be at least 3 characters: {args.name}"
            #     )

            command = f"""{PYENV} {args.root}/chat.py
                --name={name}
                --key={key}
                --root={args.root}
                --conv={args.conversation}
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
        case 'help':
            print("""
            make-conversation: 
            list: open list
            repl: open repl
            """)
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

        case message:
            print(send_message(args, message))

