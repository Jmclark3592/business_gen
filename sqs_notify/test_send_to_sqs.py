import pytest
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
    )  # Update `your_module_name` to the actual module name

    # Create test business data and send to SQS
    business = Business(name="Test Business 1", website="https://example1.com")
    queue_url = "https://sqs.us-east-2.amazonaws.com/123456789012/test_queue"

    send_to_sqs(business, queue_url)

    # Verify that SQS send_message was called for each business
    # assert mock_sqs.send_message.call_count == len(business)
    mock_sqs.send_message.assert_called_with(
        QueueUrl=queue_url, MessageBody=business.model_dump()
    )  # Last call check
