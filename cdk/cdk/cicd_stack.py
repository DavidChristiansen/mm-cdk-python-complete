from aws_cdk import (
    aws_codebuild,
    aws_codecommit,
    aws_codepipeline,
    aws_codepipeline_actions,
    aws_ecr,
    aws_ecs,
    aws_iam,
    core,
)


class CiCdStackProps(core.StackProps):
    ecr_repository: aws_ecr.Repository = None
    ecs_service: aws_ecs.FargateService = None


class CiCdStack(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, props: CiCdStackProps, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        backend_repository = aws_codecommit.Repository(
            self,
            "BackendRespository",
            repository_name="MythicalMysfits-BackendRepository",
        )

        codebuild_project = aws_codebuild.PipelineProject(
            self,
            "BuildProject",
            project_name="MythicalMysfitsServiceCodeBuildProject",
            environment=aws_codebuild.BuildEnvironment(
                compute_type=aws_codebuild.ComputeType.SMALL,
                build_image=aws_codebuild.LinuxBuildImage.UBUNTU_14_04_PYTHON_3_5_2,
                privileged=True,
                environment_variables={
                    "AWS_ACCOUNT_ID": aws_codebuild.BuildEnvironmentVariable(
                        type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value=core.Aws.ACCOUNT_ID,
                    ),
                    "AWS_DEFAULT_REGION": aws_codebuild.BuildEnvironmentVariable(
                        type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value=core.Aws.REGION,
                    ),
                },
            ),
        )

        codebuild_policy = aws_iam.PolicyStatement()
        codebuild_policy.add_resources(backend_repository.repository_arn)
        codebuild_policy.add_actions(
            "codecommit:ListBranches",
            "codecommit:ListRepositories",
            "codecommit:BatchGetRepositories",
            "codecommit:GitPull",
        )
        codebuild_project.add_to_role_policy(codebuild_policy)

        props.ecr_repository.grant_pull_push(codebuild_project.grant_principal)

        source_output = aws_codepipeline.Artifact()
        source_action = aws_codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit-Source",
            branch="master",
            trigger=aws_codepipeline_actions.CodeCommitTrigger.POLL,
            repository=backend_repository,
            output=source_output,
        )

        build_output = aws_codepipeline.Artifact()
        build_action = aws_codepipeline_actions.CodeBuildAction(
            action_name="Build",
            input=source_output,
            outputs=[build_output],
            project=codebuild_project,
        )

        deploy_action = aws_codepipeline_actions.EcsDeployAction(
            action_name="DeployAction", service=props.ecs_service, input=build_output
        )

        pipeline = aws_codepipeline.Pipeline(
            self, "Pipeline", pipeline_name="MythicalMysfitsPipeline"
        )
        pipeline.add_stage(stage_name="Source", actions=[source_action])
        pipeline.add_stage(stage_name="Build", actions=[build_action])
        pipeline.add_stage(stage_name="Deploy", actions=[deploy_action])

        core.CfnOutput(
            self,
            "BackendRepositoryCloneUrlHttp",
            description="Backend Repository CloneUrl HTTP",
            value=backend_repository.repository_clone_url_http,
        )
        core.CfnOutput(
            self,
            "BackendRepositoryCloneUrlSsh",
            description="Backend Repository CloneUrl SSH",
            value=backend_repository.repository_clone_url_ssh,
        )
