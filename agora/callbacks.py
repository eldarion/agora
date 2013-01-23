from django.utils.html import urlize, linebreaks, escape
from django.utils.safestring import mark_safe


def default_text(text):
    return mark_safe(linebreaks(urlize(escape(text))))
