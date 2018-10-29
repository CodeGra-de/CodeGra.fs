#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys
import json
import socket


def print_usage() -> None:
    print(
        (
            'Usage:\n'
            '{0} set-comment FILE LINE_NUMBER MESSAGE\n'
            'OR\n'
            '{0} delete-comment FILE LINE_NUMBER\n'
            'OR\n'
            '{0} get-comment FILE\n'
        ).format(sys.argv[0]),
        file=sys.stderr,
        end='\n',
    )


def recv(s: socket.socket) -> str:
    message = b''

    while True:
        m = s.recv(1024)
        message += m
        if len(m) < 1024:
            break

    return message.decode()


def is_file(s: socket.socket, file: str) -> int:
    s.send(
        bytes(
            json.dumps({
                'op': 'is_file',
                'file': os.path.abspath(file),
            }).encode('utf8')
        )
    )
    if json.loads(recv(s))['ok']:
        return 0
    else:
        return 2


def get_comments(s: socket.socket, file: str) -> int:
    s.send(
        bytes(
            json.
            dumps({
                'op': 'get_feedback',
                'file': os.path.abspath(file),
            }).encode('utf8')
        )
    )
    message = recv(s)

    out = json.loads(message)
    if out['ok']:
        res = []
        for key, val in out['data'].items():
            res.append({'col': 0, 'line': int(key) + 1, 'content': val['msg']})

        res.sort(key=lambda i: i['line'])
        print(json.dumps(res))
        return 0
    else:
        return 2


def delete_comment(s: socket.socket, file: str, line: int) -> int:
    s.send(
        bytes(
            json.dumps(
                {
                    'op': 'delete_feedback',
                    'file': os.path.abspath(file),
                    'line': line - 1,
                }
            ).encode('utf8')
        )
    )
    if json.loads(recv(s))['ok']:
        return 0
    else:
        return 2


def set_comment(s: socket.socket, file: str, line: int, message: str) -> int:
    s.send(
        bytes(
            json.dumps(
                {
                    'op': 'set_feedback',
                    'file': os.path.abspath(sys.argv[2]),
                    'line': line - 1,
                    'message': message
                }
            ).encode('utf8')
        )
    )
    if json.loads(recv(s))['ok']:
        return 0
    else:
        return 2


def main() -> None:
    if sys.platform.startswith('win32'):
        path = ''
    else:
        path = '/'

    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    for p in os.path.abspath(sys.argv[2]).split(os.sep):
        if path and not p:
            continue
        path = os.path.join(path, p)
        if os.path.isfile(os.path.join(path, '.api.socket')):
            break
    else:
        print('Socket not found', file=sys.stderr)
        sys.exit(3)

    with open(os.path.join(path, '.api.socket'), 'r') as f:
        socketfile_content = f.read().strip()

    if sys.platform.startswith('win32'):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', int(socketfile_content)))
    else:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(socketfile_content)

    try:
        if sys.argv[1] == 'set-comment':
            if len(sys.argv) != 5:
                print_usage()
                sys.exit(1)

            try:
                line = int(sys.argv[3])
            except ValueError:
                print_usage()
                sys.exit(3)

            message = sys.argv[4]

            sys.exit(set_comment(s, sys.argv[2], line, message))

        elif sys.argv[1] == 'delete-comment':
            if len(sys.argv) != 4:
                print_usage()
                sys.exit(1)

            try:
                line = int(sys.argv[3])
            except ValueError:
                print_usage()
                sys.exit(3)

            sys.exit(delete_comment(s, sys.argv[2], line))

        elif sys.argv[1] == 'is-file':
            if len(sys.argv) != 3:
                print_usage()
                sys.exit(1)

            sys.exit(is_file(s, sys.argv[2]))

        elif sys.argv[1] == 'get-comment':
            if len(sys.argv) != 3:
                print_usage()
                sys.exit(1)

            sys.exit(get_comments(s, sys.argv[2]))
        else:
            print_usage()
            sys.exit(1)
    finally:
        s.close()


if __name__ == '__main__':
    main()
