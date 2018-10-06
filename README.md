# fserver
a simple http.server implement by flask

```
usage: server.py [-h] [-p PORT] [port]

positional arguments:
  port                  Specify alternate port [default: 2000]

optional arguments:
  -h, --help            show this help message and exit

arguments of url:
  m                     get_arg to set the mode of processing method of file
                        Such as http://localhost:port?m=dv to download the file specified by url
                        value 'p' to play file with Dplayer
                        value 'v' to show the file specified by url
                        value 'dv' to download the file specified by url
```
