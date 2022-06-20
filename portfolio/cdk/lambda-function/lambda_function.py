import os

from datasette.app import Datasette
from mangum import Mangum
import boto3


# Set client ID and secret environment variables from SSM parameters.
ssm = boto3.client("ssm")
os.environ["GITHUB_CLIENT_ID"] = ssm.get_parameter(Name="/portfolio/github-client-id")[
    "Parameter"
]["Value"]
os.environ["GITHUB_CLIENT_SECRET"] = ssm.get_parameter(
    Name="/portfolio/github-client-secret", WithDecryption=True
)["Parameter"]["Value"]

# Use Mangum to serve Datasette application.
handler = Mangum(
    Datasette(
        files=["portfolio.db"],
        metadata={
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
        },
    ).app()
)
