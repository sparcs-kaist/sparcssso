import logging
import time
from functools import wraps

from django.contrib.auth.hashers import check_password
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.decorators import available_attrs

from apps.core.backends.sudo import sudo_password_needed, sudo_renew


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
        logger = logging.getLogger('sso.auth')
        user = request.user
        if not user.has_usable_password():
            return view_func(request, *args, **kwargs)

        if not sudo_password_needed(request.session):
            sudo_renew(request.session)
            return view_func(request, *args, **kwargs)

        fail = False
        if request.method == 'POST':
            password = request.POST.get('password', '')
            success = check_password(password, user.password)

            log_msg = 'success' if success else 'fail'
            (logger.info if success else logger.warning)(f'sudo.{log_msg}', {
                'r': request,
                'extra': [('path', request.path)],
            })

            if success:
                sudo_renew(request.session)
                return redirect(request.get_full_path())

            fail = True
        return render(request, 'account/sudo.html', {'fail': fail})
    return _wrapped_view
