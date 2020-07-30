from django.conf import settings
from django.utils import timezone


class TimezoneMiddleware:
    _exclude_paths = [
        '/api/measurements/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    @classmethod
    def process_view(cls, request, view_func, *args, **kwargs):
        for ep in cls._exclude_paths:
            if request.path.startswith(ep):
                return

        timezone.activate(settings.LOCAL_TIMEZONE)

