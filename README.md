### Simple usage:

```bash
➜  alias aget='python3 ~/code/aget/main.py'
➜  aget -h                                 
usage: main.py [-h] [--output OUTPUT] [--num-blocks NUM_BLOCKS]
               [--max-retries MAX_RETRIES] [--verbose] [--quiet]
               url

Download files asynchronously in a single thread!

positional arguments:
  url                   URL to download

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        output file
  --num-blocks NUM_BLOCKS, -n NUM_BLOCKS
                        number of blocks
  --max-retries MAX_RETRIES, -r MAX_RETRIES
                        number of retries
  --verbose, -v         verbose logging (repeat for more verbose)
  --quiet, -q           only log errors
➜  aget https://dl.google.com/translate/android/Translate.apk
INFO:__main__:saving to Translate.apk ...
100%|██████████████████████████████████████████| 16.0M/16.0M [00:36<00:00, 458KB/s]
```
