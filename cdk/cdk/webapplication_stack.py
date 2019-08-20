from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_iam as iam,
    aws_s3_deployment as deployment,
    core
)
import os

class WebApplicationStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(
            self,
            "Bucket",
            website_index_document='index.html'
        )

        config = {
            "comment": "mythical-mysfits"
        }

        origin = cloudfront.CfnCloudFrontOriginAccessIdentity(
            self,
            "BucketOrigin",
            cloud_front_origin_access_identity_config=config
        )

        identity = iam.CanonicalUserPrincipal(canonical_user_id=origin.attr_s3_canonical_user_id)
        
        bucket.grant_read(identity)

        contentDir = os.path.realpath("./web")

        deployment.BucketDeployment(
            self,
            "DeployWebsite",
            source=deployment.Source.asset(contentDir),
            destination_key_prefix="web/",
            destination_bucket=bucket,
            retain_on_delete=False,
        )

        cloudfront_distribution = cloudfront.CloudFrontWebDistribution(
            self,
            "CloudFront",
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            origin_configs=[
                {
                    "behaviors": [{
                        "isDefaultBehavior": True, 
                        "max_ttl_seconds": None,
                        "allowedMethods": cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS
                    }],
                    "originPath": "/web",
                    "s3OriginSource": {
                        "s3BucketSource": bucket,
                        "originAccessIdentity": origin.attr_s3_canonical_user_id,
                    },
                }
            ],
        )

        core.CfnOutput(self, "CloudFrontURL", description= "The CloudFront distribution URL" ,value=cloudfront_distribution.domain_name)