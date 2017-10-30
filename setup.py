import sys
from distutils.core import setup

if sys.version_info < (3, 5, 0):
    raise RuntimeError("Aiodl requires Python 3.5.0+")

setup(
    name = 'aiodl',
    packages=['aiodl'],
    version = '0.2.0-alpha',
    description = 'Aiodl -- Yet another command line download accelerator.',
    author = 'cshuaimin',
    author_email = 'chen_shuaimin@outlook.com',
    url = 'https://github.com/cshuaimin/aget',
    download_url = 'https://github.com/cshuaimin/aget/archive/v0.2.0-alpha.tar.gz',
    scripts=['main.py']
)
