from django.conf.urls import patterns, url


urlpatterns = patterns("agora.views",
    url(r"^$", "forums", name="agora_forums"),
    url(r"^category/(\d+)/$", "forum_category", name="agora_category"),
    url(r"^forum/(\d+)/$", "forum", name="agora_forum"),
    url(r"^thread/(\d+)/$", "forum_thread", name="agora_thread"),
    url(r"^new_post/(\d+)/$", "post_create", name="agora_post_create"),
    url(r"^reply/(\d+)/$", "reply_create", name="agora_reply_create"),
    url(r"^post_edit/(thread|reply)/(\d+)/$", "post_edit", name="agora_post_edit"),
    url(r"^subscribe/(\d+)/$", "subscribe", name="agora_subscribe"),
    url(r"^unsubscribe/(\d+)/$", "unsubscribe", name="agora_unsubscribe"),
    url(r"^thread_updates/$", "thread_updates", name="agora_thread_updates"),
)
