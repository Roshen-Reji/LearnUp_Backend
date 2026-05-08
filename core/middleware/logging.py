"""
Request Logging Middleware
============================
Audit log for every API request — who, what, when, how long.
Critical for security monitoring and debugging.
"""

import time
import logging

logger = logging.getLogger("core.audit")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Skip static/media files and health checks from logging
        path = request.path
        if path.startswith(("/static/", "/media/", "/api/health/")):
            return response

        # Extract user info
        user_id = "anonymous"
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.pk)

        # Log the request
        log_data = {
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "user": user_id,
            "ip": _get_client_ip(request),
            "duration_ms": round(duration_ms, 2),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:100],
        }

        if response.status_code >= 500:
            logger.error(f"[{log_data['status']}] {log_data['method']} {log_data['path']} "
                         f"user={log_data['user']} ip={log_data['ip']} "
                         f"duration={log_data['duration_ms']}ms")
        elif response.status_code >= 400:
            logger.warning(f"[{log_data['status']}] {log_data['method']} {log_data['path']} "
                           f"user={log_data['user']} ip={log_data['ip']} "
                           f"duration={log_data['duration_ms']}ms")
        else:
            logger.info(f"[{log_data['status']}] {log_data['method']} {log_data['path']} "
                        f"user={log_data['user']} ip={log_data['ip']} "
                        f"duration={log_data['duration_ms']}ms")

        return response


def _get_client_ip(request):
    """Get the real client IP, handling reverse proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
