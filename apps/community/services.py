"""Community Business Logic."""

from .models import Post, PostUpvote, PostReply, GlobalChat, Notice, Feedback, Setting
from django.shortcuts import get_object_or_404
from apps.accounts.services import record_activity

def create_post(user, title, body, tags):
    post = Post.objects.create(
        author=user,
        author_name=user.name,
        title=title,
        body=body,
        tags=tags or []
    )
    record_activity(user)
    return post

def toggle_upvote(user, post_id):
    post = get_object_or_404(Post, id=post_id)
    upvote = PostUpvote.objects.filter(post=post, user=user).first()
    
    if upvote:
        upvote.delete()
        action = "removed"
    else:
        PostUpvote.objects.create(post=post, user=user)
        action = "added"
        
    return {"status": "success", "action": action, "upvotes_count": post.upvotes.count()}

def add_reply(user, post_id, body):
    post = get_object_or_404(Post, id=post_id)
    reply = PostReply.objects.create(
        post=post,
        author=user,
        author_name=user.name,
        body=body
    )
    record_activity(user)
    return reply

def delete_post(user, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Check if user is author or moderator in views before calling this, or handle here
    post.delete()
    return True

def add_chat_message(user, text):
    msg = GlobalChat.objects.create(
        sender=user,
        sender_name=user.name,
        text=text
    )
    record_activity(user)
    return msg

def get_settings():
    settings = Setting.objects.all()
    # Convert list of Setting models to a dict config
    return {s.key: s.value for s in settings}

def update_setting(key, value):
    setting, created = Setting.objects.update_or_create(
        key=key,
        defaults={"value": value}
    )
    return setting
