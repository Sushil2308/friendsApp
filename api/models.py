from django.db import models
from django.contrib.auth.models import User


class RequestStatus(models.Model):
    status = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.status


class FriendRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    send_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver"
    )
    status = models.ForeignKey(RequestStatus, on_delete=models.CASCADE)
    send_request_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("sender", "send_to")


class UserFriends(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, null=False, related_name="user"
    )
    friend = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="friend", null=False
    )
    accepted_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "friend")
