"""Portfolio AWS CDK app."""
from pathlib import Path

import aws_cdk as cdk
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_lambda_python_alpha as python
import aws_cdk.aws_logs as logs
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as route53_targets
import aws_cdk.aws_ssm as ssm


class App(cdk.App):
    def __init__(self) -> None:
        super().__init__()

        PortfolioCertificateStack(self, "PortfolioCertificate")
        PortfolioStack(
            self,
            "Portfolio",
            github_client_id_parameter_name="/portfolio/github-client-id",
            github_client_secret_parameter_name="/portfolio/github-client-secret",
            datasette_secret_parameter_name="/portfolio/datasette-secret",
        )

        cdk.Tags.of(self).add("project", "portfolio")


class PortfolioCertificateStack(cdk.Stack):
    """The CloudFront distribution custom certificate lives in a separate stack
    because certificates used for CloudFront distributions must be in a specific
    region: us-east-1.

    Domain name, hosted zone and certificate are exposed as attributes. These are
    referenced by the other stack.
    """

    def __init__(self, scope, id: str):

        super().__init__(
            scope,
            id,
            cross_region_references=True,
            description="Portfolio certificate stack",
            env=cdk.Environment(region="us-east-1"),
        )

        # Reference existing hosted zone.
        self.hosted_zone = route53.PublicHostedZone.from_public_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id="Z0932427366G4DNP1CWB",
            zone_name="brodie.id.au",
        )

        self.domain_name = "portfolio.brodie.id.au"

        self.certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=self.domain_name,
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
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
        super().__init__(
            scope,
            id,
            cross_region_references=True,
            description="Portfolio",
            # CloudFront certificates must be in us-east-1; so, for simplicity,
            # put everything in us-east-1.
            env=cdk.Environment(region="us-east-1"),
        )

        # Package the Lambda function defined in subdirectory `./function`.
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

        # Turn the Lambda function into a web server with a function URL 🪄.
        python_function_url = python_function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE
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

        # Reference existing hosted zone.
        hosted_zone = route53.PublicHostedZone.from_public_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id="Z0932427366G4DNP1CWB",
            zone_name="brodie.id.au",
        )

        domain_name = "portfolio.brodie.id.au"

        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Create a CloudFront distribution that serves content from the Lambda
        # function URL origin.
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                # Disable CloudFront caching.
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                # Forward all except host header to origin. Lambda function URLs
                # expect the host header to contain the origin domain, not the
                # CloudFront domain name.
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                origin=origins.HttpOrigin(
                    domain_name=cdk.Fn.parse_domain_name(python_function_url.url)
                ),
            ),
            certificate=certificate,
            domain_names=[domain_name],
        )

        # Create an alias record for the CloudFront distribution.
        route53.ARecord(
            scope=self,
            id="Alias",
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution)
            ),
            zone=hosted_zone,
            record_name=domain_name,
        )


if __name__ == "__main__":
    App().synth()
