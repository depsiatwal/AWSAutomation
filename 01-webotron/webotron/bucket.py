# !/user/bin/Python
# -*- coding: utf-8 -*-
import mimetypes
from pathlib import Path
from botocore.exceptions import ClientError
from hashlib import md5
from functools import reduce
import util
import boto3

""" Classes for s3 Buckets. """

class BucketManager:
    """Manage a S3 Bucket"""

    CHUNK_SIZE = 8388608

    def __init__(self, session):
        """Create a BucketManager"""
        self.session = session
        self.s3 = self.session.resource('s3')
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize = self.CHUNK_SIZE,
            multipart_threshold =  self.CHUNK_SIZE
        )
        self.manifest = {}

    def get_bucket_url(self, bucket):
        """Returns the url for a sepecified bucket"""
        return "http://{}.{}".format(bucket.name,
            util.get_endpoint(self.get_region_name(bucket)).host)

    def get_region_name(self, bucket):
        """Get the bucket's region """
        bucket_location = self.s3.meta.client.get_bucket_location(Bucket=bucket.name)

        return bucket_location["LocationConstraint"] or 'us-east-1'

    def all_buckets(self):
        """Get an iterator for all buckets"""
        return self.s3.buckets.all()

    def load_manifest(self, bucket):
        """ From S3 buckets get the ETAG to check if files have changed """
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents',[]):
                self.manifest[obj['Key']] = obj['ETag']


    def all_objects(self, bucket_name):
        """Get an iterator for all objects in a bucket"""
        return self.s3.Bucket(bucket_name).objects.all()


    def init_bucket(self, bucket_name):
        """Create a new bucket or returns the buckets if it exists"""
        s3_bucket = None
        try:
            s3_bucket = self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration=
                {'LocationConstraint': self.session.region_name})
        except ClientError as error:
            if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                raise error
        return s3_bucket


    def set_policy(self, bucket):
        """Make the bucket public for website"""

        policy = """{
          "Version":"2012-10-17",
          "Statement":[{
          "Sid":"PublicReadGetObject",
          "Effect":"Allow",
          "Principal": "*",
          "Action":["s3:GetObject"],
          "Resource":["arn:aws:s3:::%s/*"
              ]
            }
          ]
        }
        """ % bucket.name
        policy = policy.strip()
        pol = bucket.Policy()
        pol.put(Policy=policy)

    @staticmethod
    def hash_data(data):
        """ Generates a has using MD5  """
        hash = md5()
        hash.update(data)

        return hash

    def gen_etag(self, path):
        """  """
        hashes = []

        with open(path, 'rb') as f:
            while True:
                data = f.read(self.CHUNK_SIZE)

                if not data:
                    break

            hashes.append(self.hash_data(data))

        if not hashes:
            return
        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            hash = self.hash_data(reduce(lambda x, y: x + y, (h.digest() for h in hashes)))
            return '"{}-{}"'.format(hash.hexdigest(), len(hashes))


    def upload_file(self, bucket, path, key):
        """ This uploads files to a given bucket. """
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        etag = self.gen_etag(path)
        if self.manifest.get(key,'') == etag:
            print("Skipping etags match. file={}".format(key))
            return
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={'ContentType': content_type},
            Config = self.transfer_config
            )



    def configure_website(self, bucket):
        """ This functions sets the s3 buckets to be a website """
        ws = bucket.Website()
        ws.put(WebsiteConfiguration={'ErrorDocument': {
                    'Key': 'error.html'
                },
                'IndexDocument': {
                    'Suffix': 'index.html'
                }})

    def sync(self, pathname, bucket_name):
        """ This functions is used to sync files to an s3 bucket """
        bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(bucket)
        root = Path(pathname).expanduser().resolve()


        def handle_directory(target):
            for p in target.iterdir():
                if p.is_dir():
                    handle_directory(p)
                if p.is_file():
                    self.upload_file(bucket,str(p),str(p.relative_to(root)))


        handle_directory(root)
