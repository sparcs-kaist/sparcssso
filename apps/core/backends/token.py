from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from apps.core.models import EmailAuthToken, ResetPWToken
from secrets import token_hex
import datetime


RESET_PW_MSG_TITLE = '[SPARCS SSO] 비밀번호 재설정 / Reset Password'
RESET_PW_MSG_BODY = (
    '<h3>SPARCS SSO 비밀번호 재설정 안내</h3>'
    '<p>이 이메일을 사용하는 SPARCS SSO 계정에 대해 비밀번호 재설정이 요청되었습니다. '
    '다음 링크를 클릭하거나 주소창에 붙여 넣어 비밀번호를 재설정할 수 있습니다.</p>'
    '<p>링크: <a href="{0}">{0}</a></p><br/>'
    '<p>만일 인증을 요청한 적이 없다면, 이 이메일을 무시하세요.</p>'
)

EMAIL_AUTH_MSG_TITLE = '[SPARCS SSO] 이메일 인증 / Email Authentication'
EMAIL_AUTH_MSG_BODY = (
    '<h3>SPARCS SSO 이메일 인증</h3>'
    '<p>SPARCS SSO의 서비스를 사용하기 위해 이메일 소유 인증이 요청되었습니다. '
    '다음 링크를 클릭하거나 주소창에 붙여 넣어 이메일을 인증할 수 있습니다.</p>'
    '<p>링크: <a href="{0}">{0}</a></p><br/>'
    '<p style="color:red"><b>만일 인증을 요청한 적이 없다면, '
    '절대로 링크를 클릭하지 마세요.</b></p>'
)


# issue reset pw token to user
def token_issue_reset_pw(user):
    if user.email.endswith('@sso.sparcs.org'):
        return

    while True:
        tokenid = token_hex(24)
        if not ResetPWToken.objects.filter(tokenid=tokenid).count():
            break

    tomorrow = timezone.now() + datetime.timedelta(days=1)
    ResetPWToken.objects.filter(user=user).delete()
    ResetPWToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()

    url = '{}/account/password/reset/{}'.format(settings.DOMAIN, tokenid)
    send_mail(RESET_PW_MSG_TITLE, '',
              'noreply@sso.sparcs.org', [user.email],
              html_message=RESET_PW_MSG_BODY.format(url))


# issue email auth token to user
def token_issue_email_auth(user):
    if user.email.endswith('@sso.sparcs.org'):
        return

    while True:
        tokenid = token_hex(24)
        if not EmailAuthToken.objects.filter(tokenid=tokenid).count():
            break

    tomorrow = timezone.now() + datetime.timedelta(days=1)
    EmailAuthToken.objects.filter(user=user).delete()
    EmailAuthToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()

    url = '{}/account/email/{}'.format(settings.DOMAIN, tokenid)
    send_mail(EMAIL_AUTH_MSG_TITLE, '',
              'noreply@sso.sparcs.org', [user.email],
              html_message=EMAIL_AUTH_MSG_BODY.format(url))
