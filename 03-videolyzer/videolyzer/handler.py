import os
import urllib
import boto3
import json


def get_video_labels(job_id):
    """ Get all the labels once we know they've been compete there's limit of 1000 CHARS """
    """ Therefore this function will loop through the pages """

    rekognition_client = boto3.client('rekognition')
    response = rekognition_client.get_label_detection(JobId=job_id)

    next_token = response.get('NextToken', None)

    while next_token:
        next_page = rekognition_client.get_label_detection(
            JobId=job_id,
            NextToken = next_token
            )
        next_token = next_page.get('NextToken', None)

        response['Labels'].extend(next_page['Labels'])
    return response


def make_item(data):
    """ Since out labels consists of floats dynamodb doesn't like these """
    """ Hense we itterate through each data item (incuding dicts and lists) and convert to str if we encounter a float """
    if isinstance(data, dict):
        return {k: make_item(v) for k, v in data.items()}

    if isinstance(data, list):
        return [ make_item(v) for v in data ]

    if isinstance(data , float):
        return str(data)

    return data

def put_labels_in_db(data, video_name, video_bucket):
    """ Places our labeles into a dynamodb DB """
    del data['ResponseMetadata']
    del data['JobStatus']

    data['videoName'] = video_name
    data['videoBucket'] = video_bucket

    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ['DYANAMODB_TABLE_NAME']
    videos_table = dynamodb.Table(table_name)
    data = make_item(data)
    videos_table.put_item(Item = data)
    return

def start_label_detection(bucket, key):
    """ Local function to start the label detection and send a SNS/Topic to spend to when jobs is completed """
    rekognition_client = boto3.client('rekognition')

    rekognition_sns_arn = os.environ['REKOGNITION_SNS_TOPIC_ARN']
    role_arn = os.environ['REKOGNITION_ROLE_ARN']

    response = rekognition_client.start_label_detection(
        Video={'S3Object': {
            'Bucket': bucket,
            'Name': key
            }
        },
        NotificationChannel={
            'SNSTopicArn': rekognition_sns_arn,
            'RoleArn': role_arn
            })
    print(response)

    return


#Lamda events functions



def start_processing_video(event, context):
    """ This is triggered when we upload a video is S3 we start lable detection  """
    for record in event['Records']:
        start_label_detection(
            record['s3']['bucket']['name'],
            urllib.parse.unquote_plus(
            record['s3']['object']['key']
            )
        )
    return

def handle_label_dectection(event, context):
    """ This is hooked up to our SNS topic when returned with job label detection job completed """
    table_name = os.environ['DYANAMODB_TABLE_NAME']

    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        job_id = message['JobId']
        s3_object = message['Video']['S3ObjectName']
        s3_bucket = message['Video']['S3Bucket']

        response = get_video_labels(job_id)
        put_labels_in_db(response, s3_object, s3_bucket)
    return
