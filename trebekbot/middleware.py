# https://code.djangoproject.com/ticket/34613#comment:10

from http import cookies

from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponseBase
from django.middleware.http import MiddlewareMixin

cookies.Morsel._flags.add('partitioned')
cookies.Morsel._reserved.setdefault('partitioned', 'Partitioned')


class CookiePartitioningMiddleware(MiddlewareMixin):
    def process_response(self, request: HttpRequest, response: HttpResponseBase) -> HttpResponseBase:
        csrf_cookie_name = getattr(settings, 'CSRF_COOKIE_NAME')
        session_id_name = getattr(settings, 'SESSION_COOKIE_NAME')
        csrf_cookie = response.cookies.get(csrf_cookie_name)
        session_id_cookie = response.cookies.get(session_id_name)
        if csrf_cookie:
            csrf_cookie['Partitioned'] = True
        if session_id_cookie:
            session_id_cookie['Partitioned'] = True
        return response
