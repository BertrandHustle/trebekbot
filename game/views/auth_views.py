import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game.models import Player


class LoginView(APIView):

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        payload = json.loads(request.data['payload'])
        username, password = payload.get('username'), payload.get('password')
        if username is None or password is None:
            return JsonResponse({'detail': 'Please provide username and password.'}, status=400)

        user = authenticate(username=username, password=password)

        if user is None:
            username_exists = Player.objects.filter(username=username).first()
            if not username_exists:
                new_player = Player(username=username)
                new_player.set_password(password)
                new_player.is_active = True
                new_player.save()
                return Response({'detail': f'New Player {username} created.'})
            else:
                return Response({'detail': 'Invalid credentials or username already exists.'}, status=400)

        login(request, user)
        response = JsonResponse({'detail': 'Successfully logged in.'})
        return Response({'detail': 'Successfully logged in.'})


# @ensure_csrf_cookie
# def login_view(request):
#     data = json.loads(request.body)
#     username = data.get('username')
#     password = data.get('password')
#
#     if username is None or password is None:
#         return JsonResponse({'detail': 'Please provide username and password.'}, status=400)
#
#     user = authenticate(username=username, password=password)
#
#     if user is None:
#         username_exists = Player.objects.filter({'username': username}).first()
#         if not username_exists:
#             new_player = Player(name=username, password=password)
#             new_player.save()
#             return JsonResponse({'detail': f'New Player **{username}** created.'})
#         else:
#             return JsonResponse({'detail': 'Invalid credentials or username already exists.'}, status=400)
#
#     login(request, user)
#     response = JsonResponse({'detail': 'Successfully logged in.'})
#     response.headers = {'Access-Control-Allow-Credentials': True}
#     return JsonResponse({'detail': 'Successfully logged in.'})
#
#
# def logout_view(request):
#     if not request.user.is_authenticated:
#         return JsonResponse({'detail': 'You\'re not logged in.'}, status=400)
#
#     logout(request)
#     return JsonResponse({'detail': 'Successfully logged out.'})
#
#
# class SessionView(APIView):
#     authentication_classes = [SessionAuthentication, BasicAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     @staticmethod
#     def get():
#         return JsonResponse({'isAuthenticated': True})
#
#
# class GetUsername(APIView):
#     authentication_classes = [SessionAuthentication, BasicAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     @staticmethod
#     def get(request):
#         return JsonResponse({'username': request.user.username})


