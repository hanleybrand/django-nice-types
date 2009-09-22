from django.conf import settings
from django.contrib.auth.decorators import login_required

import re

class RequireLoginMiddleware(object):
    """
    Middleware component that wraps the login_required decorator around 
    matching URL patterns. To use, add the class to MIDDLEWARE_CLASSES and 
    define LOGIN_REQUIRED_URLS and LOGIN_REQUIRED_URLS_EXCEPTIONS in your 
    settings.py. For example:
    ------
    LOGIN_REQUIRED_URLS = (
        r'/topsecret/(.*)$',
    )
    LOGIN_REQUIRED_URLS_EXCEPTIONS = (
        r'/topsecret/login(.*)$', 
        r'/topsecret/logout(.*)$',
    )
    ------                 
    LOGIN_REQUIRED_URLS is where you define URL patterns; each pattern must 
    be a valid regex.     
    
    LOGIN_REQUIRED_URLS_EXCEPTIONS is, conversely, where you explicitly 
    define any exceptions (like login and logout URLs).
    """
    def __init__(self):
        self.required = tuple([re.compile(url) for url in settings.LOGIN_REQUIRED_URLS])
        self.exceptions = tuple([re.compile(url) for url in settings.LOGIN_REQUIRED_URLS_EXCEPTIONS])
    
    def process_view(self,request,view_func,view_args,view_kwargs):
        # No need to process URLs if user already logged in
        if request.user.is_authenticated(): return None
        # An exception match should immediately return None
        for url in self.exceptions:
            if url.match(request.path): return None
        # Requests matching a restricted URL pattern are returned 
        # wrapped with the login_required decorator
        for url in self.required:
            if url.match(request.path): return login_required(view_func)(request,*view_args,**view_kwargs)
        # Explicitly return None for all non-matching requests
        return None

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

class AsUserMiddleware(object):    
    def process_request(self, request):
        if 'as_user' in request.GET and request.user.is_superuser:
            as_user = request.GET.get('as_user')
            rpc = request.GET.copy()
            del rpc['as_user']
            request.GET = rpc
            user = get_object_or_404(User, username=as_user)
            request.user = user

        if 'switch_user' in request.GET and (request.user.is_superuser or request.session.has_key('_switch_user')):
            request.session['_switch_user'] = True
            as_user = request.GET.get('switch_user')
            rpc = request.GET.copy()
            del rpc['switch_user']
            request.GET = rpc
            user = get_object_or_404(User, username=as_user)
            request.session['_auth_user_id'] = user.id
            request.user = user

        return None

