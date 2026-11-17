# Serverless Attendance System

A real-time, contactless attendance management system built using AWS serverless services and facial recognition. The system allows employees to clock in and out through a webcam, automatically records attendance, identifies absent employees, and provides administrators with attendance records and weekly analytics.

## Features

- **Facial Recognition:** Detects faces through a webcam and identifies registered employees using AWS Rekognition.
- **Contactless Attendance:** Employees can clock in and out without physical attendance cards or manual registers.
- **Secure Image Upload:** Uses Amazon S3 pre-signed URLs to upload captured images directly to S3.
- **Automated Attendance Processing:** S3 events trigger AWS Lambda functions to process captured images and update attendance records.
- **Attendance Management:** Stores employee attendance, clock-in time, clock-out time, and status in Amazon DynamoDB.
- **Automatic Absence Detection:** A scheduled Lambda function identifies employees who have not clocked in and marks them absent.
- **Daily Attendance Summary:** Generates daily attendance summaries in JSON format and stores them in Amazon S3.
- **Weekly Analytics Dashboard:** Displays attendance distribution, daily attendance trends, and employee-wise weekly attendance.
- **Admin Dashboard:** Provides attendance records with employee, date, and status filters.

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Face Detection | face-api.js |
| Facial Recognition | AWS Rekognition |
| Backend | Python, AWS Lambda |
| API Management | Amazon API Gateway |
| Object Storage | Amazon S3 |
| Database | Amazon DynamoDB |
| Scheduling | Amazon EventBridge |
| Monitoring | Amazon CloudWatch |
| Cloud Infrastructure | AWS IAM |

## System Architecture

The system follows a serverless architecture using AWS managed services.

### Attendance Workflow

1. The employee opens the Camera Dashboard.
2. The webcam captures an image when a face is detected.
3. The frontend requests a pre-signed URL from API Gateway.
4. The Generate Presigned URL Lambda generates a temporary S3 upload URL.
5. The captured image is uploaded directly to the S3 incoming-captures prefix.
6. The S3 upload event triggers the Process Face Capture Lambda.
7. The Lambda sends the captured image to AWS Rekognition.
8. Rekognition searches the registered employee face collection.
9. If a matching employee is identified, the Lambda updates their attendance record in DynamoDB.
10. The dashboard retrieves attendance information through the attendance API.

### End-of-Day Workflow

1. Amazon EventBridge triggers the Mark Absent Lambda daily at 11:59 PM.
2. The Lambda retrieves registered employee IDs from the AWS Rekognition collection.
3. It retrieves attendance records for the current date from DynamoDB.
4. Employees without a clock-in record are marked absent.
5. A daily attendance summary is generated.
6. The summary is uploaded to Amazon S3 in JSON format.

### Weekly Analytics Workflow

The Analysis page retrieves attendance records through the existing attendance API for the selected week. It aggregates the returned records to display weekly attendance statistics and trends.

## Project Structure

```text
serverless-attendance-system/
│
├── backend/
│   ├── lambdas/
│   │   ├── generate_presigned_url.py
│   │   ├── get_attendance_records.py
│   │   ├── mark_absent.py
│   │   └── process_face_capture.py
│   │
│   └── scripts/
│       └── register_employee.py
│
├── frontend/
│   ├── models/
│   │   ├── tiny_face_detector_model-shard1
│   │   └── tiny_face_detector_model-weights_manifest.json
│   │
│   ├── analysis.html
│   ├── index.html
│   └── records.html
│
├── COST_ESTIMATE.md
├── README.md
└── TECHNICAL_DESIGN.md
```

## AWS Services and Configuration

The project uses the following AWS resources:

| AWS Service | Resource | Purpose |
|---|---|---|
| Amazon S3 | Backend storage bucket | Stores captured images and attendance summaries |
| Amazon S3 | Frontend hosting bucket | Hosts the static frontend |
| AWS Lambda | GeneratePresignedUrlLambda | Generates pre-signed upload URLs |
| AWS Lambda | ProcessFaceCaptureLambda | Processes captured images and records attendance |
| AWS Lambda | GetAttendanceLambda | Retrieves attendance records |
| AWS Lambda | MarkAbsentLambda | Identifies and marks absent employees |
| Amazon Rekognition | employee_faces | Stores registered employee face information |
| Amazon DynamoDB | AttendanceTable | Stores attendance records |
| Amazon API Gateway | AttendanceAdminApi | Exposes backend HTTP endpoints |
| Amazon EventBridge | Scheduled rule | Triggers the end-of-day attendance job |
| Amazon CloudWatch | Lambda logs | Monitors execution and errors |

### DynamoDB Schema

**Table:** `AttendanceTable`

| Attribute | Description |
|---|---|
| employee_id | Employee identifier (Partition Key) |
| date | Attendance date in YYYY-MM-DD format (Sort Key) |
| clock_in | Employee clock-in timestamp |
| clock_out | Employee clock-out timestamp |
| status | OnTime, Late, or absent |

The table also supports a `StatusDateIndex` global secondary index for status-based attendance queries.

### S3 Storage Structure

**Backend bucket:**

```text
attendance-system-backend-storage-12345/
│
├── incoming-captures/
├── employee-photos/
└── summaries/
    └── daily-YYYY-MM-DD.json
```

**Frontend bucket:**

```text
attendance-system-frontend-ui-12345/
│
├── index.html
├── records.html
├── analysis.html
└── models/
```

