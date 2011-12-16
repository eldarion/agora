from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response

from django.contrib.auth.decorators import login_required

from agora.models import ForumCategory, Forum, UserPostCount
from agora.models import ForumThread, ForumReply, ThreadSubscription


def ajax(func):
    def _wrapped_view(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except:
            import sys
            print sys.exc_info()
            raise
    return _wrapped_view


def forums(request):
    
    categories = ForumCategory.objects.filter(parent__isnull=True)
    categories = categories.order_by("title")
    
    most_active_forums = Forum.objects.order_by("-post_count")[:5]
    most_viewed_forums = Forum.objects.order_by("-view_count")[:5]
    most_active_members = UserPostCount.objects.order_by("-count")[:5]
    
    latest_posts = ForumReply.objects.order_by("-created")[:10]
    latest_threads = ForumThread.objects.order_by("-last_modified")
    most_active_threads = ForumThread.objects.order_by("-reply_count")
    most_viewed_threads = ForumThread.objects.order_by("-view_count")
    
    return render_to_response("agora/forums.html", {
        "categories": categories,
        "most_active_forums": most_active_forums,
        "most_viewed_forums": most_viewed_forums,
        "most_active_members": most_active_members,
        "latest_posts": latest_posts,
        "latest_threads": latest_threads,
        "most_active_threads": most_active_threads,
        "most_viewed_threads": most_viewed_threads,
    }, context_instance=RequestContext(request))


def forum_category(request, category_id):
    
    category = get_object_or_404(ForumCategory, id=category_id)
    
    forums = category.forums.order_by("title")
    
    return render_to_response("agora/category.html", {
        "category": category,
        "forums": forums,
    }, context_instance=RequestContext(request))


def forum(request, forum_id):
    
    forum = get_object_or_404(Forum, id=forum_id)
    
    threads = forum.threads.order_by("-last_modified")
    
    return render_to_response("agora/forum.html", {
        "forum": forum,
        "threads": threads,
    }, context_instance=RequestContext(request))


def forum_thread(request, thread_id):
    thread = get_object_or_404(ForumThread, id=thread_id)
    
    if request.method == "POST" and request.user.is_authenticated:
        
        content = request.POST.get("content")
        subscribe = {"true": True, "false": False, False: False}.get(request.POST.get("subscribe", False), True)
        
        reply = ForumReply(thread=thread, author=request.user, content=content)
        reply.save()
        
        # subscribe the poster to the thread if requested (default value is True)
        if subscribe:
            thread.subscribe(reply.author, "email")
        
        # all users are automatically subscribed to onsite
        thread.subscribe(reply.author, "onsite")
        
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    
    order_type = request.GET.get("order_type", "asc")
    
    posts = ForumThread.objects.posts(thread, reverse=(order_type == "desc"))
    
    thread.inc_views()
    
    return render_to_response("agora/thread.html", {
        "thread": thread,
        "posts": posts,
        "order_type": order_type,
        "subscribed": thread.subscribed(request.user, "email"),
    }, context_instance=RequestContext(request))


@ajax
@login_required
def new_post(request, forum_id):
    
    member = request.user.get_profile()
    forum = get_object_or_404(Forum, id=forum_id)
    
    if request.method == "POST":
        
        title = request.POST.get("title")
        content = request.POST.get("content")
        subscribe = {"true": True, "false": False, False: False}.get(request.POST.get("subscribe", False), True)
        
        thread = ForumThread(forum=forum, title=title, content=content, author=request.user)
        thread.save()
        
        # subscribe the poster to the thread if requested (default value is True)
        if subscribe:
            thread.subscribe(thread.author, "email")
        
        # all users are automatically subscribed to onsite
        thread.subscribe(thread.author, "onsite")
        
        return HttpResponseRedirect(reverse("agora_thread", args=[thread.id]))
    
    return render_to_response("agora/new_post.html", {
        "member": member,
        "forum_id": forum_id,
    }, context_instance=RequestContext(request))


@ajax
@login_required
def reply(request, thread_id):
    
    member = request.user.get_profile()
    thread = get_object_or_404(ForumThread, id=thread_id)
    
    quote = request.GET.get("quote") # thread id to quote
    
    if quote:
        quote_reply = ForumReply.objects.get(id=int(quote))
        quote_content = "\"%s\"" % quote_reply.content
    else:
        quote_content = ""
    
    if request.method == "POST":
        content = request.POST.get("content")
        subscribe = {"true": True, "false": False, False: False}.get(request.POST.get("subscribe", False), True)
        
        reply = ForumReply(thread=thread, author=request.user, content=content)
        reply.save()
        
        # subscribe the poster to the thread if requested (default value is True)
        if subscribe:
            thread.subscribe(reply.author, "email")
        
        # all users are automatically subscribed to onsite
        thread.subscribe(reply.author, "onsite")
        
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    
    first_reply = not ForumReply.objects.filter(thread=thread, author=request.user).exists()
    
    return render_to_response("agora/reply.html", {
        "member": member,
        "thread": thread,
        "quote_content": quote_content,
        "subscribed": thread.subscribed(request.user, "email"),
        "first_reply": first_reply,
    }, context_instance=RequestContext(request))


@ajax
@login_required
def post_edit(request, post_kind, post_id):
    member = request.user.get_profile()
    
    if post_kind == "thread":
        post = get_object_or_404(ForumThread, id=post_id)
        thread_id = post.id
    elif post_kind == "reply":
        post = get_object_or_404(ForumReply, id=post_id)
        thread_id = post.thread.id
    else:
        raise Http404
    
    if not post.editable(request.user):
        raise Http404()
    
    if request.method == "POST":
        content = request.POST.get("content")
        
        post.content = content
        post.save()
        
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    
    return render_to_response("agora/post_edit.html", {
        "member": member,
        "post_kind": post_kind,
        "post": post,
    }, context_instance=RequestContext(request))


@ajax
@login_required
def subscribe(request, thread_id):
    user = request.user
    thread = get_object_or_404(ForumThread, pk=thread_id)
    
    if request.method == "POST":
        thread.subscribe(user, "email")
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    else:
        ctx = RequestContext(request, {"thread": thread})
        return render_to_response("agora/subscribe.html", ctx)


@ajax
@login_required
def unsubscribe(request, thread_id):
    user = request.user
    thread = get_object_or_404(ForumThread, pk=thread_id)
    
    if request.method == "POST":
        thread.unsubscribe(user, "email")
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    else:
        ctx = RequestContext(request, {"thread": thread})
        return render_to_response("agora/unsubscribe.html", ctx)


@login_required
def thread_updates(request):
    subscriptions = ThreadSubscription.objects.filter(user=request.user, kind="onsite")
    subscriptions = subscriptions.select_related("thread", "user")
    subscriptions = subscriptions.order_by("-thread__last_modified")
    
    if request.method == "POST":
        subscriptions.filter(pk=request.POST["thread_id"]).delete()
    
    ctx = {
        "subscriptions": subscriptions,
    }
    ctx = RequestContext(request, ctx)
    return render_to_response("agora/thread_updates.html", ctx)
