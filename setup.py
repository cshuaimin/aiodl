from setuptools import setup
import os

from aiodl import __version__

setup(
    name = 'aiodl',
    packages=['aiodl'],
    version = __version__,
    description = 'Aiodl -- Yet another command line download accelerator.',
    author = 'cshuaimin',
    author_email = 'chen_shuaimin@outlook.com',
    url = 'https://github.com/cshuaimin/aiodl',
    python_requires='>=3.5',
    install_requires=['aiohttp', 'tqdm', 'termcolor', 'argparse'],

    classifiers=[
        'Development Status :: 3 - Alpha',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    license="MIT",
    keywords='asynchronous download',
    entry_points={
        'console_scripts': [
            'aiodl = aiodl.main:main'
        ]
    }
)
