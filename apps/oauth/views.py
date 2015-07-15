# -*- coding: utf-8
from django.shortcuts import render
from oauth2_provider.views.generic import ProtectedResourceView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


class ApiEndpoint(ProtectedResourceView):
        # LOGIN API
        # Process
        # 1. 다른 웹사이트로부터 /api/hello/에 로그인 정보와 함께 요청이 들어온다.
        # 2. 로그인 정보를 확인하고, 유효할 경우 유저 정보와 토큰을 준다.
        # ( 일단 어떤 정보를 POST로 받고 그걸 그대로 출력하는 기능을 만들어보자 )

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(ApiEndpoint, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, OAuth2!')

    def post(self, request, *args, **kwargs):
        return HttpResponse('Welcome, ' + request.POST['a'])
