from django.contrib import admin

from agora import models


class ForumThreadAdmin(admin.ModelAdmin):

    class ForumThreadReplyInline(admin.StackedInline):
        model = models.ForumReply
        extra = 1

    list_display = [
        "id",
        "title",
        "created",
        "author",
        "view_count",
        "reply_count",
        "subscriber_count",
    ]
    inlines = [
        ForumThreadReplyInline
    ]


admin.site.register(
    models.ForumCategory,
    list_display=[
        "title",
        "parent"
    ]
)
admin.site.register(
    models.Forum,
    list_display=[
        "id",
        "title",
        "parent",
        "category",
        "view_count",
        "post_count"
    ]
)
admin.site.register(models.ForumThread, ForumThreadAdmin)
