from django import template


register = template.Library()


@register.filter
def get_at_index(obj, index):
    return obj[index]


@register.filter
def order_by(obj, args):
    args = args.split(',')
    return obj.order_by(*args)

