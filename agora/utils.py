from django.core.exceptions import ImproperlyConfigured
from django.utils.html import urlize, linebreaks, escape
from django.utils.safestring import mark_safe
try:
    from django.utils.importlib import import_module
except ImportError:
    from importlib import import_module


def load_path_attr(path):
    i = path.rfind(".")
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured("Error importing %s: '%s'" % (module, e))
    try:
        attr = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured("Module '%s' does not define a '%s'" % (module, attr))
    return attr


def default_text(text):
    return mark_safe(linebreaks(urlize(escape(text))))
