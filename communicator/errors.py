class ApiError(Exception):
    """
    Follows the RFC 7807 standard https://tools.ietf.org/html/rfc7807
    Example Usage:
        {
        "type": "https://example.com/probs/out-of-credit",
        "title": "You do not have enough credit.",
        "detail": "Your current balance is 30, but that costs 50.",
        "instance": "/account/12345/msgs/abc",
        "balance": 30,
        "accounts": ["/account/12345",
                     "/account/67890"]
        }
    """

    def __init__(self, type, title, status, detail, instance):
        self.type = type
        self.title = title
        self.status = status
        self.detail = detail
        self.instance = instance


class CommError(Exception):
    """A standard error from which to extend, that can be easily converted to
     an API error if needed. The code should be a unique numeric value, and
     the detail is optional."""

    def __init__(self, code: int, title, detail=""):
        self.code = code
        self.title = title
        self.detail = detail
