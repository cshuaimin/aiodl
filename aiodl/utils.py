import asyncio
import aiohttp
import random
import functools
import socket

from contextlib import contextmanager
from termcolor import colored, COLORS
from tqdm import tqdm


colors = list(COLORS)


def print_colored_kv(k, v):
    tqdm.write(
        colored('  ' + k + ': ', color=random.choice(colors), attrs=['bold']) +
        colored(v, color='white', attrs=['bold'])
    )


class AiodlQuitError(Exception):
    'Something caused aiodl to quit.'


class ClosedRange:
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

    def __iter__(self):
        yield self.begin
        yield self.end

    def __str__(self):
        return '[{0.begin}, {0.end}]'.format(self)

    # Why not __len__() ? See https://stackoverflow.com/questions/47048561/
    @property
    def size(self):
        return self.end - self.begin + 1


def retry(coro_func):
    @functools.wraps(coro_func)
    async def wrapper(self, *args, **kwargs):
        tried = 0
        while True:
            tried += 1
            try:
                return await coro_func(self, *args, **kwargs)
            except (aiohttp.ClientError, socket.gaierror) as exc:
                try:
                    msg = '%d %s' % (exc.code, exc.message)
                    # For 4xx client errors, it's no use to try again :)
                    if 400 <= exc.code < 500:
                        tqdm.write(msg)
                        raise AiodlQuitError from exc
                except AttributeError:
                    msg = str(exc) or exc.__class__.__name__
                if tried <= self.max_tries:
                    sec = tried / 2
                    tqdm.write(
                        '%s() failed: %s, retry in %.1f seconds (%d/%d)' %
                        (coro_func.__name__, msg,
                         sec, tried, self.max_tries)
                    )
                    await asyncio.sleep(sec)
                else:
                    tqdm.write(
                        '%s() failed after %d tries: %s ' %
                        (coro_func.__name__, self.max_tries, msg)
                    )
                    raise AiodlQuitError from exc
            except asyncio.TimeoutError:
                # Usually server has a fixed TCP timeout to clean dead
                # connections, so you can see a lot of timeouts appear
                # at the same time. I don't think this is an error,
                # So retry it without checking the max retries.
                tqdm.write(
                    '%s() timeout, retry in 1 second' % coro_func.__name__)
                await asyncio.sleep(1)
    return wrapper


@contextmanager
def connecting(connecting='  Connecting'):
    length = len(connecting)
    print(colored(connecting, 'grey', attrs=['bold']), end='', flush=True)
    async def print_dots():
        while True:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            print(colored('.', 'grey', attrs=['bold']), end='', flush=True)
            nonlocal length
            length += 1
    fut = asyncio.ensure_future(print_dots())
    yield
    fut.cancel()
    print('\r' + ' ' * length)
