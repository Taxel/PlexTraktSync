# helper functions

import getpass
import json

def input_text(msg, default):
    answer = input('{0} ({1}): '.format(msg, default))

    if answer == '':
        print(default)
        return default

    return answer

def input_hidden(msg):
    reply = getpass.getpass(prompt = msg)

    return reply

def input_yesno(msg):
    answer = str(input(msg + ' (y/n): ')).lower()
    if answer in ['yes', 'y']:
        return True
    elif answer in ['no', 'n']:
        return False
    else:
        print('Invalid input. Try again.')
        return input_yesno(msg)

def load_json(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    return data
