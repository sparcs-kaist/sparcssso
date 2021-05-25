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
