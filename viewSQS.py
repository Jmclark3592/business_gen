import boto3

sqs = boto3.client("sqs", region_name="us-east-2")
queue_url = "https://sqs.us-east-2.amazonaws.com/251703218564/bus_queue1"

while True:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,  # adjust this number as needed
        VisibilityTimeout=0,  # don't wait to make message invisible
        WaitTimeSeconds=1,  # don't wait for messages
    )

    messages = response.get("Messages")
    if messages:
        for message in messages:
            print(message["Body"])
    else:
        print("No more messages in queue.")
        break
