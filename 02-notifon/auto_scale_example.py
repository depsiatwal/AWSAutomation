# coding: utf-8
import boto3
session = boto3.Session(profile_name='awsautomation')

client = boto3.client('autoscaling')
client.describe_auto_scaling_groups()
client.describe_policies()
client.client.execute_policy(
    AutoScalingGroupName='autosgroup',
    PolicyName='scale up')
client.execute_policy(
    AutoScalingGroupName='autosgroup',
    PolicyName='scale down')
