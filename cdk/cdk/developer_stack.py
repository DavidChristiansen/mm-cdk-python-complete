from aws_cdk import aws_codecommit as codecommit, core


class DeveloperStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        cdkRepository = codecommit.Repository(
            self,
            "CDKRepository",
            repository_name="MythicalMysfitsService-Repository-CDK",
        )
        webRepository = codecommit.Repository(
            self,
            "WebRepository",
            repository_name="MythicalMysfitsService-Repository-Web",
        )
        apiRepository = codecommit.Repository(
            self,
            "APIRepository",
            repository_name="MythicalMysfitsService-Repository-API",
        )
        lambdaRepository = codecommit.Repository(
            self,
            "LambdaRepository",
            repository_name="MythicalMysfitsService-Repository-Lambda",
        )

        core.CfnOutput(
            self,
            "CDKRepositoryCloneUrlHttp",
            description="CDK Repository CloneUrl HTTP",
            value=cdkRepository.repository_clone_url_http,
        )
        core.CfnOutput(
            self,
            "CDKRepositoryCloneUrlSsh",
            description="CDK Repository CloneUrl SSH",
            value=cdkRepository.repository_clone_url_ssh,
        )

        core.CfnOutput(
            self,
            "WebRepositoryCloneUrlHttp",
            description="Web Repository CloneUrl HTTP",
            value=webRepository.repository_clone_url_http,
        )
        core.CfnOutput(
            self,
            "WebRepositoryCloneUrlSsh",
            description="Web Repository CloneUrl SSH",
            value=webRepository.repository_clone_url_http,
        )

        core.CfnOutput(
            self,
            "APIRepositoryCloneUrlHttp",
            description="API Repository CloneUrl HTTP",
            value=apiRepository.repository_clone_url_http,
        )
        core.CfnOutput(
            self,
            "APIRepositoryCloneUrlSsh",
            description="API Repository CloneUrl SSH",
            value=apiRepository.repository_clone_url_ssh,
        )

        core.CfnOutput(
            self,
            "LambdaRepositoryCloneUrlHttp",
            description="Lambda Repository CloneUrl HTTP",
            value=lambdaRepository.repository_clone_url_ssh,
        )
        core.CfnOutput(
            self,
            "LambdaRepositoryCloneUrlSsh",
            description="Lambda Repository CloneUrl SSH",
            value=lambdaRepository.repository_clone_url_ssh,
        )
