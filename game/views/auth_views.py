import base64

from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game.models.Player import Player


# TODO: change this to use TokenAuthentication
@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):

    def _decode_basic_auth_header(self, auth_header: str) -> tuple:
        decoded_auth_bytes = base64.b64decode(auth_header.split()[1])
        split_auth_string = decoded_auth_bytes.decode().split(':')
        return tuple(split_auth_string)

    #@method_decorator(ensure_csrf_cookie)
    def post(self, request):
        auth_header = request.headers['Authorization']
        username, password = self._decode_basic_auth_header(auth_header)
        if username is None or password is None:
            return Response({'detail': 'Please provide username and password.'}, status=HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is None:
            username_exists = Player.objects.filter(username=username).first()
            if not username_exists:
                new_player = Player(username=username)
                new_player.set_password(password)
                new_player.is_active = True
                new_player.save()
                authenticate(username=username, password=password)
                login(request, new_player)
                return Response({
                    'detail': f'New Player {username} created.',
                    'new': True
                })
            else:
                return Response(
                    {'detail': 'Invalid credentials or username already exists.'}, status=HTTP_400_BAD_REQUEST
                )

        if user.is_authenticated:
            login(request, user)
        return Response({'detail': 'Successfully logged in.'})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'User not logged in.'}, status=HTTP_400_BAD_REQUEST)

        logout(request)
        return Response({'detail': 'Successfully logged out.'})




