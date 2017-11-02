from setuptools import setup
import re


with open('aiodl/version.py') as f:
    version = re.match(r'^__version__ = [\'"](.+)[\'"]$', f.read()).group(1)

setup(
    name='aiodl',
    packages=['aiodl'],
    version=version,
    description='Aiodl -- Yet another command line download accelerator.',
    setup_requires=['setuptools-markdown'],
    long_description_markdown_filename='README.md',
    author='cshuaimin',
    author_email='chen_shuaimin@outlook.com',
    url='https://github.com/cshuaimin/aiodl',
    python_requires='>=3.5',
    install_requires=['aiohttp', 'tqdm', 'termcolor', 'argparse', 'fake_useragent'],

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
            'aiodl = aiodl.__main__:main'
        ]
    }
)
