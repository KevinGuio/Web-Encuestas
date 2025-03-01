from django import template

register = template.Library()

@register.filter(name='divide')
def divide(value, arg):
    try:
        return (float(value) / float(arg)) * 100
    except (ZeroDivisionError, ValueError):
        return 0