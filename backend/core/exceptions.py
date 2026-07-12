from rest_framework.views import exception_handler
from rest_framework.response import Response


def voa_exception_handler(exc, context):
    """Wraps DRF's default exception handler to return a consistent error shape."""
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "errors": response.data,
        }
        return response

    return Response(
        {"success": False, "errors": {"detail": "An unexpected server error occurred."}},
        status=500,
    )
