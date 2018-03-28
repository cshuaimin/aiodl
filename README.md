## Aiodl
[![PyPI version](https://badge.fury.io/py/aiodl.svg)](https://badge.fury.io/py/aiodl)

Aiodl -- Yet another command line download accelerator.

## Features

- Accelerate the downloading process by using multiple connections for one file.
- Reasonable retries on network errors.
- Breakpoint resume.

## Installation

```bash
$ pip3 install aiodl --user
# or
$ sudo pip3 install aiodl
```

## Usage

### Commandline
Simply call `aiodl` with the URL:
```console
$ aiodl https://dl.google.com/translate/android/Translate.apk

  File: Translate.apk
  Size: 16.8M
  Type: application/vnd.android.package-archive

 11%|████▎                                  | 1.78M/16.0M [00:03<00:26, 565KB/s]
```

Hit Ctrl+C to stop the download. Aiodl will save necessary information to `<download-file>.aiodl`, next time it will automatically continue to download from here.

Other arguments:

```
--fake-user-agent, -u  Use a fake User-Agent.
--num-tasks N, -n N    Limit number of asynchronous tasks.
--max-tries N, -r N    Limit retries on network errors.
```

### In your script

```python
import aiodl

# in an async function
filename = await aiodl.download('https://dl.google.com/translate/android/Translate.apk', quiet=True)
```
