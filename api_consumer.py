#!/usr/bin/env python3
import os
import sys
import json
import socket

if __name__ == '__main__':
    path = '/'
    for p in os.path.abspath(sys.argv[2]).split('/'):
        if not p:
            continue
        path = os.path.join(path, p)
        if os.path.isfile(os.path.join(path, '.api.socket')):
            break
    else:
        print('Not found', file=sys.stderr)
        sys.exit(1)

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(open(os.path.join(path, '.api.socket'), 'r').read())

    if sys.argv[1] == 'add-comment':
        line = int(sys.argv[3])
        message = sys.argv[4]
        s.send(
            bytes(
                json.dumps(
                    {
                        'op': 'add_feedback',
                        'file': os.path.abspath(sys.argv[2]),
                        'line': line,
                        'message': message
                    }
                ).encode('utf8')
            )
        )
        if json.loads(s.recv(1024))['ok']:
            s.close()
            sys.exit(0)
        else:
            s.close()
            sys.exit(1)
    elif sys.argv[1] == 'get-comment':
        s.send(
            bytes(
                json.dumps(
                    {
                        'op': 'get_feedback',
                        'file': os.path.abspath(sys.argv[2]),
                    }
                ).encode('utf8')
            )
        )
        message = b''

        while True:
            m = s.recv(1024)
            message += m
            if len(m) < 1024:
                break

        out = json.loads(message)
        if out['ok']:
            res = []
            for key, val in out['data'].items():
                res.append((key, val['msg']))
            res.sort(key=lambda i: i[0])
            print(
                '\n'.join(
                    '{}:{}:{}:{}'.format(
                        os.path.abspath(sys.argv[2]), number, 0, msg
                    ) for number, msg in res
                )
            )
            s.close()
            sys.exit(0)
        else:
            s.close()
            sys.exit(1)
