# -*- coding: utf-8 -*-
import os
import signal
import sys

import gevent
import logging
from gevent.pywsgi import WSGIServer

from fserver import conf
from fserver import logger
from fserver import path_util
from fserver import network_util
from fserver.fogging import colorize, Color
from fserver.fserver_app import app as application

usage_short = 'usage: fserver [-h] [-d] [-u] [-o] [-n] [-i ADDRESS] [-s CONTENT] [-w PATH] [-b PATH] [-r PATH] [port]'
usage = '''
Usage:
  fserver [-h] [-d] [-u] [-o] [-n] [-i ADDRESS] [-s CONTENT] [-w PATH] [-b PATH] [-r PATH] [port]

Positional arguments:
  port                                Specify alternate port, default value 2000

Optional arguments:

  -h, --help                          Show this help message and exit
  -d, --debug                         Use debug mode of fserver
  -u, --upload                        Open upload file function. This function is closed by default
  -o, --override                      Set upload file with override mode, only valid when [-u] is used
  -n, --nosort                        Do not sort the files for list
  -i ADDRESS, --ip ADDRESS            Specify alternate bind address [default: all interfaces]
  -r PATH, --root PATH                Set PATH as root path for server
  -w PATH, --white PATH               Use white_list mode. Only PATH, sub directory or file, will be share. 
                                      You can use [-wi PATH], i is num from 1 to 23, to share 24 PATHs at most    
  -b PATH, --black PATH               Use black_list mode. It's similar to option '-w'    
  -s CONTENT, --string CONTENT        Share string content, while disable the share of file
 '''


def run_fserver():
    # init conf
    try:
        CmdOption().init_conf(sys.argv[1:])
    except OptionError as e:
        print('ERROR: {}\n\n{}\n'.format(e.msg, usage_short))
        sys.exit(-1)

    if conf.DEBUG:
        conf.display()
    logger.setLevel(logging.DEBUG if conf.DEBUG else logging.INFO)
    print('fserver is available at following address:')
    if conf.BIND_IP == '0.0.0.0':
        ips = network_util.get_ip_v4()
        for _ip in ips:
            print('  http://%s:%s' % (_ip, conf.BIND_PORT))
    else:
        print('  http://%s:%s' % (conf.BIND_IP, conf.BIND_PORT))

    gevent.signal(signal.SIGINT, _quit)
    gevent.signal(signal.SIGTERM, _quit)
    http_server = WSGIServer((conf.BIND_IP, int(conf.BIND_PORT)), application)
    try:
        http_server.serve_forever()
    except OSError as e:
        print(colorize(e, Color.RED))


class OptionError(Exception):
    def __init__(self, msg):
        self.msg = msg


def getopt(args, short_opts, long_opts=None):
    if long_opts is None:
        long_opts = []
    opts_2 = [('-' + i.replace(':', ''), True if i.endswith(':') else False) for i in short_opts if i is not None]
    opts_2.extend([('--' + i.replace('=', ''), True if i.endswith('=') else False) for i in long_opts if i is not None])
    options = dict()
    for ind, value in enumerate(args):
        if value is None:
            continue
        recognized = False
        for name, has_value in opts_2:
            if value == name:
                v = ''
                if has_value:
                    if ind == len(args) - 1:
                        raise OptionError('ERROR: option %s requires argument' % value)
                    v = args[ind + 1]
                    args[ind + 1] = None
                options[value] = v
                recognized = True
                break
        if recognized:
            args[ind] = None
        elif value.startswith('-') and value != '-' and value != '--':
            raise OptionError('ERROR: option %s not recognized' % value)

    none_count = 0
    for v in args:
        if v is None:
            none_count += 1
    for ind, value in enumerate(args):
        if value is not None and ind < none_count:
            raise OptionError(value)

    argv = [i for i in args if i is not None]
    return options, argv


