"""Portfolio AWS CDK app."""
from pathlib import Path


import aws_cdk as cdk
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_logs as logs
import aws_cdk.aws_ssm as ssm
import aws_cdk.aws_lambda_python_alpha as python


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

        # Package the Lambda function defined in subdirectory function.
        python_function = python.PythonFunction(
            self,
            "PythonFunction",
            entry=str(Path(__file__).parent / "function"),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler",
            index="index.py",
            environment={
                "GITHUB_CLIENT_ID_PARAMETER_NAME": github_client_id_parameter_name,
                "GITHUB_CLIENT_SECRET_PARAMETER_NAME": github_client_secret_parameter_name,
                "DATASETTE_SECRET_PARAMETER_NAME": datasette_secret_parameter_name,
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
            memory_size=256,
            timeout=cdk.Duration.seconds(10),
            retry_attempts=0,
        )

        # Create a function URL.
        cdk.CfnOutput(
            self,
            "FunctionUrl",
            value=python_function.add_function_url(
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
            ).grant_read(python_function)


if __name__ == "__main__":
    App().synth()
