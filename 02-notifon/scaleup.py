import boto3
session = boto3.Session(profile_name='awsautomation')

as_client = boto3.client('autoscaling')
as_client.execute_policy(
    AutoScalingGroupName='autosgroup',
    PolicyName='scale up')
