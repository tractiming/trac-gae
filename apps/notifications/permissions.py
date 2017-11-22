from rest_framework import permissions


class IsFromTaskQueuePermission(permissions.BasePermission):
    """Permission for determining if request is from Google Task Queue."""

    def has_permission(self, request, view):
        # Per "https://cloud.google.com/appengine/docs/python/taskqueue/"
        # "overview-push#task_request_headers", requests from the task queue
        # will contain certain headers that cannot be contained in a
        # normal request.
        return 'HTTP_X_APPENGINE_QUEUENAME' in request.META
