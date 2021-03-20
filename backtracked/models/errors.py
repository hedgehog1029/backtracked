class ApiError(Exception):
    def __init__(self, endpoint, status, message):
        self.endpoint = endpoint
        self.status = status
        self.message = f"Request failed: {status} {endpoint} ({message})"

class AuthorizationError(Exception):
    pass
