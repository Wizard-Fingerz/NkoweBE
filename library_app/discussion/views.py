from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import DiscussionThread, DiscussionPost, DiscussionThreadReadStatus
from .serializers import (
    DiscussionThreadSerializer,
    DiscussionPostSerializer,
    DiscussionThreadReadStatusSerializer,
)


class DiscussionThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Discussion Threads, including joining, requesting, approving, toggling chat, etc.
    """
    queryset = DiscussionThread.objects.all().prefetch_related('members', 'requested_members', 'posts', 'read_statuses')
    serializer_class = DiscussionThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        List all threads. Shows public threads and private threads where user is creator/member/requested.
        """
        user = self.request.user
        qs = DiscussionThread.objects.all().prefetch_related('members', 'requested_members', 'posts')
        # Filter to public or threads where user is creator/member/requested
        return qs.filter(
            models.Q(visibility=DiscussionThread.PUBLIC)
            | models.Q(created_by=user)
            | models.Q(members=user)
            | models.Q(requested_members=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        """
        Join a public thread or request join for a private thread.
        """
        thread = self.get_object()
        user = request.user

        if thread.is_member(user):
            return Response({'detail': 'Already a member.'}, status=400)

        if thread.is_public():
            thread.add_member(user)
            return Response({'status': 'joined'})
        else:  # private
            if thread.has_requested(user):
                return Response({'detail': 'Join request already sent.'}, status=400)
            thread.request_to_join(user)
            return Response({'status': 'request_sent'})

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Approve a user's join request (creator only).
        """
        thread = self.get_object()
        user = request.user

        if thread.created_by != user:
            return Response({'detail': 'Only the creator can approve requests.'}, status=403)
        request_user_id = request.data.get('user_id')
        if not request_user_id:
            return Response({'detail': 'user_id required.'}, status=400)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        applicant = get_object_or_404(User, id=request_user_id)
        if not thread.has_requested(applicant):
            return Response({'detail': 'No such request.'}, status=404)
        thread.approve_request(applicant)
        return Response({'status': 'approved'})

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def remove_member(self, request, pk=None):
        """
        Remove a member (creator or self-removal).
        """
        thread = self.get_object()
        user = request.user
        member_id = request.data.get('user_id')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if member_id:
            member = get_object_or_404(User, id=member_id)
        else:
            member = user

        if member == thread.created_by:
            return Response({'detail': 'Cannot remove thread creator.'}, status=400)

        if thread.created_by == user or member == user:
            thread.remove_member(member)
            return Response({'status': 'removed'})
        else:
            return Response({'detail': 'Not allowed.'}, status=403)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def toggle_chat(self, request, pk=None):
        """
        Enable or disable chat (posting) for thread. Creator only.
        """
        thread = self.get_object()
        user = request.user
        if thread.created_by != user:
            return Response({'detail': 'Only creator can change chat status.'}, status=403)
        enable = request.data.get('enable')
        if enable is None:
            return Response({'detail': 'Missing "enable" field.'}, status=400)
        thread.chat_enabled = bool(enable)
        thread.save()
        return Response({'chat_enabled': thread.chat_enabled})

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def toggle_visibility(self, request, pk=None):
        """
        Change thread from public <-> private. Creator only.
        """
        thread = self.get_object()
        user = request.user
        if thread.created_by != user:
            return Response({'detail': 'Only creator can change visibility.'}, status=403)
        set_public = request.data.get('public')
        if set_public is None:
            return Response({'detail': 'Missing "public" field.'}, status=400)
        thread.visibility = DiscussionThread.PUBLIC if set_public else DiscussionThread.PRIVATE
        thread.save()
        return Response({'visibility': thread.visibility})

    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated])
    def members(self, request, pk=None):
        """
        Get all members of the thread (includes creator).
        """
        thread = self.get_object()
        member_objs = thread.members.all()
        members = [{
            "id": thread.created_by.id,
            "username": thread.created_by.username,
            "full_name": (thread.created_by.get_full_name() if hasattr(thread.created_by, "get_full_name") else thread.created_by.username),
            "is_creator": True,
        }]
        for member in member_objs:
            if member != thread.created_by:
                members.append({
                    "id": member.id,
                    "username": member.username,
                    "full_name": (member.get_full_name() if hasattr(member, "get_full_name") else member.username),
                    "is_creator": False,
                })
        return Response(members)


class DiscussionPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for posts: list/create per thread, edit/delete own.
    """
    queryset = DiscussionPost.objects.select_related('thread', 'user').all()
    serializer_class = DiscussionPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        thread_id = self.request.query_params.get("thread")
        qs = DiscussionPost.objects.all()
        if thread_id:
            qs = qs.filter(thread_id=thread_id)
        return qs.order_by('created_at')

    def perform_create(self, serializer):
        thread_id = self.request.data.get('thread')
        if not thread_id:
            raise Exception("Thread required")
        thread = get_object_or_404(DiscussionThread, pk=thread_id)
        user = self.request.user
        # Only allow create if chat_enabled and (user is member or creator)
        if not (thread.chat_enabled and (thread.is_member(user) or thread.created_by == user)):
            raise Exception("No permission to post to this thread.")
        post = serializer.save(user=user, thread=thread)
        # Optionally update last read status
        DiscussionThreadReadStatus.objects.update_or_create(
            user=user, thread=thread, defaults={'last_read_at': post.created_at}
        )

    def update(self, request, *args, **kwargs):
        """
        Only allow post owner to update.
        """
        instance = self.get_object()
        if instance.user != request.user:
            return Response({'detail': 'Cannot edit others\' posts.'}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Only allow post owner to delete.
        """
        instance = self.get_object()
        if instance.user != request.user:
            return Response({'detail': 'Cannot delete others\' posts.'}, status=403)
        return super().destroy(request, *args, **kwargs)


class DiscussionThreadReadStatusViewSet(viewsets.ModelViewSet):
    """
    (Optional) API for tracking which threads user has read, and updating last read.
    """
    serializer_class = DiscussionThreadReadStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return DiscussionThreadReadStatus.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def mark_read(self, request):
        """
        Mark a thread as read (update last_read_at).
        """
        thread_id = request.data.get("thread_id")
        thread = get_object_or_404(DiscussionThread, pk=thread_id)
        obj, _ = DiscussionThreadReadStatus.objects.update_or_create(
            user=request.user, thread=thread,
            defaults={"last_read_at": timezone.now()}
        )
        return Response({'status': 'marked as read'})

