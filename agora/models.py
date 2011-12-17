import datetime
import functools

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_delete
from django.utils import simplejson as json
from django.utils.html import conditional_escape

from django.contrib.auth.models import User

from agora.managers import ForumThreadManager
from agora.settings import PARSER, EDIT_TIMEOUT
from agora.utils import load_path_attr


# this is the glue to the activity events framework, provided as a no-op here
def issue_update(kind, **kwargs):
    pass


class ForumCategory(models.Model):
    
    title = models.CharField(max_length=100)
    
    parent = models.ForeignKey("self", null=True, blank=True, related_name="subcategories")
    
    # @@@ total descendant forum count?
    # @@@ make group-aware
    
    class Meta:
        verbose_name_plural = "forum categories"
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("agora_category", args=(self.pk,))
    
    @property
    def forums(self):
        return self.forum_set.order_by("title")


class Forum(models.Model):
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    
    # must only have one of these (or neither):
    parent = models.ForeignKey("self",
        null = True,
        blank = True,
        related_name = "subforums"
    )
    category = models.ForeignKey(ForumCategory,
        null = True,
        blank = True,
        on_delete = models.SET_NULL
    )
    
    # @@@ make group-aware
    
    last_modified = models.DateTimeField(
        default = datetime.datetime.now,
        editable = False
    )
    last_thread = models.ForeignKey(
        "ForumThread",
        null = True,
        editable = False,
        on_delete = models.SET_NULL,
        related_name = "+"
    )
    
    view_count = models.IntegerField(default=0, editable=False)
    post_count = models.IntegerField(default=0, editable=False)
    
    @property
    def thread_count(self):
        return self.threads.count()
    
    # this is what gets run normally
    def inc_views(self):
        self.view_count += 1
        self.save()
    
    # this can be used occasionally to get things back in sync
    def update_view_count(self):
        view_count = 0
        for thread in self.threads.all():
            view_count += thread.view_count
        self.view_count = view_count
        self.save()
    
    def update_post_count(self):
        post_count = 0
        for forum in self.subforums.all():
            forum.update_post_count()
            post_count += forum.post_count
        for thread in self.threads.all():
            thread.update_reply_count()
            post_count += thread.reply_count + 1 # add one for the thread itself
        self.post_count = post_count
        self.save()
    
    def new_post(self, post):
        self.post_count += 1 # if this gets out of sync run update_post_count
        self.last_modified = post.created
        self.last_thread = post.thread
        self.save()
        if self.parent:
            self.parent.new_post(post)
    
    def __unicode__(self):
        return self.title
    
    def update_last_thread(self):
        try:
            self.last_thread = self.threads.order_by("-created")[0]
        except IndexError:
            self.last_thread = None
        self.save()
    
    @property
    def last_post(self):
        if self.last_thread_id is None:
            return None
        else:
            return self.last_thread.last_post
    
    def export(self, out=None):
        if out is None:
            out = "forum-export-%d.json" % self.id
        data = {
            "self": {
                "id": self.id,
                "title": self.title,
                "description": self.description,
                "parent": self.parent_id,
                "category": self.category_id,
                "last_modified": self.last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                "last_thread": self.last_thread_id,
                "view_count": self.view_count,
                "post_count": self.post_count
            },
            "threads": [
                {
                    "id": t.id,
                    "author": t.author_id,
                    "content": t.content,
                    "created": t.created.strftime("%Y-%m-%d %H:%M:%S"),
                    "forum": t.forum_id,
                    "title": t.title,
                    "last_modified": t.last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_reply": t.last_reply_id,
                    "view_count": t.view_count,
                    "reply_count": t.reply_count,
                    "subscriber_count": t.subscriber_count,
                    "replies": [
                        {
                            "id": r.id,
                            "author": r.author_id,
                            "content": r.content,
                            "created": r.created.strftime("%Y-%m-%d %H:%M:%S"),
                            "thread": r.thread_id,
                        }
                        for r in t.replies.all()
                    ],
                    "subscriptions": [
                        {
                            "id": s.id,
                            "thread": s.thread_id,
                            "user": s.user_id,
                            "kind": s.kind,
                        }
                        for s in t.subscriptions.all()
                    ]
                }
                for t in self.threads.all()
            ]
        }
        json.dump(data, open(out, "wb"))
    
    @classmethod
    def restore(cls, in_):
        data = json.load(open(in_))
        forum = Forum(**dict(
            id = data["self"]["id"],
            title = data["self"]["title"],
            description = data["self"]["description"],
            parent_id = data["self"]["parent"],
            category_id = data["self"]["category"],
            last_modified = data["self"]["last_modified"],
            view_count = data["self"]["view_count"],
            post_count = data["self"]["post_count"]
        ))
        forum._importing = True
        forum.save()
        for thread_data in data["threads"]:
            thread = ForumThread(**dict(
                id = thread_data["id"],
                author_id = thread_data["author"],
                content = thread_data["content"],
                created = thread_data["created"],
                forum_id = thread_data["forum"],
                title = thread_data["title"],
                last_modified = thread_data["last_modified"],
                view_count = thread_data["view_count"],
                reply_count = thread_data["reply_count"],
                subscriber_count = thread_data["subscriber_count"]
            ))
            thread._importing = True
            thread.save()
            for reply_data in thread_data["replies"]:
                reply = ForumReply(**dict(
                    id = reply_data["id"],
                    author_id = reply_data["author"],
                    content = reply_data["content"],
                    created = reply_data["created"],
                    thread_id = reply_data["thread"],
                ))
                reply._importing = True
                reply.save()
            for subscriber_data in thread_data["subscriptions"]:
                ThreadSubscription(**dict(
                    id = subscriber_data["id"],
                    user_id = subscriber_data["user"],
                    thread_id = subscriber_data["thread"],
                    kind = subscriber_data["kind"],
                )).save()
            thread.last_reply_id = thread_data["last_reply"]
            thread.save()
        forum.last_thread_id = data["self"]["last_thread"]
        forum.save()


