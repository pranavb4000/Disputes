"""S3 storage against moto's in-memory S3 (no AWS account needed)."""

from __future__ import annotations

import io

import boto3
from moto import mock_aws

from app.storage.s3 import GUARDDUTY_TAG, S3FileStorage


@mock_aws
def test_s3_round_trip_and_scan_tag() -> None:
    client = boto3.client("s3", region_name="ap-south-1")
    client.create_bucket(Bucket="dms-test", CreateBucketConfiguration={"LocationConstraint": "ap-south-1"})
    storage = S3FileStorage("dms-test", "ap-south-1", client=client)

    storage.put("uploads/a.xlsx", io.BytesIO(b"hello"), "application/octet-stream")
    assert storage.exists("uploads/a.xlsx") and not storage.exists("uploads/missing.xlsx")
    assert storage.open("uploads/a.xlsx").read() == b"hello"
    assert storage.scan_status("uploads/a.xlsx") is None  # GuardDuty has not tagged it yet

    client.put_object_tagging(
        Bucket="dms-test",
        Key="uploads/a.xlsx",
        Tagging={"TagSet": [{"Key": GUARDDUTY_TAG, "Value": "NO_THREATS_FOUND"}]},
    )
    assert storage.scan_status("uploads/a.xlsx") == "NO_THREATS_FOUND"
    storage.delete("uploads/a.xlsx")
    assert not storage.exists("uploads/a.xlsx")
