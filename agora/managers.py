from django.db import models


class ForumThreadPostQuerySet(models.query.QuerySet):
    
    def iterator(self):
        queryset = super(ForumThreadPostQuerySet, self).iterator()
        reverse = self._posts_manager_params["reverse"]
        thread = self._posts_manager_params["thread"]
        first = True
        if not reverse:
            yield thread
        for obj in queryset:
            yield obj
        if reverse:
            yield thread
    
    def _clone(self, *args, **kwargs):
        kwargs["_posts_manager_params"] = self._posts_manager_params
        return super(ForumThreadPostQuerySet, self)._clone(*args, **kwargs)


class ForumThreadManager(models.Manager):
    
    def posts(self, thread, reverse=False):
        from agora.models import ForumReply
        queryset = ForumThreadPostQuerySet(ForumReply, using=self._db)
        queryset._posts_manager_params = {
            "reverse": reverse,
            "thread": thread,
        }
        queryset = queryset.filter(thread=thread)
        queryset = queryset.select_related("thread")
        if reverse:
            queryset = queryset.order_by("%screated" % (reverse and "-" or ""))
        return queryset
