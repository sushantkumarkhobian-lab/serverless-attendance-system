import json
import os
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Attr

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('TABLE_NAME', 'AttendanceTable')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'attendance-system-backend-storage-12345')

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    print(f"Running EOD Absentee Job for date: {today_str}")

    try:
        # 1. Get all unique registered employee IDs from the table
        scan_response = table.scan(ProjectionExpression="employee_id")
        all_items = scan_response.get('Items', [])
        
        while 'LastEvaluatedKey' in scan_response:
            scan_response = table.scan(
                ProjectionExpression="employee_id",
                ExclusiveStartKey=scan_response['LastEvaluatedKey']
            )
            all_items.extend(scan_response.get('Items', []))

        all_employee_ids = list(set(item['employee_id'] for item in all_items))
        
        if not all_employee_ids:
            print("No employees found in the database.")
            return {"statusCode": 200, "body": "No employees found."}

        # 2. Get today's existing attendance records
        today_response = table.scan(
            FilterExpression=Attr('date').eq(today_str)
        )
        today_records = today_response.get('Items', [])
        
        while 'LastEvaluatedKey' in today_response:
            today_response = table.scan(
                FilterExpression=Attr('date').eq(today_str),
                ExclusiveStartKey=today_response['LastEvaluatedKey']
            )
            today_records.extend(today_response.get('Items', []))

        checked_in_employees = set(record['employee_id'] for record in today_records)

        # 3. Find missing employees who haven't clocked in today
        absent_employees = [emp_id for emp_id in all_employee_ids if emp_id not in checked_in_employees]

        # 4. Auto-insert absent records into DynamoDB
        for emp_id in absent_employees:
            absent_item = {
                'employee_id': emp_id,
                'date': today_str,
                'status': 'absent',
                'clock_in': None,
                'notes': 'Auto-marked absent by EOD Cleanup job'
            }
            table.put_item(Item=absent_item)
            today_records.append(absent_item)
            print(f"Marked employee {emp_id} as absent for {today_str}")

        # 5. Compile daily summary structure
        summary_data = {
            "date": today_str,
            "total_employees": len(all_employee_ids),
            "present_or_late": len(checked_in_employees),
            "total_absent": len(absent_employees),
            "records": today_records
        }

        # 6. Save summary JSON to S3 bucket (summaries/daily-YYYY-MM-DD.json)
        file_key = f"summaries/daily-{today_str}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=json.dumps(summary_data, default=str, indent=2),
            ContentType='application/json'
        )
        print(f"Successfully uploaded daily summary to s3://{BUCKET_NAME}/{file_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "EOD job executed successfully",
                "date": today_str,
                "absent_marked": len(absent_employees)
            })
        }

    except Exception as e:
        print(f"Error executing EOD Absentee Job: {str(e)}")
        raise e