class CmdOption:
    def __init__(self):
        pass

    OPTIONS = {
        'help': ('h', 'help', ['--help', '-h']),
        'debug': ('d', 'debug', ['--debug', '-d']),
        'upload': ('u', 'upload', ['--upload', '-u']),
        'override': ('o', 'override', ['--override', '-o']),
        'nosort': ('n', 'nosort', ['--nosort', '-n']),
        'version': ('v', 'version', ['--version', '-v']),
        'ip': ('i:', 'ip=', ['--ip', '-i']),
        'white': ('w:', 'white=', ['--white', '-w']),
        'black': ('b:', 'black=', ['--black', '-b']),
        'root': ('r:', 'root=', ['--root', '-r']),
        'string': ('s:', 'string=', ['--string', '-s'])
    }
    for i in range(1, 24):
        OPTIONS['white%s' % i] = ('w%s:' % i, 'white%s=' % i, ['--white%s' % i, '-w%s' % i])
        OPTIONS['black%s' % i] = ('b%s:' % i, 'black%s=' % i, ['--black%s' % i, '-b%s' % i])

    def init_conf(self, string):
        short_opts = []
        long_opts = []
        for item in self.OPTIONS.items():
            short_opts.append(item[1][0])
            long_opts.append(item[1][1])

        try:
            options, args = getopt(string, short_opts, long_opts)
        except OptionError as e:
            print(usage_short)
            print(e.msg)
            sys.exit()

        if len(args) > 0:
            conf.BIND_PORT = args[0]

        tmp_white_list = set()
        tmp_black_list = set()
        for name, value in options.items():
            value = path_util.to_unicode_str(value)
            if name in self.OPTIONS['help'][2]:
                print(usage)
                sys.exit()
            if name in ['-v', '--version']:
                print('fserver %s build at %s' % (conf.VERSION, conf.BUILD_TIME))
                print('Python %s' % sys.version)
                sys.exit()
            if name in self.OPTIONS['debug'][2]:
                conf.DEBUG = True
                continue
            if name in self.OPTIONS['upload'][2]:
                conf.UPLOAD = True
                continue
            if name in self.OPTIONS['nosort'][2]:
                conf.SORT = False
                continue
            if name in self.OPTIONS['override'][2]:
                conf.UPLOAD_OVERRIDE_MODE = True
                continue
            if name in self.OPTIONS['ip'][2]:
                conf.BIND_IP = value
                continue
            if name in self.OPTIONS['root'][2]:
                conf._ROOT = path_util.normalize_path(value)
                continue
            if name in self.OPTIONS['string'][2]:
                conf.STRING = value
                tmp_white_list.add(path_util.to_unicode_str(''))  # disable share file
            for white_opt in self.OPTIONS.keys():
                if not white_opt.startswith('white'):
                    continue
                if name in self.OPTIONS[white_opt][2]:
                    p = path_util.to_local_abspath(value)
                    tmp_white_list.add(p)
            for black_opt in self.OPTIONS.keys():
                if not black_opt.startswith('black'):
                    continue
                if name in self.OPTIONS[black_opt][2]:
                    p = path_util.to_local_abspath(value)
                    tmp_black_list.add(p)

        conf._ROOT = path_util.to_local_abspath(conf._ROOT)
        if not isinstance(conf.BIND_PORT, int) and not conf.BIND_PORT.isdigit():
            raise OptionError('Port must be digit: %s' % conf.BIND_PORT)
        if not os.path.exists(conf.ROOT) or not os.path.isdir(conf.ROOT):
            raise OptionError('Invalid root path: %s' % conf.ROOT)
        if not network_util.is_ip_v4(conf.BIND_IP):
            raise OptionError('Invalid ip_v4: %s' % conf.BIND_IP)
        try:
            os.chdir(conf._ROOT)
            conf.ROOT = os.getcwd()
        except OSError:
            raise OptionError('Permission deny for root path: %s' % conf._ROOT)

        conf.WHITE_LIST.clear()
        conf.BLACK_LIST.clear()
        tmp_white_list2 = set()  # store relative path for conf.ROOT
        tmp_black_list2 = set()  # store relative path for conf.ROOT
        if len(tmp_white_list) > 0:  # make sure to open white mode when '-w' is used
            conf.WHITE_LIST.add('')
        for i in tmp_white_list:
            p = path_util.to_local_path(i)
            if p.startswith('..'):
                logger.warn('Un support parent path: %s' % p)
            else:
                tmp_white_list2.add(p)
        for i in tmp_black_list:
            p = path_util.to_local_path(i)
            if p.startswith('..'):
                logger.warn('Un support parent path: %s' % p)
            else:
                tmp_black_list2.add(p)
        for w in tmp_white_list2:
            [conf.WHITE_LIST.add(i) for i in path_util.ls_reg(w)]
        for b in tmp_black_list2:
            [conf.BLACK_LIST.add(i) for i in path_util.ls_reg(b)]
        # to make sure the prior of black is high than white's.
        [conf.WHITE_LIST.remove(b) for b in conf.BLACK_LIST if b in conf.WHITE_LIST]
        for w in conf.WHITE_LIST:  # init white_list_parents
            [conf.WHITE_LIST_PARENTS.add(i) for i in path_util.parents_path(w)]
        if len(conf.WHITE_LIST) > 1 and '' in conf.WHITE_LIST:  # make sure to open white mode when '-w' is used
            conf.WHITE_LIST.remove('')


def _quit():
    print('Bye')
    sys.exit(0)


if __name__ == '__main__':
    run_fserver()
