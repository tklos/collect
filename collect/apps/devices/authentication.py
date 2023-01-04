"""API key authentication.

API key can be specified in:
    API-KEY HTTP header or
    api-key data parameter
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Device
from . import const


class ApiKeyAuthentication(BaseAuthentication):

    def authenticate(self, request):
        api_key = request.META.get('HTTP_API_KEY')
        if api_key is None:
            api_key = request.data.get('api-key')
            if api_key is None:
                raise AuthenticationFailed('Missing API key')

        if len(api_key) != const.DEVICE_API_KEY_LEN:
            raise AuthenticationFailed('Incorrect API key')

        token = api_key[:const.DEVICE_TOKEN_LEN]
        for d in Device.objects.filter(token=token):
            if d.is_matching_api_key(api_key):
                return d, None

        raise AuthenticationFailed('Incorrect API key')

