from django import template


register = template.Library()


@register.filter
def thai_be_date(value):
    if not value:
        return '-'
    return f'{value.day}/{value.month}/{value.year + 543}'


@register.filter
def split_parties(value):
    if not value:
        return []
    return [part.strip() for part in value.split(',') if part.strip()]
