### 开始使用

```bash
$ alias aget='python3 ~/aget/main.py'
$ aget https://dl.google.com/translate/android/Translate.apk
INFO	Length: 16.0MB [application/vnd.android.package-archive]
INFO	Saving to: 'Translate.apk'
 39%|████████████████████████████████████▌                                                         | 6.21M/16.0M [00:08<00:12, 793KB/s]
^CINFO	saving status to Translate.apk.aget_st
```

### 特性

* 通过同时下载多个片段来提高速度
* 断点续传
