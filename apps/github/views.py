import requests
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.accounts.models import User


class GitHubDataView(APIView):
    """GET /api/v1/github/ - Retrieve real GitHub profile data using stored token."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.github_connected or not request.user.github_access_token:
            return Response({"connected": False})

        headers = {
            "Authorization": f"token {request.user.github_access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Fetch Profile
        profile_res = requests.get("https://api.github.com/user", headers=headers)
        if profile_res.status_code != 200:
            return Response({"connected": False, "error": "Invalid token"})
            
        profile_data = profile_res.json()
        
        # Fetch Repos
        repos_res = requests.get("https://api.github.com/user/repos?sort=updated&per_page=5", headers=headers)
        repos_data = repos_res.json() if repos_res.status_code == 200 else []

        # Simplified repos
        formatted_repos = []
        for r in repos_data:
            formatted_repos.append({
                "name": r.get("name"),
                "description": r.get("description"),
                "language": r.get("language"),
                "stars": r.get("stargazers_count"),
                "forks": r.get("forks_count"),
                "url": r.get("html_url"),
                "pushed_at": r.get("pushed_at"),
                "is_private": r.get("private"),
            })

        return Response({
            "connected": True,
            "username": profile_data.get("login"),
            "points": request.user.github_points,
            "profile": {
                "name": profile_data.get("name") or profile_data.get("login"),
                "avatar": profile_data.get("avatar_url"),
                "bio": profile_data.get("bio"),
                "public_repos": profile_data.get("public_repos"),
                "followers": profile_data.get("followers"),
                "following": profile_data.get("following"),
            },
            "repos": formatted_repos,
            "recent_commits": 0
        })


class GitHubAuthView(APIView):
    """GET /api/v1/github/auth/ - Generate GitHub OAuth URL with user state."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client_id = getattr(settings, "GITHUB_CLIENT_ID", "")
        # The callback must point to this Django backend, NOT the frontend
        redirect_uri = getattr(settings, "GITHUB_REDIRECT_URI", "http://localhost:8000/api/v1/github/callback/")
        # Encode user ID in state so the callback can identify the user
        state = str(request.user.id)
        url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=read:user,repo"
            f"&state={state}"
        )
        return Response({"url": url})


class GitHubCallbackView(APIView):
    """GET /api/v1/github/callback/ - Handle GitHub OAuth redirect (unauthenticated)."""
    permission_classes = [AllowAny]
    authentication_classes = []  # No auth needed — user is identified via state param

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")  # This is the user's UUID

        if not code:
            return redirect("http://localhost:3000/github?error=no_code")

        if not state:
            return redirect("http://localhost:3000/github?error=no_state")

        # Look up the user from the state parameter
        try:
            user = User.objects.get(id=state)
        except User.DoesNotExist:
            return redirect("http://localhost:3000/github?error=invalid_user")

        client_id = getattr(settings, "GITHUB_CLIENT_ID", "")
        client_secret = getattr(settings, "GITHUB_CLIENT_SECRET", "")

        # Exchange code for access token
        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": "http://localhost:8000/api/v1/github/callback/",
            },
            headers={"Accept": "application/json"}
        )
        
        if token_res.status_code != 200:
            return redirect("http://localhost:3000/github?error=token_failed")

        token_data = token_res.json()
        access_token = token_data.get("access_token")

        if access_token:
            # Fetch user profile to save username
            user_res = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github.v3+json"}
            )
            if user_res.status_code == 200:
                user_data = user_res.json()
                user.github_username = user_data.get("login")
                
            user.github_connected = True
            user.github_access_token = access_token
            user.save()
            return redirect("http://localhost:3000/github?connected=true")
            
        return redirect("http://localhost:3000/github?error=no_access_token")
