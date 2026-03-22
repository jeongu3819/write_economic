def api_response(data=None, error=None, success=True):
    """Consistent API response wrapper."""
    return {
        "success": success,
        "data": data,
        "error": error,
    }


def api_error(message: str, status_code: int = 400):
    """Create error response dict (raise HTTPException separately)."""
    return {
        "success": False,
        "data": None,
        "error": message,
    }
