from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from agora.models import ForumThread, ForumReply, ThreadSubscription, UserPostCount


@receiver(post_save, sender=ForumThread)
def forum_thread_save(sender, instance=None, created=False, **kwargs):
    if instance and created:
        forum = instance.forum
        forum.new_post(instance)

        # @@@ this next part could be manager method
        post_count, created = UserPostCount.objects.get_or_create(user=instance.author)
        post_count.count += 1
        post_count.save()


@receiver(post_save, sender=ForumReply)
def forum_reply_save(sender, instance=None, created=False, **kwargs):
    if instance and created:
        thread = instance.thread
        thread.new_reply(instance)

        # @@@ this next part could be manager method
        post_count, created = UserPostCount.objects.get_or_create(user=instance.author)
        post_count.count += 1
        post_count.save()


@receiver(pre_delete, sender=ForumThread)
def forum_thread_delete(sender, **kwargs):
    thread = kwargs["instance"]
    if thread.id == thread.forum.last_thread_id:
        thread.forum.update_last_thread()
    thread.forum.update_view_count()
    thread.forum.update_post_count()


@receiver(pre_delete, sender=ForumReply)
def forum_reply_delete(sender, **kwargs):
    reply = kwargs["instance"]
    if reply.id == reply.thread.last_reply_id:
        reply.thread.update_last_reply()
    reply.thread.forum.update_post_count()


@receiver(post_save, sender=ThreadSubscription)
def forum_subscription_update(sender, instance=None, created=False, **kwargs):
    if instance and created:
        thread = instance.thread
        thread.update_subscriber_count()