## API Endpoints

The backend exposes the following API Gateway endpoints.

**Base URL:**

```text
https://o5d5kar5gl.execute-api.us-east-2.amazonaws.com
```

### 1. Generate Pre-signed URL

**Endpoint:**

```http
POST /generate-presigned-url
```

**Request Body:**

```json
{
  "contentType": "image/jpeg"
}
```

Generates a temporary S3 pre-signed PUT URL for uploading a captured image.

### 2. Retrieve Attendance Records

**Endpoint:**

```http
GET /attendance
```

Supported query parameters:

| Parameter | Description |
|---|---|
| employee_id | Filter by employee |
| date | Filter by attendance date |
| status | Filter by attendance status |

Examples:

```http
GET /attendance?employee_id=EMP001
```

```http
GET /attendance?date=2026-11-16
```

```http
GET /attendance?status=Late
```

```http
GET /attendance?employee_id=EMP001&date=2026-11-16
```

## Employee Face Registration

Employees must be registered in the AWS Rekognition face collection before they can be recognized.

The registration utility is available at:

```text
backend/scripts/register_employee.py
```

The script indexes an employee's reference image in the Rekognition collection and associates the face with the employee ID using `ExternalImageId`.

Example:

```bash
python3 register_employee.py EMP001 employee-photos/EMP001.jpeg
```

The employee ID is subsequently used to associate recognition results with attendance records.

## Deployment and Setup

### Prerequisites

- AWS account
- AWS CLI or AWS Management Console
- Python 3.12 for Lambda functions
- Amazon S3 buckets
- Amazon Rekognition face collection
- Amazon DynamoDB table
- Amazon API Gateway
- Amazon EventBridge
- Appropriate AWS IAM permissions

### Step 1: Configure AWS Resources

Create and configure:

1. Backend S3 bucket.
2. Frontend S3 bucket.
3. Rekognition collection named `employee_faces`.
4. DynamoDB table named `AttendanceTable`.
5. API Gateway HTTP API.
6. Required Lambda functions.
7. IAM execution roles and policies.

### Step 2: Deploy Lambda Functions

Deploy the Python files from:

```text
backend/lambdas/
```

Configure the Lambda functions with the appropriate execution roles and environment variables.

Recommended environment variables:

| Variable | Value |
|---|---|
| TABLE_NAME | AttendanceTable |
| BUCKET_NAME | attendance-system-backend-storage-12345 |
| COLLECTION_ID | employee_faces |

Configure the S3 ObjectCreated event notification to invoke the Process Face Capture Lambda for objects under `incoming-captures/`.

### Step 3: Register Employees

Upload employee reference photographs to:

```text
employee-photos/
```

Run the registration script to index each employee's face in the Rekognition collection.

### Step 4: Configure API Gateway

Configure the following routes:

```text
POST /generate-presigned-url
GET  /attendance
```

Connect each route to its corresponding Lambda function and configure the required CORS settings.

### Step 5: Configure EventBridge

Create a scheduled EventBridge rule to invoke the Mark Absent Lambda every day at 11:59 PM Indian Standard Time.

Ensure the schedule uses the appropriate timezone configuration.

### Step 6: Deploy Frontend

Upload the contents of the `frontend/` directory to the frontend S3 bucket.

Ensure the HTML files and `models/` directory retain their relative paths.

Configure the frontend to use the deployed API Gateway endpoint.

The frontend can then be accessed through the S3 website endpoint or a configured CloudFront distribution.

## Testing

The following workflows should be tested:

| Test | Expected Result |
|---|---|
| Employee face registration | Employee face indexed in Rekognition |
| Face detection | Face detected through webcam |
| Pre-signed URL generation | Temporary upload URL returned |
| S3 image upload | Captured image uploaded successfully |
| Face recognition | Registered employee identified |
| First attendance capture | Clock-in recorded |
| Second attendance capture | Clock-out recorded |
| Attendance API | Correct attendance records returned |
| End-of-day execution | Employees without clock-in marked absent |
| Daily summary generation | JSON report uploaded to S3 |
| Weekly analytics | Attendance statistics and trends displayed |

The Mark Absent Lambda also supports manual historical-date testing using a test event:

```json
{
  "test_date": "2026-11-16",
  "dry_run": true
}
```

Setting `dry_run` to `true` allows the Lambda to identify employees who would be marked absent without modifying DynamoDB or uploading the summary to S3.

## Security Considerations

- Use IAM roles with least-privilege permissions.
- Restrict Lambda access to required AWS resources.
- Use pre-signed URLs for controlled S3 uploads.
- Enable encryption at rest for DynamoDB.
- Enable S3 versioning where required.
- Configure an S3 lifecycle policy to delete raw captured images after the required retention period.
- Do not commit AWS credentials, access keys, or other secrets to the repository.

## Project Documentation

Additional documentation is available in:

- **[TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md)** – System architecture, components, and implementation details.
- **[COST_ESTIMATE.md](COST_ESTIMATE.md)** – Estimated AWS costs for the project workload.

## Future Enhancements

- Employee authentication and role-based access control.
- Employee name and department management.
- Improved attendance reporting and export functionality.
- Historical weekly analytics reports stored in S3.
- Email notifications for attendance summaries.
- Enhanced recognition feedback and error handling.

## License

This project is developed for academic and educational purposes.
