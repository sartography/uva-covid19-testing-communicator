from flask import request

from communicator.errors import CommError
from communicator.models.user import User


class UserService(object):
    """Provides details about the current User as read in from Shibboleth headers """
    # ----------------------------------------
    # Shibboleth Authentication Headers
    # ----------------------------------------
    # X-Remote-Cn: Daniel Harold Funk (dhf8r)
    # X-Remote-Sn: Funk
    # X-Remote-Givenname: Daniel
    # X-Remote-Uid: dhf8r
    # Eppn: dhf8r@virginia.edu
    # Cn: Daniel Harold Funk (dhf8r)
    # Sn: Funk
    # Givenname: Daniel
    # Uid: dhf8r
    # X-Remote-User: dhf8r@virginia.edu
    # X-Forwarded-For: 128.143.0.10
    # X-Forwarded-Host: dev.crconnect.uvadcos.io
    # X-Forwarded-Server: dev.crconnect.uvadcos.io
    # Connection: Keep-Alive

    def get_user_info(self):
        uid = request.headers.get("Uid")
        cn = request.headers.get("Cn")
        if not uid:
            uid = request.headers.get("X-Remote-Uid")
        if not uid:
            raise CommError(1100, "invalid_sso_credentials", r"'Uid' nor 'X-Remote-Uid' were present in the headers: %s"% str(request.headers))
        return User(uid, cn)