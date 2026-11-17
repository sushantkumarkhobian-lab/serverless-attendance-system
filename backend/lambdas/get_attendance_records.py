
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

TABLE_NAME = "AttendanceTable"
GSI_NAME = "StatusDateIndex"

table = dynamodb.Table(TABLE_NAME)


# ==========================================
# QUERY PAGINATION
# ==========================================

def query_all_pages(query_kwargs):

    items = []

    while True:

        response = table.query(**query_kwargs)

        items.extend(response.get('Items', []))

        if 'LastEvaluatedKey' not in response:
            break

        query_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

    return {
        "Items": items,
        "Count": len(items)
    }


# ==========================================
# SCAN PAGINATION
# ==========================================

def scan_all_pages(scan_kwargs):

    items = []

    while True:

        response = table.scan(**scan_kwargs)

        items.extend(response.get('Items', []))

        if 'LastEvaluatedKey' not in response:
            break

        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

    return {
        "Items": items,
        "Count": len(items)
    }


# ==========================================
# LAMBDA HANDLER
# ==========================================

def lambda_handler(event, context):

    # Parse query string parameters passed from API Gateway

    query_params = event.get('queryStringParameters') or {}

    employee_id = query_params.get('employee_id')
    status = query_params.get('status')
    date = query_params.get('date')


    # CORS headers for local frontend development

    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization"
    }


    try:

        # ==========================================
        # 1. FILTER BY STATUS
        # ==========================================

        if status:

            # Querying via GSI: StatusDateIndex

            query_kwargs = {
                'IndexName': GSI_NAME,
                'KeyConditionExpression': Key('status').eq(status)
            }

            if date:

                query_kwargs['KeyConditionExpression'] = (
                    Key('status').eq(status) &
                    Key('date').eq(date)
                )

            response = query_all_pages(query_kwargs)


        # ==========================================
        # 2. FILTER BY EMPLOYEE ID
        # ==========================================

        elif employee_id:

            # Querying via Main Table

            query_kwargs = {
                'KeyConditionExpression': Key('employee_id').eq(employee_id)
            }

            if date:

                query_kwargs['KeyConditionExpression'] = (
                    Key('employee_id').eq(employee_id) &
                    Key('date').eq(date)
                )

            response = query_all_pages(query_kwargs)


        # ==========================================
        # 3. FILTER BY DATE ONLY
        # ==========================================

        elif date:

            # Scan all attendance records for the selected date

            response = scan_all_pages({
                'FilterExpression': Attr('date').eq(date)
            })


        # ==========================================
        # 4. NO FILTER PROVIDED
        # ==========================================

        else:

            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "error": "Provide employee_id, status, or date."
                })
            }


        # ==========================================
        # SUCCESS RESPONSE
        # ==========================================

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "count": response.get('Count', 0),
                "items": response.get('Items', [])
            }, default=str)
        }


    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except Exception as e:

        print(f"Error querying attendance records: {str(e)}")

        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "error": "Internal Server Error",
                "details": str(e)
            })
        }
