"""Amazon S3 storage (boto3). Encryption with SSE-KMS; malware status read from GuardDuty's object tag."""

from __future__ import annotations

from typing import Any, BinaryIO, cast

import boto3
from botocore.exceptions import ClientError

from app.storage.base import validate_key

GUARDDUTY_TAG = "GuardDutyMalwareScanStatus"


class S3FileStorage:
    def __init__(self, bucket: str, region: str, kms_key_id: str = "", client: Any | None = None) -> None:
        self._bucket = bucket
        self._kms_key_id = kms_key_id
        # Credentials come from the ECS task role in AWS (never from code or .env).
        self._s3 = client or boto3.client("s3", region_name=region)

    def _extra_args(self, content_type: str) -> dict[str, str]:
        args = {"ContentType": content_type}
        if self._kms_key_id:
            args |= {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self._kms_key_id}
        return args

    def put(self, object_key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> None:
        self._s3.upload_fileobj(data, self._bucket, validate_key(object_key), ExtraArgs=self._extra_args(content_type))

    def open(self, object_key: str) -> BinaryIO:
        response = self._s3.get_object(Bucket=self._bucket, Key=validate_key(object_key))
        return cast(BinaryIO, response["Body"])

    def exists(self, object_key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=validate_key(object_key))
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True

    def delete(self, object_key: str) -> None:
        self._s3.delete_object(Bucket=self._bucket, Key=validate_key(object_key))

    def scan_status(self, object_key: str) -> str | None:
        tags = self._s3.get_object_tagging(Bucket=self._bucket, Key=validate_key(object_key)).get("TagSet", [])
        for tag in tags:
            if tag.get("Key") == GUARDDUTY_TAG:
                return str(tag.get("Value"))
        return None
