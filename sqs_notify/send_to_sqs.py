import boto3
from model.business import Business


def send_to_sqs(bus: Business, queue_url: str):
    sqs = boto3.client("sqs", region_name="us-east-2")
    try:
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=bus.model_dump())
        print(f"Message sent with ID: {response['MessageId']}")
    except Exception as e:
        print(f"Error sending message to SQS: {e}")
