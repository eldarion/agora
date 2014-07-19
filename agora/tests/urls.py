from django.conf.urls import patterns, include


urlpatterns = patterns(
    "",
    (r"^", include("agora.urls")),
)
