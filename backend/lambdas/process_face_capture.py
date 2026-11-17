
import boto3
import urllib.parse
from datetime import datetime, time
from zoneinfo import ZoneInfo
from botocore.exceptions import ClientError

# AWS configuration
REGION = "us-east-2"
COLLECTION_ID = "employee_faces"
TABLE_NAME = "AttendanceTable"
SIMILARITY_THRESHOLD = 85
TIMEZONE = "Asia/Kolkata"
LATE_CUTOFF = time(9, 0)  # 9:00 AM IST

# AWS clients
rekognition = boto3.client("rekognition", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
attendance_table = dynamodb.Table(TABLE_NAME)


def recognize_employee(bucket, image_key):

    response = rekognition.search_faces_by_image(
        CollectionId=COLLECTION_ID,
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": image_key
            }
        },
        MaxFaces=1,
        FaceMatchThreshold=SIMILARITY_THRESHOLD
    )

    matches = response.get("FaceMatches", [])

    if not matches:
        print("No matching employee found.")
        return None

    best_match = matches[0]

    employee_id = best_match["Face"].get("ExternalImageId")
    similarity = best_match.get("Similarity", 0)

    print("Recognized Employee:", employee_id)
    print("Similarity:", similarity)

    return employee_id


def mark_attendance(employee_id, image_key):

    now = datetime.now(ZoneInfo(TIMEZONE))

    date = now.strftime("%Y-%m-%d")
    timestamp = now.isoformat(timespec="seconds")

    # Determine attendance status using 9:00 AM cutoff
    current_time = now.time().replace(tzinfo=None)

    if current_time <= LATE_CUTOFF:
        attendance_status = "OnTime"
    else:
        attendance_status = "Late"

    # First distinct image: CLOCK IN
    try:

        attendance_table.update_item(
            Key={
                "employee_id": employee_id,
                "date": date
            },
            UpdateExpression=(
                "SET clock_in = :time, "
                "#status = :status, "
                "last_capture_key = :capture"
            ),
            ConditionExpression=(
                "attribute_not_exists(clock_in) AND "
                "(attribute_not_exists(last_capture_key) "
                "OR last_capture_key <> :capture)"
            ),
            ExpressionAttributeNames={
                "#status": "status"
            },
            ExpressionAttributeValues={
                ":time": timestamp,
                ":status": attendance_status,
                ":capture": image_key
            }
        )

        print(
            "CLOCK-IN recorded:",
            employee_id,
            timestamp,
            "Status:",
            attendance_status
        )

        return "clock_in"

    except ClientError as error:

        if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise

    # Second distinct image: CLOCK OUT
    try:

        attendance_table.update_item(
            Key={
                "employee_id": employee_id,
                "date": date
            },
            UpdateExpression=(
                "SET clock_out = :time, "
                "last_capture_key = :capture"
            ),
            ConditionExpression=(
                "attribute_exists(clock_in) AND "
                "attribute_not_exists(clock_out) AND "
                "(attribute_not_exists(last_capture_key) "
                "OR last_capture_key <> :capture)"
            ),
            ExpressionAttributeValues={
                ":time": timestamp,
                ":capture": image_key
            }
        )

        print("CLOCK-OUT recorded:", employee_id, timestamp)

        return "clock_out"

    except ClientError as error:

        if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise

        print(
            "Duplicate capture or attendance already completed:",
            employee_id
        )

        return "ignored"


def lambda_handler(event, context):

    print("Received S3 event:", event)

    for record in event.get("Records", []):

        if record.get("eventSource") != "aws:s3":
            continue

        bucket = record["s3"]["bucket"]["name"]

        image_key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        # Process only incoming webcam captures
        if not image_key.startswith("incoming-captures/"):
            print("Ignoring object:", image_key)
            continue

        print("Processing image:", image_key)

        # Identify employee
        employee_id = recognize_employee(
            bucket,
            image_key
        )

        if not employee_id:
            print("Attendance not recorded: face not recognized.")
            continue

        # Update attendance
        result = mark_attendance(
            employee_id,
            image_key
        )

        print("Attendance result:", result)

    return {
        "statusCode": 200,
        "body": "Face processing completed"
    }
