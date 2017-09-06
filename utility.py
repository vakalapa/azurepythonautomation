
#!/bin/env python

"""
Version: 0.1
Author: vakalapa@cisco.com

Azure Automation Script


"""

import sys, os
import termios
from distutils.util import strtobool


try:
    raw_input
except: # Python3
    raw_input = input

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def msg_color(msg, style):
    message = ''
    if style.lower() == 'header':
        message = bcolors.HEADER
    elif style.lower() == 'blue':
        message = bcolors.OKBLUE
    elif style.lower() == 'green':
        message = bcolors.OKGREEN
    elif style.lower() == 'underline':
        message = bcolors.UNDERLINE
    elif style.lower() == 'warning':
        message = bcolors.WARNING
    elif style.lower() == 'bold':
        message = bcolors.BOLD
    elif style.lower() == 'fail':
        message = bcolors.FAIL

    return message + msg + bcolors.ENDC

def confirm(msg, default = False):
    if not os.isatty(1):
        return default
    termios.tcflush(sys.stdin, termios.TCIFLUSH)
    try:
        return strtobool(raw_input(msg))
    except KeyboardInterrupt:
        print('')
        sys.exit(-1)
    except Exception:
        return default

def read_line(msg = '', default = ''):
    if not os.isatty(1):
        return default
    termios.tcflush(sys.stdin, termios.TCIFLUSH)
    try:
        return raw_input(msg).strip()
    except KeyboardInterrupt:
        print('')
        sys.exit(-1)



#print confirm('HELLO \nIgnore and continue? (y/N):')