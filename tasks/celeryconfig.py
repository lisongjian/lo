from kombu import Exchange, Queue

# CELERY_DEFAULT_EXCHANGE = 'default'
# CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'
# 
# CELERY_DEFAULT_QUEUE = 'default'

CELERY_QUEUES = (
    Queue('default', routing_key='default_key'),
    Queue('sms', routing_key='sms'),
    Queue('jpush', routing_key='jpush'),
    Queue('wallad', routing_key='wallad'),
    Queue('ipfind', routing_key='ipfind'),
)


# CELERY_DEFAULT_EXCHANGE = 'ex'
# CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
# CELERY_DEFAULT_ROUTING_KEY = 'task.default'


CELERY_ROUTES = { 
                 'sms': { 'queue': 'sms' }, 
                 'jpush': { 'queue': 'jpush' },  
                 'wallad': { 'queue': 'wallad' }, 
                 'ipfind': { 'queue': 'ipfind' }, 
                 }

# from kombu import Queue
# CELERY_DEFAULT_EXCHANGE = 'exchange_name'
# CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
# CELERY_DEFAULT_QUEUE = 'default'
# CELERY_DEFAULT_ROUTING_KEY = 'task.default'
# CELERY_QUEUES = (
#      Queue('default', routing_key='task.#'),
#      Queue('high_priority', routing_key='high_priority.#'),
# )
# 
# CELERY_ROUTES = {
#      'high_priority_task': {
#      'queue': 'high_priority',
#      'routing_key': 'high_priority.#',
#      },
# }