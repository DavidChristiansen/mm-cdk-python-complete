from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_iam as iam,
    aws_s3_deployment as deployment,
    core,
)
import os


class WebApplicationStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(self, "Bucket", website_index_document="index.html")

        config = {"comment": "mythical-mysfits"}

        origin = cloudfront.CfnCloudFrontOriginAccessIdentity(
            self, "BucketOrigin", cloud_front_origin_access_identity_config=config
        )

        identity = iam.CanonicalUserPrincipal(
            canonical_user_id=origin.attr_s3_canonical_user_id
        )

        bucket.grant_read(identity)

        cloudfront_behaviour = cloudfront.Behavior(
            max_ttl=core.Duration.seconds(60),
            allowed_methods=cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
            is_default_behavior=True
        )
        cloudfront_distribution = cloudfront.CloudFrontWebDistribution(
            self,
            "CloudFront",
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            origin_configs=[
                cloudfront.SourceConfiguration(
                    behaviors=[cloudfront_behaviour],
                    origin_path="/web",
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=bucket, origin_access_identity_id=origin.ref
                    ),
                )
            ],
        )

        contentDir = os.path.realpath("../web/")
        source = deployment.Source.asset(contentDir)
        deployment.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[source],
            destination_key_prefix="web/",
            destination_bucket=bucket,
            distribution=cloudfront_distribution,
            retain_on_delete=False,
        )

        core.CfnOutput(
            self,
            "CloudFrontURL",
            description="The CloudFront distribution URL",
            value="http://{}".format(cloudfront_distribution.domain_name),
        )
