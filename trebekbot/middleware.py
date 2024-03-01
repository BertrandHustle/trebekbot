# https://code.djangoproject.com/ticket/34613#comment:10

from http import cookies

from django.http.request import HttpRequest
from django.http.response import HttpResponseBase
from django.middleware.http import MiddlewareMixin

cookies.Morsel._flags.add('partitioned')
cookies.Morsel._reserved.setdefault('partitioned', 'Partitioned')


class CookiePartitioningMiddleware(MiddlewareMixin):
    def process_response(self, request: HttpRequest, response: HttpResponseBase) -> HttpResponseBase:
        csrf_cookie = response.cookies.get('CSRF_COOKIE_NAME')
        session_id_cookie = response.cookies.get('SESSION_COOKIE_NAME')
        if csrf_cookie:
            csrf_cookie['Partitioned'] = True
        if session_id_cookie:
            session_id_cookie['Partitioned'] = True
        return response
