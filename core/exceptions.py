"""
Centralized Exception Handling
================================
Uniform error response format across the entire API.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

logger = logging.getLogger("core")


def custom_exception_handler(exc, context):
    """
    Wraps default DRF handler to ensure consistent error response shape:
    {
        "success": false,
        "error": {
            "code": "validation_error",
            "message": "Human readable message",
            "details": { ... }
        }
    }
    """
    # Let DRF handle it first
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "error": {
                "code": _get_error_code(response.status_code),
                "message": _extract_message(response.data),
                "details": response.data if isinstance(response.data, dict) else {"detail": response.data},
            },
        }
        response.data = error_data
        return response

    # Handle Django-native exceptions that DRF doesn't catch
    if isinstance(exc, DjangoValidationError):
        error_data = {
            "success": False,
            "error": {
                "code": "validation_error",
                "message": str(exc.message) if hasattr(exc, "message") else str(exc),
                "details": exc.message_dict if hasattr(exc, "message_dict") else {},
            },
        }
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

    # Log unexpected exceptions
    logger.exception(f"Unhandled exception in {context.get('view', 'unknown')}: {exc}")

    error_data = {
        "success": False,
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {},
        },
    }
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_error_code(status_code):
    codes = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        406: "not_acceptable",
        409: "conflict",
        429: "too_many_requests",
        500: "internal_server_error",
    }
    return codes.get(status_code, "error")


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        # Take the first field error
        for key, value in data.items():
            if isinstance(value, list):
                return f"{key}: {value[0]}"
            return f"{key}: {value}"
    if isinstance(data, list):
        return str(data[0])
    return str(data)
