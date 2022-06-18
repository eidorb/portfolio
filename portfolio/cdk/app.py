"""Portfolio AWS CDK app."""
from pathlib import Path
import shutil
import subprocess


import aws_cdk as cdk
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_logs as logs


# Path to directory containing Lambda function bundle.
dist_path = Path(__file__).parent / "lambda-function/dist"


class App(cdk.App):
    def __init__(self) -> None:
        super().__init__()

        PortfolioStack(self, "Portfolio")


class PortfolioStack(cdk.Stack):
    def __init__(self, scope, id):
        super().__init__(scope, id, description="Portfolio stack")

        # Create an Lambda function with code from the bundle directory.
        function = lambda_.Function(
            self,
            "Function",
            code=lambda_.Code.from_asset(str(dist_path / "bundle")),
            handler="lambda_function.handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        # Create a function URL.
        cdk.CfnOutput(
            self,
            "FunctionUrl",
            value=function.add_function_url(
                auth_type=lambda_.FunctionUrlAuthType.NONE
            ).url,
        )


def bundle_lambda_function():
    """Bundles Lambda function dependencies for x86_64 Lambda function.

    This bundles the correct dependencies regardless of whether we're running on
    an M1 Mac or x86 Linux build pipeline.

    Most of the dependencies are pure Python, except for PyYAML and MarkupSafe.

    Additionally, the version of SQLite in the Lambda runtime is old. As a workaround,
    we install pysqlite-binary. This package contain a more recent statically linked
    version of SQLite.

    So... to create a bundle of dependencies targeting the x86 Lambda function
    architecture, we do the following steps:

    - Build the Lambda function as a wheel.
    - Install the wheel (and its dependencies) to a directory.
    - Install PyYAML, MarkupSafe and pysqlite-binary wheels built for the
      manylinux2014_x86_64, replacing any existing packages.

    To be clear, unfortunately we cannot simply specify the manylinux2014_x86_64
    platform when installing the wheel. The reason for this is that not all
    dependencies offer wheels, and you cannot simultaneously specify a platform
    and allow source builds.

    Files are bundled in directory lambda-function/dist, relative to this module.
    """
    # Delete lambda-function/dist directory, relative to this module.
    shutil.rmtree(dist_path, ignore_errors=True)

    # Build the Lambda function as a Python wheel. We run the command from the Lambda
    # function's directory in order for Poetry to see that directory's pyproject.toml
    # file.
    subprocess.run("poetry build --format wheel".split(), cwd=dist_path.parent)

    # Install dependencies to lambda-function/dist/bundle directory.
    subprocess.run(
        [
            "pip",
            "install",
            dist_path / "lambda_function-0.1.0-py3-none-any.whl",
            "--target",
            dist_path / "bundle",
        ]
    )

    # Install PyYAML and MarkupSafe wheels, specifying the manylinux2014_x86_64
    # platform.
    subprocess.run(
        [
            "pip",
            "install",
            "--upgrade",
            "PyYAML",
            "MarkupSafe",
            "pysqlite-binary",
            "--target",
            dist_path / "bundle",
            "--platform",
            "manylinux2014_x86_64",
            "--only-binary=:all:",
        ]
    )


if __name__ == "__main__":
    App().synth()
