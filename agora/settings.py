from django.conf import settings


PARSER = getattr(settings, "AGORA_PARSER", ["agora.utils.default_text", {}])