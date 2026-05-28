from django import template
from django.utils import timezone


register = template.Library()


def _local_value(value):
    if hasattr(value, 'hour') and timezone.is_aware(value):
        return timezone.localtime(value)
    return value


@register.filter
def thai_be_date(value):
    if not value:
        return '-'
    value = _local_value(value)
    return f'{value.day:02d}/{value.month:02d}/{value.year + 543}'


@register.filter
def thai_be_datetime(value):
    if not value:
        return '-'
    value = _local_value(value)
    return f'{value.day:02d}/{value.month:02d}/{value.year + 543} {value:%H:%M}'


@register.filter
def thai_be_datetime_seconds(value):
    if not value:
        return '-'
    value = _local_value(value)
    return f'{value.day:02d}/{value.month:02d}/{value.year + 543} {value:%H:%M:%S}'


@register.filter
def split_parties(value):
    if not value:
        return []
    return [part.strip() for part in value.split(',') if part.strip()]
