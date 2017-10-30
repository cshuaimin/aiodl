from setuptools import setup
import re


with open('aiodl/__version__.py') as f:
    version = re.match(r'^__version__ = [\'"](.+)[\'"]$', f.read()).group(1)

with open('README.md') as f:
    long_description = f.read()

setup(
    name='aiodl',
    packages=['aiodl'],
    version=version,
    description='Aiodl -- Yet another command line download accelerator.',
    long_description=long_description,
    author='cshuaimin',
    author_email='chen_shuaimin@outlook.com',
    url='https://github.com/cshuaimin/aiodl',
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
            'aiodl = aiodl.__main__:main'
        ]
    }
)
