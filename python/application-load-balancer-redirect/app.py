#!/usr/bin/env python3
import base64
from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    core,
)


class LoadBalancerRedirectionStack(core.Stack):
    def __init__(self, app: core.App, id: str) -> None:
        super().__init__(app, id)

        vpc = ec2.Vpc(self, "VPC")

        data = open("./httpd.sh", "rb").read()
        httpd=ec2.UserData.for_linux()
        httpd.add_commands(str(data,'utf-8'))


        asg = autoscaling.AutoScalingGroup(
            self,
            "ASG",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            user_data=httpd,
        )

        lb = elbv2.ApplicationLoadBalancer(
            self, "LB",
            vpc=vpc,
            internet_facing=True)

        listener = lb.add_listener("Listener", port=80)
        listener.add_targets("Target", port=80, targets=[asg])
        listener.add_action('Action', action=elbv2.ListenerAction.redirect(
            port='443',
            protocol=elbv2.ApplicationProtocol.HTTPS.value,
            permanent=True
        ))

        listener.connections.allow_default_port_from_any_ipv4("Open to the world")

        asg.scale_on_request_count("AModestLoad", target_requests_per_second=1)
        core.CfnOutput(self,"LoadBalancerRedirection",export_name="LoadBalancerRedirection",value=lb.load_balancer_dns_name)


app = core.App()
LoadBalancerRedirectionStack(app, "LoadBalancerRedirectionStack")
app.synth()
