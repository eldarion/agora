from django import template
from django.core.urlresolvers import reverse

from agora.models import ThreadSubscription


register = template.Library()


class SubscriptionNode(template.Node):

    def __init__(self, user, varname, thread_list=None):
        self.user = template.Variable(user)
        if thread_list:
            self.thread_list = [template.Variable(t) for t in thread_list]
        self.varname = varname

    def render(self, context):
        user = self.user.resolve(context)
        threads = ThreadSubscription.objects.filter(user=user)
        if self.thread_list:
            threads = threads.filter(thread__in=self.thread_list)
        context[self.varname] = threads
        return ""


@register.tag
def subscriptions(parser, token):
    """
    {% subscriptions for user as varname %}
    """
    tag, _, user, _, varname = token.split_contents()
    return SubscriptionNode(user, varname)


@register.tag
def filter_subscriptions(parser, token):
    """
    {% filter_subscriptions user thread_list as subscribed_threads %}
    """
    tag, user, thread_list, _, varname = token.split_contents()
    return SubscriptionNode(user, varname, thread_list)


class SubscribeUrlNode(template.Node):

    def __init__(self, user, thread, varname, subscribe=True):
        self.user = template.Variable(user)
        self.thread = template.Variable(thread)
        self.varname = varname
        self.viewname = "agora_unsubscribe"
        if subscribe:
            self.viewname = "agora_subscribe"

    def render(self, context):
        user = self.user.resolve(context)
        thread = self.thread.resolve(context)
        context[self.varname] = reverse(self.viewname, kwargs={
            "user_id": user.id,
            "thread_id": thread.id
        })
        return ""


@register.tag
def subscribe_url(parser, token):
    """
    {% subscribe_url user_obj thread_obj as theurl %}
    """
    tag, user, _, thread, _, varname = token.split_contents()
    return SubscribeUrlNode(user, thread, varname)


@register.tag
def unsubscribe_url(parser, token):
    """
    {% unsubscribe_url user_obj thread_obj as theurl %}
    """
    tag, user, _, thread, _, varname = token.split_contents()
    return SubscribeUrlNode(user, thread, varname, subscribe=False)


@register.filter
def post_editable(post, user):
    return post.editable(user)
