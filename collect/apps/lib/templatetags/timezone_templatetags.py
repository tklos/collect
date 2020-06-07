from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def get_user_timezone(user):
    return settings.LOCAL_TIMEZONE

