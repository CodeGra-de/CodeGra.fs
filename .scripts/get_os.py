#!/usr/bin/env python
import sys
import platform


def main():
    system = platform.system()
    if system == 'Windows':
        print('win')
    elif system in ('Darwin', 'Linux'):
        print(system.lower())
    else:
        print('The system {} is not supported'.format(system), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
