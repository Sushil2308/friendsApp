from django.urls import path
from .views import LoginProcess, UserSignUp, FriendRequestProcess, FriendRequestRetrival

urlpatterns = [
    path("login", LoginProcess.as_view(), name="User-Login-Process"),
    path("signup", UserSignUp.as_view(), name="User-SignUp-Process"),
    path("send-request", FriendRequestProcess.as_view(), name="Send-Friend-Request"),
    path(
        "get-friends",
        FriendRequestRetrival.as_view(),
        name="Get Friend Request Status Checker",
    ),
]
