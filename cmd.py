# -*- coding: utf-8 -*-

import signal
import sys

import gevent

from app.command_line import run_fserver


def quit():
    print ('Bye')
    sys.exit(0)


if __name__ == '__main__':
    gevent.signal(signal.SIGINT, quit)
    run_fserver()
