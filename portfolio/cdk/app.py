"""Portfolio AWS CDK app."""
from pathlib import Path
import shutil
import subprocess


import aws_cdk as cdk
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_logs as logs
import aws_cdk.aws_ssm as ssm


# Path to directory containing Lambda function bundle.
dist_path = Path(__file__).parent / "dist"


class App(cdk.App):
    def __init__(self) -> None:
        super().__init__()

        PortfolioStack(
            self,
            "Portfolio",
            github_client_id_parameter_name="/portfolio/github-client-id",
            github_client_secret_parameter_name="/portfolio/github-client-secret",
            datasette_secret_parameter_name="/portfolio/datasette-secret",
        )


class PortfolioStack(cdk.Stack):
    def __init__(
        self,
        scope,
        id: str,
        github_client_id_parameter_name: str,
        github_client_secret_parameter_name: str,
        datasette_secret_parameter_name: str,
    ):
        super().__init__(scope, id, description="Portfolio stack")

        # Create a Lambda function with code from the bundle directory.
        function = lambda_.Function(
            self,
            "Function",
            code=lambda_.Code.from_asset(str(dist_path / "bundle")),
            handler="lambda_function.handler",
            environment={
                "GITHUB_CLIENT_ID_PARAMETER_NAME": github_client_id_parameter_name,
                "GITHUB_CLIENT_SECRET_PARAMETER_NAME": github_client_secret_parameter_name,
                "DATASETTE_SECRET_PARAMETER_NAME": datasette_secret_parameter_name,
            },
            runtime=lambda_.Runtime.PYTHON_3_9,
            log_retention=logs.RetentionDays.ONE_MONTH,
            memory_size=256,
            timeout=cdk.Duration.seconds(10),
            retry_attempts=0,
        )

        # Create a function URL.
        cdk.CfnOutput(
            self,
            "FunctionUrl",
            value=function.add_function_url(
                auth_type=lambda_.FunctionUrlAuthType.NONE
            ).url,
        )

        # Grant Lambda function execution role permission to read parameters.
        for id, parameter_name in (
            ("ClientId", github_client_id_parameter_name),
            ("ClientSecret", github_client_secret_parameter_name),
            ("DatasetteSecret", datasette_secret_parameter_name),
        ):
            ssm.StringParameter.from_secure_string_parameter_attributes(
                self, id, parameter_name=parameter_name
            ).grant_read(function)


def bundle_lambda_function():
    """Bundles Lambda function dependencies.

    The version of SQLite included with the Lambda runtime is old. As a workaround,
    we install pysqlite-binary. This package contains a more recent statically linked
    version of SQLite. Datasette checks for its presence and falls back to sqlite3
    if not available.

    To create a bundle of dependencies targeting the x86 Lambda function architecture,
    we take the following steps:

    - Build the Lambda function as a wheel (including database files, etc. as
      necessary).
    - Export requirements.txt from poetry.lock file.
    - Install the wheel and dependencies to a directory.

    Files are bundled in directory dist/bundle, relative to this module.
    """
    # Delete dist directory, relative to this module.
    shutil.rmtree(dist_path, ignore_errors=True)

    # Build the Lambda function as a Python wheel. We run the command from this
    # modules's directory so that Poetry picks up the correct pyproject.toml file.
    subprocess.run("poetry build --format wheel".split(), cwd=dist_path.parent)

    # Export pinned dependency versions to requirements.txt.
    subprocess.run(
        [
            "poetry",
            "export",
            "--without-hashes",
            "--output",
            dist_path / "requirements.txt",
        ],
        cwd=dist_path,
    )

    # Install Lambda function and dependencies to dist/bundle directory.
    subprocess.run(
        [
            "pip",
            "install",
            "lambda_function-0.1.0-py3-none-any.whl",
            "-r",
            "requirements.txt",
            "--target",
            "bundle",
        ],
        cwd=dist_path,
    )


if __name__ == "__main__":
    App().synth()
