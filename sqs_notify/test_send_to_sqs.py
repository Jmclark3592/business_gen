import pytest
import json
from unittest.mock import Mock
from sqs_notify.send_to_sqs import send_to_sqs
from model.business import Business


def test_send_to_sqs(mocker):
    # Mock the SQS send_message method
    mock_response = {"MessageId": "test_id"}
    mock_sqs = mocker.Mock()
    mock_sqs.send_message.return_value = mock_response
    mocker.patch(
        "boto3.client", return_value=mock_sqs
    )

    # Create test business data and send to SQS
    business = Business(name="Test Business 1", website="https://example1.com", email="test@example1.com")
    queue_url = "https://sqs.us-east-2.amazonaws.com/123456789012/test_queue"

    send_to_sqs(business, queue_url)

    # Verify that SQS send_message was called for the business
    mock_sqs.send_message.assert_called_with(
        QueueUrl=queue_url, MessageBody=json.dumps(business.to_sqs())
    )  # Last call check

