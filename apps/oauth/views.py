# -*- coding: utf-8
from django.shortcuts import render
from oauth2_provider.views.generic import ProtectedResourceView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import urllib2
import base64


# def getToken


# http://localhost:8000/o/authorize/?state=random_state_string&response_type=token&client_id=1PCwIzWWpLRrSiJtadffc7owJYsCsTOXjHeGSvpX
# 여기로 요청을 보내면, 바로 토큰을 줍니다 이제.
# 얘를 리다이렉트로 쏘면 get으로 정보들이 가기 때문에, 그걸 그냥 바로 쓰면 될 것 같네요.
# 아, get으로 주는게 아니고 #으로 달려서 가는데 이게 뭐하는 짓이죠?

# import urllib2
# req = urllib2.Request('https://api.twitch.tv/kraken/streams/test_channel')
# req.add_header('Accept', 'application/vnd.twitchtv.v2+json')
# resp = urllib2.urlopen(req)
# content = resp.read()

# Have To Use cURL
# Read Following URL :
# http://stackoverflow.com/questions/17560053/curl-to-python-conversion


class GetUserInform(ProtectedResourceView):
        # Get User's Informations
        # Conditions
        # 1. 유저는 로그인되어 있어야한다.
        # Process
        # 1. 다른 웹사이트로부터 /api/hello/에 요청이 들어온다.
        # 2-1. 로그인이 되어 있는 경우, ...?
        # ( 일단 어떤 정보를 POST로 받고 그걸 그대로 출력하는 기능을 만들어보자 )

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(GetUserInform, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, OAuth2!')

    def post(self, request, *args, **kwargs):
        return HttpResponse('Welcome, ' + request.POST['a'])
