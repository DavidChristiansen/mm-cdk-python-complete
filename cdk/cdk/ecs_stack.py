from aws_cdk import aws_ec2, aws_ecr, aws_ecs, aws_ecs_patterns, aws_iam, core


class EcsStackProps(core.StackProps):
    vpc: aws_ec2.Vpc = None
    ecr_repository: aws_ecr.Repository = None


class EcsStack(core.Stack):
    @property
    def ecs_cluster(self) -> aws_ecs.Cluster:
        return self._ecs_cluster

    @property
    def ecs_service(self) -> aws_ecs_patterns.NetworkLoadBalancedFargateService:
        return self._ecs_service

    def __init__(
        self, scope: core.Construct, id: str, props: EcsStackProps, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self._ecs_service = None

        self._ecs_cluster = aws_ecs.Cluster(
            self, "Cluster", cluster_name="MythicalMysfits-Cluster", vpc=props.vpc
        )
        self._ecs_cluster.connections.allow_from_any_ipv4(aws_ec2.Port.tcp(8080))

        task_image_options = aws_ecs_patterns.NetworkLoadBalancedTaskImageOptions(
            container_port=8080,
            image=aws_ecs.ContainerImage.from_ecr_repository(props.ecr_repository),
        )
        self._ecs_service = aws_ecs_patterns.NetworkLoadBalancedFargateService(
            self,
            "Service",
            cluster=self._ecs_cluster,
            task_image_options=task_image_options,
        )
        self._ecs_service.service.connections.allow_from(
            aws_ec2.Peer.ipv4(props.vpc.vpc_cidr_block), aws_ec2.Port.tcp(8080)
        )

        task_definition_policy = aws_iam.PolicyStatement()
        task_definition_policy.add_actions(
            # Rules which allow ECS to attach network interfaces to instances
            # on your behalf in order for awsvpc networking mode to work right
            "ec2:AttachNetworkInterface",
            "ec2:CreateNetworkInterface",
            "ec2:CreateNetworkInterfacePermission",
            "ec2:DeleteNetworkInterface",
            "ec2:DeleteNetworkInterfacePermission",
            "ec2:Describe*",
            "ec2:DetachNetworkInterface",
            # Rules which allow ECS to update load balancers on your behalf
            #  with the information sabout how to send traffic to your containers
            "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
            "elasticloadbalancing:DeregisterTargets",
            "elasticloadbalancing:Describe*",
            "elasticloadbalancing:RegisterInstancesWithLoadBalancer",
            "elasticloadbalancing:RegisterTargets",
            # Rules which allow ECS to run tasks that have IAM roles assigned to them.
            "iam:PassRole",
            # Rules that let ECS create and push logs to CloudWatch.
            "logs:DescribeLogStreams",
            "logs:CreateLogGroup",
        )
        task_definition_policy.add_all_resources()
        self._ecs_service.service.task_definition.add_to_execution_role_policy(
            task_definition_policy
        )

        task_role_policy = aws_iam.PolicyStatement()
        task_role_policy.add_actions(
            # Allow the ECS Tasks to download images from ECR
            "ecr:GetAuthorizationToken",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            # Allow the ECS tasks to upload logs to CloudWatch
            "logs:CreateLogStream",
            "logs:CreateLogGroup",
            "logs:PutLogEvents",
        )
        task_role_policy.add_all_resources()
        self._ecs_service.service.task_definition.add_to_task_role_policy(
            task_definition_policy
        )

