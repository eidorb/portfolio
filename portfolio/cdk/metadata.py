"""Datasette metadata"""
metadata = {
    # Restrict access to me.
    "allow": {
        "gh_id": "1782750",
    },
    "plugins": {
        "datasette-auth-github": {
            "client_id": {"$env": "GITHUB_CLIENT_ID"},
            "client_secret": {"$env": "GITHUB_CLIENT_SECRET"},
        },
        "datasette-redirect-forbidden": {
            "redirect_to": "/-/github-auth-start",
        },
    },
}
