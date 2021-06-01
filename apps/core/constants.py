from enum import Enum


# Result codes for social account connections
class SocialConnectResult(Enum):
    # Code for 'Your social network account has been connected / renewed'
    CONNECT_SUCCESS = 0
    # Code for 'This social network account is already connected by other person'
    ALREADY_CONNECTED = 1
    # Code for 'You cannot renew your information with the other KAIST portal account'
    KAIST_IDENTITY_MISMATCH = 2
    # Code for 'Please grant all requested permissions'
    PERMISSION_NEEDED = 3
    # Code for 'To disconnect SNS account, either password has been set or other SNS accounts should be connected'
    ONLY_CONNECTION = 4
    # Code for 'Your social network account has been disconnected'
    DISCONNECT_SUCCESS = 5
    # Invalid site code (not one of 'TW', 'FB', 'KAIST')
    SITE_INVALID = 6
    # Renewing is not applicable for the given site (renewing only makes sense for KAIST)
    RENEW_UNNECESSARY = 7
    # Account is test only
    TEST_ONLY = 8


class EmailVerificationResult(Enum):
    # Code for 'Your email has been verified'
    SUCCESS = 1
    # Code for 'Expired or invalid verification token'
    TOKEN_INVAILD = 2
    # Code for 'This email address is invalid or already used'
    EMAIL_IN_USE = 3
    # Code for 'Email updated; check the inbox'
    UPDATED = 4
    # Code for 'Verification email has been sent'
    SENT = 5
