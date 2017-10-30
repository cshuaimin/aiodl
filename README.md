## Aiodl
[![PyPI version](https://badge.fury.io/py/aiodl.svg)](https://badge.fury.io/py/aiodl)

Aiodl -- Yet another command line download accelerator.

## Features

- Accelerate the downloading process by using multiple connections for one file.
- Reasonable retries on network errors.
- Breakpoint resume.

## Requirements

- Python >= 3.5 Aiodl is written with Python 3.5 async/await syntax.

## Installation

```bash
$ pip3 install aiodl --user
```
or
```bash
$ sudo pip3 install aiodl
```

## Usage

Simply call `aiodl` with the URL:
```bash
$ aiodl https://dl.google.com/translate/android/Translate.apk

  File: Translate.apk
  Size: 16.8M
  Type: application/vnd.android.package-archive

 11%|████▎                                  | 1.78M/16.0M [00:03<00:26, 565KB/s]
```

Customize output file with '-o' or '--output' option:
```bash
$ aiodl https://dl.google.com/translate/android/Translate.apk -o Google_Translate.apk
```

See more arguments with
```bash
$ aiodl -h
```