class ForumPost(models.Model):
    
    author = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_related")
    content = models.TextField()
    content_html = models.TextField()
    created = models.DateTimeField(default=datetime.datetime.now, editable=False)
    
    class Meta:
        abstract = True
    
    def save(self, **kwargs):
        render_func = functools.partial(load_path_attr(PARSER[0], **PARSER[1]))
        self.content_html = conditional_escape(render_func(self.content))
        super(ForumPost, self).save(**kwargs)
    
    # allow editing for short period after posting
    def editable(self, user):
        if user == self.author:
            if datetime.datetime.now() < self.created + datetime.timedelta(**EDIT_TIMEOUT):
                return True
        return False


class ForumThread(ForumPost):
    
    # used for code that needs to know the kind of post this object is.
    kind = "thread"
    
    forum = models.ForeignKey(Forum, related_name="threads")
    
    title = models.CharField(max_length=100)
    
    last_modified = models.DateTimeField(
        default = datetime.datetime.now,
        editable = False
    )
    last_reply = models.ForeignKey(
        "ForumReply",
        null = True,
        editable = False,
        on_delete = models.SET_NULL
    )
    
    sticky = models.IntegerField(default=0)
    # @@@ closed threads
    
    view_count = models.IntegerField(default=0, editable=False)
    reply_count = models.IntegerField(default=0, editable=False)
    subscriber_count = models.IntegerField(default=0, editable=False)
    
    objects = ForumThreadManager()
    
    def inc_views(self):
        self.view_count += 1
        self.save()
        self.forum.inc_views()
    
    def update_reply_count(self):
        self.reply_count = self.replies.all().count()
        self.save()
    
    def update_subscriber_count(self):
        self.subscriber_count = self.subscriptions.filter(kind="email").count()
        self.save()
    
    def new_reply(self, reply):
        self.reply_count += 1
        self.last_modified = reply.created
        self.last_reply = reply
        self.save()
        self.forum.new_post(reply)
    
    def subscribe(self, user, kind):
        """
        Subscribes the given user to this thread (handling duplicates)
        """
        ThreadSubscription.objects.get_or_create(thread=self, user=user, kind=kind)
    
    def unsubscribe(self, user, kind):
        try:
            subscription = ThreadSubscription.objects.get(thread=self, user=user, kind=kind)
        except ThreadSubscription.DoesNotExist:
            return
        else:
            subscription.delete()
    
    def subscribed(self, user, kind):
        if user.is_anonymous():
            return False
        try:
            ThreadSubscription.objects.get(thread=self, user=user, kind=kind)
        except ThreadSubscription.DoesNotExist:
            return False
        else:
            return True
    
    def __unicode__(self):
        return self.title
    
    def update_last_reply(self):
        try:
            self.last_reply = self.replies.order_by("-created")[0]
        except IndexError:
            self.last_reply = None
        self.save()
    
    @property
    def last_post(self):
        if self.last_reply_id is None:
            return self
        else:
            return self.last_reply
    
    @property
    def thread(self):
        return self


