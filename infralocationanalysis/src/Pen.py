COLORS = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKCYAN': '\033[96m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}


def write(text, color='WARNING', newline=True):
    if newline:
        print(f"{COLORS[color]}{text}{COLORS['ENDC']}")
    else:
        print(f"{COLORS[color]}{text}{COLORS['ENDC']}", end='')

