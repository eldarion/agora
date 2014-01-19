from django.conf import settings  # noqa
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib

from appconf import AppConf


def load_path_attr(path):
    i = path.rfind(".")
    module, attr = path[:i], path[i + 1:]
    try:
        mod = importlib.import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured("Error importing {0}: '{1}'".format(module, e))
    try:
        attr = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured("Module '{0}' does not define a '{1}'".format(module, attr))
    return attr


class AgoraAppConf(AppConf):

    PARSER = "agora.callbacks.default_text"
    EDIT_TIMEOUT = dict(minutes=3)

    def configure_parser(self, value):
        return load_path_attr(value)
