DAY_ABBREVIATIONS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')


def english_day_abbreviation(value):
    return DAY_ABBREVIATIONS[value.weekday()] if value else ''
