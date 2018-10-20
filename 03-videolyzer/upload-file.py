from pathlib import Path
import click
import boto3

@click.option('--profile', default=None)
@click.option('--region', default='eu-west-1')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucketname')
@click.command()
def upload_file(profile, region, pathname, bucketname):
    """ Used to upload files to our S3 Bucket used to test project"""

    session_cfg = {}
    session_cfg['region_name'] = region
    if profile:
        session_cfg['profile_name'] = profile_name

    session = boto3.Session(**session_cfg)
    s3 = session.resource('s3')

    bucket = s3.Bucket(bucketname)
    path = Path(pathname).expanduser().resolve()

    print("uploading file to Bucket:{} in Region {}".format(bucketname, region))
    print("file name is: {}".format(path))

    response = bucket.upload_file(str(path), str(path.name))
    print(response)


if __name__ == '__main__':
    upload_file()
