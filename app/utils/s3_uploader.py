import boto3
import os
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

async def upload_to_s3(file_bytes: bytes, filename: str, content_type: str) -> str:
    bucket_name = os.getenv("AWS_BUCKET_NAME")

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type,
        )
        return f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{filename}"
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))