import datetime
from secrets import token_hex

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.core.models import EmailAuthToken, ResetPWToken


RESET_PW_MSG_TITLE = '[SPARCS SSO] 비밀번호 재설정 / Reset Password'
RESET_PW_MSG_BODY = (
    '<h3>SPARCS SSO 비밀번호 재설정 안내</h3>'
    '<p>안녕하세요, {name}님</p>'
    '<p>SPARCS SSO 계정에 대한 비밀번호 재설정 요청이 있었습니다.</p>'
    '<p>다음 링크를 클릭하거나 주소창에 붙여 넣어 비밀번호를 재설정할 수 있습니다.</p>'
    '<p><a href="{link}">{link}</a></p>'
    '<p>만일 비밀번호 재설정을 요청한 적이 없다면, 이 이메일을 무시하세요.</p>'
    '<br/>'
    '<h3>Confirm your password reset</h3>'
    '<p>Hi, {name}</p>'
    '<p>You tried to reset the password of your SPARCS SSO account.</p>'
    '<p>To reset your password, click the link below:</p>'
    '<p><a href="{link}">{link}</a></p>'
    '<p>If you did not request a password reset, please ignore this email.</p>'
)

EMAIL_AUTH_MSG_TITLE = '[SPARCS SSO] 이메일 인증 / Email Authentication'
EMAIL_NEWBIE_MSG_BODY = (
    '<h3>SPARCS SSO 이메일 인증</h3>'
    '<p>안녕하세요, {name}님</p>'
    '<p>SPARCS SSO 회원 가입을 환영합니다!</p>'
    '<p>다음 링크를 클릭하거나 주소창에 붙여 넣어 이메일 {email}을 인증할 수 있습니다.</p>'
    '<p><a href="{link}">{link}</a></p><br/>'
    '<p style="color:red"><b>만일 인증을 요청한 적이 없다면, '
    '절대로 링크를 클릭하지 마세요.</b></p>'
    '<br/>'
    '<h3>Verify your email address</h3>'
    '<p>Hi, {name}</p>'
    '<p>Thank you for signing in to SPARCS SSO!</p>'
    '<p>To verify your email address {email}, click the link below:</p>'
    '<p><a href="{link}">{link}</a></p><br/>'
    '<p style="color:red"><b>If you did not change your email address, '
    'please DO NOT click the link.</b></p>'
)
EMAIL_AUTH_MSG_BODY = (
    '<h3>SPARCS SSO 이메일 인증</h3>'
    '<p>안녕하세요, {name}님</p>'
    '<p>SPARCS SSO 계정에 대한 이메일 주소 변경 요청이 있었습니다.</p>'
    '<p>다음 링크를 클릭하거나 주소창에 붙여 넣어 이메일 {email}을 인증할 수 있습니다.</p>'
    '<p><a href="{link}">{link}</a></p>'
    '<p style="color:red"><b>만일 인증을 요청한 적이 없다면, '
    '절대로 링크를 클릭하지 마시고 sso.sysop@sparcs.org로 신고해주세요.</b></p>'
    '<br/>'
    '<h3>Verify your new email address</h3>'
    '<p>Hi, {name}</p>'
    '<p>You changed your email address for your SPARCS SSO account.</p>'
    '<p>To verify your new email {email}, click the link below:</p>'
    '<p><a href="{link}">{link}</a></p>'
    '<p style="color:red"><b>If you did not sign in, please DO NOT click '
    'the link and report us (sso.sysop@sparcs.org).</b></p>'
)

EMAIL_SENDER = 'noreply@sso.sparcs.org'


# issue reset pw token to user
def token_issue_reset_pw(user):
    ResetPWToken.objects.filter(user=user).delete()
    while True:
        tokenid = token_hex(24)
        if not ResetPWToken.objects.filter(tokenid=tokenid).count():
            break

    tomorrow = timezone.now() + datetime.timedelta(days=1)
    ResetPWToken.objects.filter(user=user).delete()
    ResetPWToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()

    url = f'{settings.DOMAIN}/account/password/reset/{tokenid}'
    msg = RESET_PW_MSG_BODY.format(
        name=user.first_name,
        link=url,
    )
    send_mail(RESET_PW_MSG_TITLE, '', EMAIL_SENDER,
              [user.email], html_message=msg)


# issue email auth token to user
def token_issue_email_auth(user, newbie=False):
    EmailAuthToken.objects.filter(user=user).delete()
    while True:
        tokenid = token_hex(24)
        if not EmailAuthToken.objects.filter(tokenid=tokenid).count():
            break

    tomorrow = timezone.now() + datetime.timedelta(days=1)
    EmailAuthToken.objects.filter(user=user).delete()
    EmailAuthToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()

    email = user.profile.email_new if user.profile.email_authed else user.email
    url = f'{settings.DOMAIN}/account/email/verify/{tokenid}'
    template = EMAIL_NEWBIE_MSG_BODY if newbie else EMAIL_AUTH_MSG_BODY
    msg = template.format(
        name=user.first_name,
        email=email,
        link=url,
    )
    send_mail(EMAIL_AUTH_MSG_TITLE, '', EMAIL_SENDER,
              [email], html_message=msg)
