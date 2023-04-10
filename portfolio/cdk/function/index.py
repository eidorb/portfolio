import json
import os
from pathlib import Path

import boto3
from datasette.app import Datasette
from mangum import Mangum


# Load base metadata from file. This is enough to run locally without authentication
# and authorization. Additional production metadata is added below.
metadata = json.load((Path(__file__).parent / "metadata.json").open())

# Restrict access to me.
metadata["allow"] = {
    "gh_id": "1782750",
}

# Configure GitHub authentication and redirect.
metadata["plugins"].update(
    {
        "datasette-auth-github": {
            "client_id": {"$env": "GITHUB_CLIENT_ID"},
            "client_secret": {"$env": "GITHUB_CLIENT_SECRET"},
        },
        "datasette-redirect-forbidden": {
            "redirect_to": "/-/github-auth-start",
        },
    }
)

# Get client ID, secret and Datasette secret from SSM parameters.
ssm = boto3.client("ssm")
os.environ["GITHUB_CLIENT_ID"] = ssm.get_parameter(Name="/portfolio/github-client-id")[
    "Parameter"
]["Value"]
os.environ["GITHUB_CLIENT_SECRET"] = ssm.get_parameter(
    Name="/portfolio/github-client-secret", WithDecryption=True
)["Parameter"]["Value"]
secret = (
    ssm.get_parameter(Name="/portfolio/datasette-secret", WithDecryption=True)[
        "Parameter"
    ]["Value"],
)

# Use Mangum to serve Datasette application.
handler = Mangum(
    Datasette(
        files=["portfolio.db"],
        metadata=metadata,
        secret=secret,
    ).app()
)
