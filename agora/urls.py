from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r'^$', 'agora.views.forums', name="agora_forums"),
    url(r'^category/(\d+)/$', 'agora.views.forum_category', name="agora_category"),
    url(r'^forum/(\d+)/$', 'agora.views.forum', name="agora_forum"),
    url(r'^thread/(\d+)/$', 'agora.views.forum_thread', name="agora_thread"),
    
    url(r'^new_post/(\d+)/$', 'agora.views.new_post', name="agora_new_post"),
    url(r'^reply/(\d+)/$', 'agora.views.reply', name="agora_reply"),
    url(r'^reply_edit/(\d+)/$', 'agora.views.reply_edit', name="agora_reply_edit"),
)