from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation, Message, CustomUser
from .forms import ChatForm
from .services import chat_service
import json
from django.utils import timezone
import logging
import os


@login_required
def chat_home(request):
    """Main chat interface with conversation list and chat area"""
    # Get all conversations for the user
    conversations = Conversation.objects.filter(
        user=request.user).order_by('-created_at')

    # Get latest active conversation or create a new one
    active_conversation = conversations.first()
    if not active_conversation:
        active_conversation = Conversation.objects.create(
            user=request.user, title="New Chat")

    # Get messages for active conversation
    messages = Message.objects.filter(
        conversation=active_conversation
    ).order_by('timestamp')

    # Update user's last activity
    request.user.last_chat_activity = timezone.now()
    request.user.save()

    return render(request, 'chat/home.html', {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
        'form': ChatForm()
    })


@login_required
def conversation_detail(request, conversation_id):
    """Load a specific conversation"""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, user=request.user)
    conversations = Conversation.objects.filter(
        user=request.user).order_by('-created_at')
    messages = Message.objects.filter(
        conversation=conversation).order_by('timestamp')

    return render(request, 'chat/home.html', {
        'conversations': conversations,
        'active_conversation': conversation,
        'messages': messages,
        'form': ChatForm()
    })


@login_required
@csrf_exempt
def send_message(request):
    """AJAX endpoint for sending messages"""
    logger = logging.getLogger(__name__)
    if request.method == 'POST':
        print("DEBUG POST DATA:", request.POST)
        form = ChatForm(request.POST)
        conversation_id = request.POST.get('conversation_id')
        if not conversation_id:
            logger.error("Missing conversation_id in POST data")
            return JsonResponse({'error': 'Missing conversation_id'}, status=400)
        if not form.is_valid():
            logger.error(f"Form is not valid: {form.errors}")
            return JsonResponse({'error': 'Invalid form', 'form_errors': form.errors, 'conversation_id': conversation_id}, status=400)
        try:
            conversation = get_object_or_404(
                Conversation, id=conversation_id, user=request.user)
        except Exception as e:
            logger.error(f"Conversation not found: {e}")
            return JsonResponse({'error': 'Conversation not found', 'conversation_id': conversation_id}, status=400)
        message = form.cleaned_data['message']

        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            content=message,
            is_user=True
        )

        # Get AI response
        history = Message.objects.filter(
            conversation=conversation
        ).order_by('timestamp').values('content', 'is_user')

        # Check for OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("OPENAI_API_KEY is not set in environment.")
            return JsonResponse({'error': 'AI service unavailable. Contact admin.', 'conversation_id': conversation_id}, status=500)

        try:
            ai_response = chat_service.get_response(message, list(history))
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return JsonResponse({'error': 'AI service error', 'conversation_id': conversation_id}, status=500)

        # Save AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            content=ai_response,
            is_user=False
        )

        # Update conversation title if first message
        if conversation.messages.count() == 2:  # User + AI messages
            conversation.title = f"{message[:30]}..." if len(
                message) > 30 else message
            conversation.save()

        return JsonResponse({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.strftime("%H:%M"),
                'is_user': True
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'timestamp': ai_message.timestamp.strftime("%H:%M"),
                'is_user': False
            },
            'conversation_title': conversation.title,
            'conversation_id': conversation.id
        })
    logger.error(f"Invalid request method: {request.method}")
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def new_conversation(request):
    """Create a new conversation"""
    conversation = Conversation.objects.create(
        user=request.user, title="New Chat")
    return redirect('chat:conversation_detail', conversation_id=conversation.id)


@login_required
@csrf_exempt
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, user=request.user)
    conversation.delete()
    return JsonResponse({'status': 'success'})


@login_required
def update_title(request, conversation_id):
    """Update conversation title"""
    if request.method == 'POST':
        conversation = get_object_or_404(
            Conversation, id=conversation_id, user=request.user)
        new_title = request.POST.get('title', '')[:200]
        if new_title:
            conversation.title = new_title
            conversation.save()
            return JsonResponse({'status': 'success', 'new_title': conversation.title})
    return JsonResponse({'status': 'error'}, status=400)
