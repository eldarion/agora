from django.db import models


class ForumThreadPostQuerySet(models.query.QuerySet):
    
    def iterator(self):
        queryset = super(ForumThreadPostQuerySet, self).iterator()
        first = True
        for obj in queryset:
            if first:
                # we should be able to gurantee only a single thread for all
                # objects in queryset
                thread = obj.thread
                first = False
                if not self.reversed:
                    yield thread
            yield obj
        if self.reversed:
            yield thread
    
    def _clone(self, *args, **kwargs):
        kwargs["reversed"] = self.reversed
        return super(ForumThreadPostQuerySet, self)._clone(*args, **kwargs)


class ForumThreadManager(models.Manager):
    
    def posts(self, thread, reverse=False):
        from agora.models import ForumReply
        queryset = ForumThreadPostQuerySet(ForumReply, using=self._db)
        queryset.reversed = reverse
        queryset = queryset.filter(thread=thread)
        queryset = queryset.select_related("thread")
        if reverse:
            queryset = queryset.order_by("%screated" % (reverse and "-" or ""))
        return queryset
