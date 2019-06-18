

class DatadogException(BaseException):
    pass


class DatadogApiKeyError(DatadogException):
    pass


class DatadogApplicationKeyError(DatadogException):
    pass


class DatadogConnectionError(DatadogException):
    pass
