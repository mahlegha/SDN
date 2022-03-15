#!/usr/bin/env python

import sys

from ryu.cmd import manager

# root@ubuntu:~# ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology sample.py --observe-links --wsapi-port 8080 --ofp-tcp-listen-port 6653

def main():
    sys.argv.append('--ofp-tcp-listen-port')
    sys.argv.append('6653')

    # sys.argv.append('cnn_path_finder_9.py')
    sys.argv.append('shortest_path_9.py')

    # sys.argv.append('--verbose')
    # sys.argv.append('--enable-debugger')

    sys.argv.append('--observe-links')
    # sys.argv.append('--observe-hosts')
    manager.main()


if __name__ == '__main__':
    main()