# helper functions

def input_yesno(msg):
    answer = str(input(msg + ' (y/n): ')).lower()
    if answer in ['yes', 'y']:
        return True
    elif answer in ['no', 'n']:
        return False
    else:
        print('Invalid input. Try again.')
        return input_yesno(msg)
