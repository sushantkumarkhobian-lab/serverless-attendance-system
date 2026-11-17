
import json
import boto3
import uuid
from datetime import datetime, timezone

# Initialize S3 client
s3 = boto3.client("s3")

# Configuration
BUCKET_NAME = "attendance-system-backend-storage-12345"
UPLOAD_PREFIX = "incoming-captures/"
URL_EXPIRATION = 300


def lambda_handler(event, context):

    try:
        # Read request body
        body = event.get("body", {})

        if isinstance(body, str):
            body = json.loads(body) if body else {}

        # Get image content type
        content_type = body.get(
            "contentType",
            "image/jpeg"
        )

        # Validate image format
        if content_type not in [
            "image/jpeg",
            "image/png"
        ]:
            return build_response(
                400,
                {
                    "message": "Only JPEG and PNG images are allowed"
                }
            )

        # Generate unique filename
        timestamp = datetime.now(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ")

        extension = (
            "jpg" if content_type == "image/jpeg"
            else "png"
        )

        filename = (
            f"{timestamp}_{uuid.uuid4().hex}.{extension}"
        )

        # Generate S3 object key
        s3_key = f"{UPLOAD_PREFIX}{filename}"

        # Generate pre-signed URL
        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ContentType": content_type
            },
            ExpiresIn=URL_EXPIRATION
        )

        # Return response
        return build_response(
            200,
            {
                "message": "Pre-signed URL generated successfully",
                "uploadUrl": upload_url,
                "s3Key": s3_key,
                "expiresIn": URL_EXPIRATION,
                "contentType": content_type
            }
        )

    except Exception as e:

        print("ERROR:", str(e))

        return build_response(
            500,
            {
                "message": "Failed to generate upload URL",
                "error": str(e)
            }
        )


def build_response(status_code, body):

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST,OPTIONS"
        },
        "body": json.dumps(body)
    }
