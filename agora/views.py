from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response

from django.contrib.auth.decorators import login_required

from agora.models import ForumCategory, Forum, UserPostCount, ForumThread, ForumReply


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
    
    most_active_forums = Forum.objects.order_by("-reply_count")[:5]
    most_viewed_forums = Forum.objects.order_by("-view_count")[:5]
    most_active_members = UserPostCount.objects.order_by("-count")[:5]
    
    latest_posts = ForumReply.objects.order_by("-created")[:10]
    latest_threads = ForumThread.objects.order_by("-last_modified")[:10]
    most_active_threads = ForumThread.objects.order_by("-reply_count")[:10]
    most_viewed_threads = ForumThread.objects.order_by("-view_count")[:10]
    
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
        member = request.user.get_profile()
        content = request.POST.get("content")
        reply = ForumReply(thread=thread, author=request.user, content=content)
        reply.save()
        
        # earn_game_points(member, "POSTED_FORUM_REPLY")
        
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    
    order_type = request.GET.get("order_type", "asc")
    
    posts = thread.replies.order_by("%screated" % (order_type == "desc" and "-" or ""))
    
    thread.inc_views()
    
    return render_to_response("agora/thread.html", {
        "thread": thread,
        "posts": posts,
        "order_type": order_type,
    }, context_instance=RequestContext(request))


@ajax
@login_required
def new_post(request, forum_id):
    
    member = request.user.get_profile()
    forum = get_object_or_404(Forum, id=forum_id)
    
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        
        thread = ForumThread(forum=forum, title=title, content=content, author=request.user)
        thread.save()
        
        # earn_points(member, "POSTED_FORUM_THREAD")
        
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
        
        reply = ForumReply(thread=thread, author=request.user, content=content)
        reply.save()
        
        # earn_game_points(member, "POSTED_FORUM_REPLY")
        
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    
    return render_to_response("agora/reply.html", {
        "member": member,
        "thread_id": thread_id,
        "quote_content": quote_content,
    }, context_instance=RequestContext(request))


@ajax
@login_required
def reply_edit(request, reply_id):
    member = request.user.get_profile()
    reply = get_object_or_404(ForumReply, id=reply_id)
    thread_id = reply.thread.id
    
    if not reply.editable(request.user):
        raise Http404()
    
    if request.method == "POST":
        content = request.POST.get("content")
        
        reply.content = content
        reply.save()
        
        return HttpResponseRedirect(reverse("agora_thread", args=[thread_id]))
    
    return render_to_response("agora/reply_edit.html", {
        "member": member,
        "reply": reply,
    }, context_instance=RequestContext(request))
