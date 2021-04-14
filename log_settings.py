# -*- coding: utf-8 -*-
# use  Python ver 3.8.5

log_config = {
    'version': 1,
    'formatters': {
        'long_formatter': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
        'short_formatter': {
            'format': '%(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'stderr_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'short_formatter',

        },
        'file_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'long_formatter',
            'filename': 'bot.log',
            'encoding': 'UTF-8',

        },
        'peewee_file_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'long_formatter',
            'filename': 'peewee.log',
            'encoding': 'UTF-8',

        },
    },
    'loggers': {
        'bot': {
            'handlers': ['stderr_handler', 'file_handler'],
            'level': 'DEBUG',
        },
        'peewee': {
            'handlers': ['stderr_handler', 'peewee_file_handler'],
            'level': 'DEBUG',
        },

    },
}
