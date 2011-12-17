from django.conf import settings


PARSER = getattr(settings, "AGORA_PARSER", ["agora.utils.default_text", {}])
EDIT_TIMEOUT = getattr(settings, "AGORA_EDIT_TIMEOUT", dict(minutes=3))