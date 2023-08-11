import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variable
load_dotenv()
QUEUE_URL = os.getenv("QUEUE_URL")


def view_messages_from_sqs(queue_url, num_messages=10):
    sqs = boto3.client("sqs", region_name="us-east-2")  # adjust region if needed

    # Fetch messages
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=num_messages,  # can be up to 10
        WaitTimeSeconds=20,  # long polling
        VisibilityTimeout=60,  # time in seconds the message will be hidden from the queue
    )

    messages = response.get("Messages", [])

    for message in messages:
        # Print message content
        print(json.loads(message["Body"]))

        # Optionally delete message after viewing to prevent it from returning to the queue
        # Uncomment the following lines if you want to delete messages after viewing.
        # receipt_handle = message['ReceiptHandle']
        # sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


if __name__ == "__main__":
    view_messages_from_sqs(QUEUE_URL)
