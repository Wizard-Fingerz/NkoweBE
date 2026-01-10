from django.db import models
from django.conf import settings
from django.utils import timezone

class DiscussionThread(models.Model):
    """
    Represents a discussion thread, e.g. 'General library questions'.
    """
    # Visibility options for public/private threads
    PUBLIC = 'public'
    PRIVATE = 'private'
    VISIBILITY_CHOICES = [
        (PUBLIC, 'Public (anyone can join)'),
        (PRIVATE, 'Private (approval needed)'),
    ]

    title = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussion_threads'
    )
    created_at = models.DateTimeField(default=timezone.now)
    pinned = models.BooleanField(default=False)
    visibility = models.CharField(
        max_length=7,
        choices=VISIBILITY_CHOICES,
        default=PUBLIC,
        help_text="Whether this thread is public (open to join) or private."
    )
    chat_enabled = models.BooleanField(
        default=True,
        help_text="Is chat (posting) enabled in this thread? The creator can turn it on/off."
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="joined_discussion_threads",
        help_text="Users who are members of this thread (creator is always a member).",
        blank=True,
    )
    requested_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="requesting_discussion_threads",
        help_text="Users who have requested to join (for private threads only).",
        blank=True,
    )

    class Meta:
        ordering = ['-pinned', '-created_at']

    def __str__(self):
        return f"{self.title} (by {self.created_by.get_full_name() or self.created_by.username})"

    @property
    def post_count(self):
        return self.posts.count()

    def is_public(self):
        return self.visibility == self.PUBLIC

    def is_private(self):
        return self.visibility == self.PRIVATE

    def is_member(self, user):
        # The creator is always considered a member
        return user and (user == self.created_by or self.members.filter(pk=user.pk).exists())

    def has_requested(self, user):
        if not user:
            return False
        return self.requested_members.filter(pk=user.pk).exists()

    def add_member(self, user):
        if user and not self.is_member(user):
            self.members.add(user)
            # Also remove from requested_members if present
            self.requested_members.remove(user)

    def request_to_join(self, user):
        if self.is_private() and user and not self.is_member(user):
            self.requested_members.add(user)

    def approve_request(self, user):
        if self.has_requested(user):
            self.add_member(user)

    def remove_member(self, user):
        if user and self.members.filter(pk=user.pk).exists():
            self.members.remove(user)
        # Creator cannot be removed
        if user == self.created_by:
            return

class DiscussionPost(models.Model):
    """
    A post/reply in a DiscussionThread.
    """
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussion_posts'
    )
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        snippet = self.content[:24] + ("…" if len(self.content) > 24 else "")
        return f"Post by {self.user.get_full_name() or self.user.username} in '{self.thread.title}': '{snippet}'"

# --- Optionally: Track which posts are unread for a user ---

class DiscussionThreadReadStatus(models.Model):
    """
    Optional: Keeps track of last read time per user and thread.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussion_thread_read_statuses'
    )
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name='read_statuses'
    )
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'thread')
        indexes = [
            models.Index(fields=["user", "thread"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} read {self.thread.title} at {self.last_read_at}"

# --- Optionally: Track which posts are read/unread by user (fine-grained) ---
# This can be extended for per-post read status.
