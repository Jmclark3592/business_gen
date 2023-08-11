# this will make it so only the results with emails will make it to SQS


def save_to_sqs(data, queue_url):
    sqs = boto3.client("sqs", region_name="us-east-2")  # might be east-1
    for item in data:
        website = item.get("Website", "")
        email = extract_email_from_website(website)
        web_content = extract_website_content(website)

        if email and web_content:  # Check if both email and web_content are present
            business_data = BusinessData(
                business_name=item["Name"],
                url=website,
                email=email,
                web_content=web_content,
            )

            try:
                response = sqs.send_message(
                    QueueUrl=queue_url, MessageBody=json.dumps(business_data.dict())
                )
                print(f"Message sent with ID: {response['MessageId']}")
            except Exception as e:
                print(f"Error sending message to SQS: {e}")