class ForumReply(ForumPost):
    
    # used for code that needs to know the kind of post this object is.
    kind = "reply"
    
    thread = models.ForeignKey(ForumThread, related_name="replies")
    
    class Meta:
        verbose_name = "forum reply"
        verbose_name_plural = "forum replies"


class UserPostCount(models.Model):
    
    user = models.ForeignKey(User, related_name="post_count")
    count = models.IntegerField(default=0)
    
    @classmethod
    def calculate(cls):
        for user in User.objects.all():
            thread_count = ForumThread.objects.filter(author=user).count()
            reply_count = ForumReply.objects.filter(author=user).count()
            count = thread_count + reply_count
            upc, created = cls._default_manager.get_or_create(
                user = user,
                defaults = dict(
                    count = count
                )
            )
            if not created:
                upc.count = count
                upc.save()


class ThreadSubscription(models.Model):
    
    thread = models.ForeignKey(ForumThread, related_name="subscriptions")
    user = models.ForeignKey(User, related_name="forum_subscriptions")
    kind = models.CharField(max_length=15)
    
    class Meta:
        unique_together = [("thread", "user", "kind")]
    
    @classmethod
    def setup_onsite(cls):
        for user in User.objects.all():
            threads = ForumThread.objects.filter(author=user).values_list("pk", flat=True)
            threads_by_replies = ForumReply.objects.filter(author=user).distinct().values_list("thread", flat=True)
            for thread in set(threads).union(threads_by_replies):
                ForumThread.objects.get(pk=thread).subscribe(user, "onsite")


def signal(signals, sender=None):
    def _wrapped(func):
        if not hasattr(signals, "__iter__"):
            _s = [signals]
        else:
            _s = signals
        for s in _s:
            s.connect(func, sender=sender)
        return func
    return _wrapped


@signal(post_save, ForumThread)
def forum_thread_save(sender, instance=None, created=False, **kwargs):
    if instance and created:
        forum = instance.forum
        forum.new_post(instance)
        
        # @@@ this next part could be manager method
        post_count, created = UserPostCount.objects.get_or_create(user=instance.author)
        post_count.count += 1
        post_count.save()


@signal(post_save, ForumReply)
def forum_reply_save(sender, instance=None, created=False, **kwargs):
    if instance and created:
        thread = instance.thread
        thread.new_reply(instance)
        
        # @@@ this next part could be manager method
        post_count, created = UserPostCount.objects.get_or_create(user=instance.author)
        post_count.count += 1
        post_count.save()


@signal(pre_delete, ForumThread)
def forum_thread_delete(sender, **kwargs):
    thread = kwargs["instance"]
    if thread.id == thread.forum.last_thread_id:
        thread.forum.update_last_thread()
    thread.forum.update_view_count()
    thread.forum.update_post_count()


@signal(pre_delete, ForumReply)
def forum_reply_delete(sender, **kwargs):
    reply = kwargs["instance"]
    if reply.id == reply.thread.last_reply_id:
        reply.thread.update_last_reply()
    reply.thread.forum.update_post_count()


@signal([post_save, post_delete], ThreadSubscription)
def forum_subscription_update(sender, instance=None, created=False, **kwargs):
    if instance and created:
        thread = instance.thread
        thread.update_subscriber_count()
