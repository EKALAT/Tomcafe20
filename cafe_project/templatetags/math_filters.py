from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Nhân hai số."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Chia hai số."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def add(value, arg):
    """Cộng hai số."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """Trừ hai số."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def floatformat(value, arg):
    """Format số thập phân."""
    try:
        return round(float(value), int(arg))
    except (ValueError, TypeError):
        return value 