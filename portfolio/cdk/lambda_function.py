import os

from datasette.app import Datasette
from mangum import Mangum
import boto3

from metadata import metadata


# Get client ID, secret and Datasette secret from SSM parameters.
ssm = boto3.client("ssm")
os.environ["GITHUB_CLIENT_ID"] = ssm.get_parameter(
    Name=os.environ["GITHUB_CLIENT_ID_PARAMETER_NAME"]
)["Parameter"]["Value"]
os.environ["GITHUB_CLIENT_SECRET"] = ssm.get_parameter(
    Name=os.environ["GITHUB_CLIENT_SECRET_PARAMETER_NAME"], WithDecryption=True
)["Parameter"]["Value"]
secret = (
    ssm.get_parameter(
        Name=os.environ["DATASETTE_SECRET_PARAMETER_NAME"], WithDecryption=True
    )["Parameter"]["Value"],
)

# Use Mangum to serve Datasette application.
handler = Mangum(
    Datasette(
        files=["portfolio.db"],
        metadata=metadata,
        secret=secret,
    ).app()
)
