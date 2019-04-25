import json
import logging
import logging.config

import codegra_fs.cgfs


class JsonFormatter(logging.Formatter):
    ATTR_TO_JSON = set(
        [
            'created',
            'filename',
            'funcName',
            'levelname',
            'lineno',
            'module',
            'msecs',
            'name',
            'pathname',
            'process',
            'processName',
            'relativeCreated',
            'thread',
            'threadName',
        ]
    )

    def format(self, record):
        obj = {attr: getattr(record, attr) for attr in self.ATTR_TO_JSON}

        message = record.msg % record.args
        fuse_context = codegra_fs.cgfs.get_fuse_context()
        if fuse_context:
            message = '{}: {}'.format(fuse_context, message)

        obj.update(
            {
                'message': message,
                'notify': getattr(record, 'notify', False),
            }
        )

        if codegra_fs.cgfs.gui_mode.enabled:
            return json.dumps(obj, separators=(',', ':'))
        else:
            return logging.BASIC_FORMAT % obj


logging.config.dictConfig(
    {
        'version': 1,
        'formatters': {
            'json': {
                '()': JsonFormatter,
            },
        },
        'handlers':
            {
                'json': {
                    '()': logging.StreamHandler,
                    'formatter': 'json',
                },
            },
        'root': {
            'handlers': ['json'],
        },
    }
)
