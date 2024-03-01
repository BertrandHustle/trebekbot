# https://code.djangoproject.com/ticket/34613#comment:10

from http import cookies

from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponseBase
from django.middleware.http import MiddlewareMixin

cookies.Morsel._flags.add("partitioned")
cookies.Morsel._reserved.setdefault("partitioned", "Partitioned")


class CookiePartitioningMiddleware(MiddlewareMixin):
    def process_response(self, request: HttpRequest, response: HttpResponseBase) -> HttpResponseBase:
        for name in (
            getattr(settings, f"{prefix}_COOKIE_NAME")
            for prefix in ("CSRF", "SESSION", "LANGUAGE")
            if getattr(settings, f"{prefix}_COOKIE_SECURE")
        ):
            if cookie := response.cookies.get(name):
                cookie["Partitioned"] = True

        return response
