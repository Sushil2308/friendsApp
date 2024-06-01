from django.db import models
from django.contrib.auth.models import User


class RequestStatus(models.Model):
    status = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.status


class FriendRequest(models.Model):
    requestedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    requestedTo = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver"
    )
    status = models.ForeignKey(RequestStatus, on_delete=models.CASCADE)
    requestedOn = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("requestedBy", "requestedTo")


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
