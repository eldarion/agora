from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r'^$', 'agora.views.forums', name="agora_forums"),
    url(r'^category/(\d+)/$', 'agora.views.forum_category', name="agora_category"),
    url(r'^forum/(\d+)/$', 'agora.views.forum', name="agora_forum"),
    url(r'^thread/(\d+)/$', 'agora.views.forum_thread', name="agora_thread"),
    
    url(r'^new_forum_post/(\d+)/$', 'agora.views.new_forum_post', name="agora_new_forum_post"),
    url(r'^forum_reply/(\d+)/$', 'agora.views.forum_reply', name="agora_forum_reply"),
    url(r'^forum_reply_edit/(\d+)/$', 'agora.views.forum_reply_edit', name="agora_forum_reply_edit"),
)