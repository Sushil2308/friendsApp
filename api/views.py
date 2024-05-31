from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import RequestStatus, FriendRequest, UserFriends
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import F, Q
from django.core.paginator import Paginator


class LoginProcess(APIView):

    def post(self, request):
        try:
            username = request.data.get("username")
            password = request.data.get("password")
            if not username or not password:
                return Response(
                    {"error": "Please provide both username and password"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = authenticate(username=username, password=password)
            if not user:
                return Response(
                    {"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
                )
            userToken, _ = Token.objects.get_or_create(user=user)
            return Response(
                {"token": userToken.key, "username": username},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class UserSignUp(APIView):

    def post(self, request):
        try:
            username = request.data.get("username")
            password = request.data.get("password")
            email = request.data.get("email")
            if not username or not password or not email:
                return Response(
                    {"error": "Please provide both username, password and email"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(username=username).exists():
                return Response(
                    {"error": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = User.objects.create_user(
                username=username, password=password, email=email
            )
            userToken, _ = Token.objects.get_or_create(user=user)
            if not _:
                return Response(
                    {
                        "error": "Unable to process your request at this time, pls try again later"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {"token": userToken.key, "username": username},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class FriendRequestProcess(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            sender = request.user
            receiver = User.objects.get(username=request.data.get("receiver"))
            if sender == receiver:
                return Response(
                    {"error": "You can't send friend request to yourself"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if UserFriends.objects.filter(
                user_id=sender.id, friend_id=receiver.id
            ).exists():
                return Response(
                    {"error": "You are already friends with this user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if FriendRequest.objects.filter(
                sender_id=sender.id, send_to_id=receiver.id
            ).exists():
                return Response(
                    {"error": "Friend request already sent to this user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            currentTime = timezone.now()
            oneMinuteAgo = currentTime - timezone.timedelta(minutes=1)
            if (
                FriendRequest.objects.filter(
                    sender_id=sender.id,
                    send_request_on__range=[oneMinuteAgo, currentTime],
                ).count()
                > 3
            ):
                return Response(
                    {"error": "You can't send more than 3 friend requests in a minute"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            requrstStatus = RequestStatus.objects.get(status="Pending")
            FriendRequest.objects.create(
                sender_id=sender.id, send_to_id=receiver.id, status=requrstStatus
            )
            return Response(
                {"message": "Friend request sent successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FriendRequestRetrival(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.query_params.get("statusType", None):
                statusType = request.query_params.get("statusType", None)
                if not statusType:
                    return Response(
                        {"error": "Please provide statusType"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # When You want to get all friend requests which is accepted by the user Then send statusType as "Accepted"
                # When You want to get all friend requests which is pending Then send statusType as "Pending"
                statusType = RequestStatus.objects.get(status=statusType)
                friendObjects = FriendRequest.objects.filter(
                    sender_id=request.user.id, status_id=statusType.id
                )
                if statusType.status.lower() == "pending":
                    return Response(
                        friendObjects.values(
                            requestTo=F("send_to__username"),
                            requestedOn=F("send_request_on"),
                        ),
                        status=status.HTTP_200_OK,
                    )
                if statusType.status.lower() == "rejected":
                    return Response(
                        friendObjects.values(
                            rejectedBy=F("send_to__username"),
                            requestedOn=F("send_request_on"),
                        ),
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    friendObjects.values(
                        acceptedBy=F("send_to__username"),
                        requestedOn=F("send_request_on"),
                    ),
                    status=status.HTTP_200_OK,
                )
            if request.query_params.get("searchTerm", None):
                searchTerm = request.query_params.get("searchTerm", None)
                pageNo = request.query_params.get("pageNo", 1)
                perPage = request.query_params.get("perPage", 10)
                if not pageNo  or not pageNo > 0:
                    return Response(
                        {"error": "Please provide valid pageNo"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not perPage or not perPage > 0:
                    return Response(
                        {"error": "Please provide valid perPage"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                pageNo = int(pageNo)
                perPage = int(perPage)
                userObjects = dict()
                if searchTerm:
                    userObjects = User.objects.filter(
                        Q(email=searchTerm) | Q(username__icontains=searchTerm)
                    ).values_list("username", flat=True)
            else:
                userObjects = User.objects.values_list("username", flat=True)
            paginator = Paginator(userObjects, perPage)
            return Response(
                {
                    "total": paginator.count,
                    "pageNo": pageNo,
                    "perPage": perPage,
                    "pagesCount": paginator.num_pages,
                    "userList": list(paginator.page(pageNo)),
                },
                status=status.HTTP_200_OK,
            )
        except RequestStatus.DoesNotExist:
            return Response(
                {"error": "Invalid statusType"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
