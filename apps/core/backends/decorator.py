from django.contrib.auth.hashers import check_password
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.utils.decorators import available_attrs
from functools import wraps
import time


def _user_required(test_func, raise_error=False, redirect_to=''):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            elif raise_error:
                raise PermissionDenied
            elif redirect_to:
                return redirect(redirect_to)
            return redirect('/')
        return _wrapped_view
    return decorator


# developer or sysop user is required; raise 403
def dev_required(view_func):
    return _user_required(
        lambda u: u.profile.flags['dev'],
        raise_error=True,
    )(view_func)


# anonymous user is required; redirect to
def anon_required(view_func, redirect_to=None):
    return _user_required(
        lambda u: not u.is_authenticated,
        redirect_to=redirect_to,
    )(view_func)


# real user is required (no test users); raise 403
def real_user_required(view_func):
    return _user_required(
        lambda u: not u.profile.test_only,
        raise_error=True,
    )(view_func)


# sudo mode is required
def sudo_required(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.has_usable_password():
            return view_func(request, *args, **kwargs)

        timestamp = int(request.session.get('sudo_timestamp', '0'))
        if time.time() - timestamp < 10 * 60:
            request.session['sudo_timestamp'] = time.time()
            return view_func(request, *args, **kwargs)

        fail = False
        if request.method == 'POST':
            password = request.POST.get('password', '')
            if check_password(password, user.password):
                request.session['sudo_timestamp'] = time.time()
                return redirect(request.get_full_path())

            fail = True
        return render(request, 'account/sudo.html', {'fail': fail})
    return _wrapped_view
