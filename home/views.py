from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from buddies.models import Bookmark, Conversation, DirectMessage
from django.db.models import Q


def index(request):
    template_data = {}
    template_data['title'] = 'StudyBuddies'
    return render(request, 'home/index.html', {'template_data': template_data})


def about(request):
    template_data = {}
    template_data['title'] = 'About'
    return render(request, 'home/about.html', {'template_data': template_data})


@login_required
def dashboard(request):
    template_data = {}
    template_data['title'] = 'Dashboard'
    
    # Get recent bookmarks (last 5)
    recent_bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related('listing', 'listing__course', 'listing__university').order_by('-created_at')[:5]
    
    # Get recent conversations (last 5)
    recent_conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).select_related('participant1', 'participant2', 'listing').prefetch_related('messages').order_by('-updated_at')[:5]
    
    # Calculate unread message counts and get last messages
    total_unread = 0
    for conversation in recent_conversations:
        other_participant = conversation.get_other_participant(request.user)
        unread_count = conversation.messages.filter(
            sender=other_participant,
            read_at__isnull=True
        ).count()
        conversation.unread_count = unread_count
        total_unread += unread_count
        
        # Get last message
        last_message = conversation.messages.order_by('-created_at').first()
        conversation.last_message = last_message
    
    context = {
        'template_data': template_data,
        'recent_bookmarks': recent_bookmarks,
        'recent_conversations': recent_conversations,
        'total_unread': total_unread,
    }
    
    return render(request, 'home/dashboard.html', context)

