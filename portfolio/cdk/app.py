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
        PortfolioStack(self, "Portfolio")
        cdk.Tags.of(self).add("project", "portfolio")


class PortfolioStack(cdk.Stack):
    def __init__(
        self,
        scope,
        id: str,
    ):
        super().__init__(
            scope,
            id,
            cross_region_references=True,
            description="Portfolio",
            # CloudFront certificates and Lambda@Edge functions must be defined
            # in us-east-1. So, for simplicity, put everything in us-east-1.
            env=cdk.Environment(region="us-east-1"),
        )

        # Package the Lambda function contained within subdirectory `./function`.
        python_function = python.PythonFunction(
            self,
            "PythonFunction",
            entry=str(Path(__file__).parent / "function"),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler",
            index="index.py",
            log_retention=logs.RetentionDays.ONE_MONTH,
            memory_size=256,
            timeout=cdk.Duration.seconds(10),
            retry_attempts=0,
        )

        # Likewise, package the demo Lambda function.
        demo_python_function = python.PythonFunction(
            self,
            "DemoPythonFunction",
            entry=str(Path(__file__).parent / "demo-function"),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler",
            index="index.py",
            log_retention=logs.RetentionDays.ONE_MONTH,
            retry_attempts=0,
        )

        # Grant Lambda function execution role permission to read parameters.
        for index, parameter_name in enumerate(
            (
                "/portfolio/github-client-id",
                "/portfolio/github-client-secret",
                "/portfolio/datasette-secret",
            )
        ):
            ssm.StringParameter.from_secure_string_parameter_attributes(
                self, f"Parameter{index}", parameter_name=parameter_name
            ).grant_read(python_function)

        # Reference existing hosted zone.
        hosted_zone = route53.PublicHostedZone.from_public_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id="Z0932427366G4DNP1CWB",
            zone_name="brodie.id.au",
        )

        domain_name = "portfolio.brodie.id.au"
        demo_domain_name = "portfolio-demo.brodie.id.au"

        # Create certificates.
        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )
        demo_certificate = acm.Certificate(
            self,
            "DemoCertificate",
            domain_name=demo_domain_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Create a CloudFront distribution that serves content from Lambda@Edge.
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                # Include all query strings and cookies (auth) in cache key; default
                # cache settings otherwise.
                cache_policy=cloudfront.CachePolicy(
                    scope=self,
                    id="CachePolicy",
                    cookie_behavior=cloudfront.CacheCookieBehavior.all(),
                    query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                ),
                edge_lambdas=[
                    cloudfront.EdgeLambda(
                        event_type=cloudfront.LambdaEdgeEventType.ORIGIN_REQUEST,
                        function_version=python_function.current_version,
                        include_body=True,
                    )
                ],
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                # Use a placeholder domain name because origin will never be fetched.
                origin=origins.HttpOrigin(domain_name="example.com"),
            ),
            certificate=certificate,
            domain_names=[domain_name],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
        )

        # Do the same for the demo distribution.
        demo_distribution = cloudfront.Distribution(
            self,
            "DemoDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                # Include all query strings in cache key, but maximal cache otherwise.
                cache_policy=cloudfront.CachePolicy(
                    scope=self,
                    id="DemoCachePolicy",
                    query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                ),
                edge_lambdas=[
                    cloudfront.EdgeLambda(
                        event_type=cloudfront.LambdaEdgeEventType.ORIGIN_REQUEST,
                        function_version=demo_python_function.current_version,
                        include_body=True,
                    )
                ],
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                # Use a placeholder domain name because origin will never be fetched.
                origin=origins.HttpOrigin(domain_name="example.com"),
            ),
            certificate=demo_certificate,
            domain_names=[demo_domain_name],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
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

        # Create an alias record for the demo CloudFront distribution.
        route53.ARecord(
            scope=self,
            id="DemoAlias",
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(demo_distribution)
            ),
            zone=hosted_zone,
            record_name=demo_domain_name,
        )


if __name__ == "__main__":
    App().synth()
