import random

from termcolor import colored, COLORS
from tqdm import tqdm


colors = list(COLORS.keys())


def print_colored_kv(k, v):
    tqdm.write(
        colored('  ' + k + ': ', color=random.choice(colors), attrs=['bold']) +
        colored(v, color='white', attrs=['bold'])
    )
