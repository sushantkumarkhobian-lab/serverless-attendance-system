import boto3
from botocore.exceptions import ClientError

REGION = "us-east-2"
BUCKET = "attendance-system-backend-storage-12345"
COLLECTION_ID = "employee_faces"

rekognition = boto3.client("rekognition", region_name=REGION)


def ensure_collection():
    try:
        rekognition.describe_collection(
            CollectionId=COLLECTION_ID
        )
        print("Using existing collection:", COLLECTION_ID)

    except rekognition.exceptions.ResourceNotFoundException:
        rekognition.create_collection(
            CollectionId=COLLECTION_ID
        )
        print("Created collection:", COLLECTION_ID)


def register_employee():
    employee_id = input("\nEnter employee ID: ").strip()
    photo_key = input(
        "Enter S3 photo key (e.g. employee-photos/EMP001.jpg): "
    ).strip()

    if not employee_id or not photo_key:
        print("Employee ID and photo key are required.")
        return

    if not photo_key.startswith("employee-photos/"):
        print("Reference photos must be inside employee-photos/.")
        return

    try:
        # Confirm that the reference photograph exists
        s3 = boto3.client("s3", region_name=REGION)
        s3.head_object(
            Bucket=BUCKET,
            Key=photo_key
        )

        # Register the face
        response = rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image={
                "S3Object": {
                    "Bucket": BUCKET,
                    "Name": photo_key
                }
            },
            ExternalImageId=employee_id,
            MaxFaces=1,
            QualityFilter="AUTO",
            DetectionAttributes=[]
        )

        faces = response.get("FaceRecords", [])

        if faces:
            face = faces[0]["Face"]

            print("\nEMPLOYEE REGISTERED SUCCESSFULLY")
            print("Employee ID:", employee_id)
            print("Face ID:", face["FaceId"])
            print("Confidence:", face["Confidence"])

        else:
            print("\nNo face was registered.")
            print("Check the photograph and try again.")

            for item in response.get("UnindexedFaces", []):
                print("Reason:", item.get("Reasons"))

    except ClientError as error:
        print("\nAWS ERROR:", error.response["Error"]["Message"])

    except Exception as error:
        print("\nERROR:", str(error))


if __name__ == "__main__":
    ensure_collection()

    while True:
        register_employee()

        again = input(
            "\nRegister another employee? (yes/no): "
        ).strip().lower()

        if again not in ["yes", "y"]:
            break

    print("\nFace registration process completed.")
