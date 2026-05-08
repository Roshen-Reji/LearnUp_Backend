"""
Security Headers Middleware
=============================
Adds enterprise-grade security headers to every response.
"""


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Prevent MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response["X-Frame-Options"] = "DENY"

        # XSS Protection (legacy browsers)
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy — limit information leakage
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — disable unused browser features
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )

        # Content Security Policy for API responses
        response["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        return response
