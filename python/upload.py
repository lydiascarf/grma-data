import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    bucket_name = os.getenv("BUCKET_NAME")
    if not bucket_name:
        raise RuntimeError("BUCKET_NAME not set in .env file")

    index_path = Path(__file__).resolve().parent.parent / "index.html"
    s3_client = boto3.client("s3")
    s3_client.upload_file(
        str(index_path),
        bucket_name,
        "index.html",
        ExtraArgs={"ContentType": "text/html"},
    )
    print(f"Successfully uploaded {index_path} to s3://{bucket_name}/index.html")


if __name__ == "__main__":
    main()
