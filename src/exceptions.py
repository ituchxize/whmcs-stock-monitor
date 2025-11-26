class WhmcsClientError(Exception):
    """Base exception for WHMCS client errors."""
    pass


class WhmcsAuthenticationError(WhmcsClientError):
    """Raised when authentication with WHMCS API fails."""
    pass


class WhmcsAPIError(WhmcsClientError):
    """Raised when WHMCS API returns an error response."""
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class WhmcsConnectionError(WhmcsClientError):
    """Raised when connection to WHMCS API fails."""
    pass


class WhmcsTimeoutError(WhmcsClientError):
    """Raised when WHMCS API request times out."""
    pass


class WhmcsValidationError(WhmcsClientError):
    """Raised when request validation fails."""
    pass
