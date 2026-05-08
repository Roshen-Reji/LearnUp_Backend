"""
Standardized Pagination
========================
Consistent pagination across all list endpoints.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class LargePagination(PageNumberPagination):
    """For endpoints that return larger datasets (leaderboard, questions)."""
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class SmallPagination(PageNumberPagination):
    """For chat messages, notifications, etc."""
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 50
