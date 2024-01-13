import json
import os
from pathlib import Path

import boto3
import yaml
from datasette.app import Datasette
from mangum import Mangum


# Load base metadata from file. This is enough to run locally without authentication
# and authorization. Additional production metadata is added below.
metadata = yaml.safe_load((Path(__file__).parent / "metadata.yaml").open())

# Restrict access to me.
metadata["allow"] = {
    "gh_id": "1782750",
}

# Configure GitHub authentication and redirect plugins.
metadata["plugins"].update(
    {
        "datasette-auth-github": {
            # Read secret configuration values from environment variables. This
            # prevents values being exposed on the `/-/metadata` page.
            "client_id": {"$env": "GITHUB_CLIENT_ID"},
            "client_secret": {"$env": "GITHUB_CLIENT_SECRET"},
        },
        "datasette-redirect-forbidden": {
            "redirect_to": "/-/github-auth-start",
        },
    }
)

# Configure SSM client to use region us-east-1. The parameters are in us-east-1,
# but Lambda@Edge functions may execute in any region.
ssm = boto3.client("ssm", region_name="us-east-1")

# Store GitHub client ID and secret in environment variables. These environment
# variables are referenced in Datasette metadata above.
os.environ["GITHUB_CLIENT_ID"] = ssm.get_parameter(Name="/portfolio/github-client-id")[
    "Parameter"
]["Value"]
os.environ["GITHUB_CLIENT_SECRET"] = ssm.get_parameter(
    Name="/portfolio/github-client-secret", WithDecryption=True
)["Parameter"]["Value"]

# Use Mangum to serve Datasette application.
handler = Mangum(
    Datasette(
        # Open database in immutable mode for improved performance.
        immutables=["portfolio.db"],
        # Load precalculated counts from file.
        inspect_data=json.load((Path(__file__).parent / "inspect_data.json").open()),
        metadata=metadata,
        # Import Datasette secret from SSM parameter.
        secret=ssm.get_parameter(
            Name="/portfolio/datasette-secret", WithDecryption=True
        )["Parameter"]["Value"],
    ).app(),
    # Content-Length header is not allowed in Lambda@Edge responses.
    exclude_headers=["Content-Length"],
)
