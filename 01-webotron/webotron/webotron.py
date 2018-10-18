# !/user/bin/Python
# -*- coding: utf-8 -*-
""" Deploy Website with AWS.
Weboton automates the process of deploying websites to AWS S3
-- Configure S3 buckets
    -- Set buckets up for website hosting
    -- upload and syn contents
    -- setup static hosting
-- Configure a contant delivery network
"""
import boto3
import click
from bucket import BucketManager

session = None
bucket_manager = None


@click.group()
@click.option('--profile', default=None,
help="Use a given aws profile")
def cli(profile):
    """webotron deploys websites to aws."""
    global session, bucket_manager
    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile

    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)


@cli.command('list-buckets')
def list_buckets():
    "List all s3 buckets"
    for bucket in bucket_manager.all_buckets():
        print(bucket)



@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """This creates a new bucket and sets-up a basic website."""

    s3_bucket = bucket_manager.init_bucket(bucket)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website(s3_bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List all objects in a bucket."""
    for obj in bucket_manager.all_objects(bucket):
        print(obj)



@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to Bucket."""
    bucket_manager.sync(pathname, bucket)
    print(bucket_manager.get_bucket_url(bucket_manager.s3.Bucket(bucket)))

if __name__ == '__main__':
    cli()
