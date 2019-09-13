from aws_cdk import aws_ecr, core


class EcrStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ecr_repository = aws_ecr.Repository(
            self, "Repository", repository_name="mythicalmysfits/service"
        )
