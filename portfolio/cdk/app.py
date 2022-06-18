"""Portfolio AWS CDK app."""
from pathlib import Path

import aws_cdk as cdk
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_logs as logs


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


if __name__ == "__main__":
    App().synth()
