class FetchingError(Exception):
    pass


class ContinueException(Exception):
    def __init__(self, message, status_code=None):
        self.message = message or "Message not provided"
        self.status_code = status_code or "Not applicable"

    def __str__(self):
        return f"Message: {self.message}. Status code: {self.status_code}"
