class ResetPWMessage:
    title = '[SPARCS SSO] 비밀번호 재설정 / Reset Password'
    body = (
        '<h3>SPARCS SSO 비밀번호 재설정 안내</h3>'
        '<p>이 이메일을 사용하는 SPARCS SSO 계정에 대해 비밀번호 재설정이 요청되었습니다. '
        '다음 링크를 클릭하거나 주소창에 붙여 넣어 비밀번호를 재설정할 수 있습니다.</p>'
        '<p>링크: <a href="{0}">{0}</a></p><br/>'
        '<p>만일 인증을 요청한 적이 없다면, 이 이메일을 무시하세요.</p>'
    )


class EmailAuthMessage:
    title = '[SPARCS SSO] 이메일 인증 / Email Authentication'
    body = (
        '<h3>SPARCS SSO 이메일 인증</h3>'
        '<p>SPARCS SSO의 서비스를 사용하기 위해 이메일 소유 인증이 요청되었습니다. '
        '다음 링크를 클릭하거나 주소창에 붙여 넣어 이메일을 인증할 수 있습니다.</p>'
        '<p>링크: <a href="{0}">{0}</a></p><br/>'
        '<p style="color:red"><b>만일 인증을 요청한 적이 없다면, '
        '절대로 링크를 클릭하지 마세요.</b></p>'
    )
