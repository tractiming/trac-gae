from functools import wraps

from django.conf import settings
try:
    from google.appengine.api import taskqueue
except ImportError:
    taskqueue = None


_webhook_url = '/notifications/notify/'


def do_maybe_notification(func):
    """Wrap a method that returns a serialized list of splits and send updates
    to the notification task queue.
    """
    @wraps(func)
    def send_notification(*args, **kwargs):
        resp = func(*args, **kwargs)
        if settings.ENABLE_NOTIFICATIONS and taskqueue is not None:
            data = resp.data if isinstance(resp.data, list) else [resp.data]
            for split in data:
                taskqueue.add(url=_webhook_url, params={'split': split['id']})
        return resp
    return send_notification
