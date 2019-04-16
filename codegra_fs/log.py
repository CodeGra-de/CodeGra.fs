import json
import logging
import logging.config

json_output = False

class JsonFormatter(logging.Formatter):
    ATTR_TO_JSON = set([
        'created',
        'filename',
        'funcName',
        'levelname',
        'lineno',
        'module',
        'msecs',
        'msg',
        'name',
        'pathname',
        'process',
        'processName',
        'relativeCreated',
        'thread',
        'threadName',
    ])

    def format(self, record):
        obj = {
            attr: getattr(record, attr)
            for attr in self.ATTR_TO_JSON
        }
        obj['msg'] = obj['msg'] % record.args

        if json_output or True:
            return json.dumps(obj, separators=(',', ':'))
        else:
            return logging.BASIC_FORMAT % obj

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'json': {
            '()': JsonFormatter,
        },
    },
    'handlers': {
        'json': {
            '()': logging.StreamHandler,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['json'],
    },
})
