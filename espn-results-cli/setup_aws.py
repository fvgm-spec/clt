#!/usr/bin/env python3
"""
One-time AWS setup for espn_results.py.
Creates the DynamoDB cache table and required IAM inline policy.

Usage:
    python3 setup_aws.py [--region us-east-1] [--iam-user YOUR_IAM_USERNAME]
"""
import argparse
import json
import sys
import boto3
from botocore.exceptions import ClientError

POLICY_NAME = "ESPNResultsDynamoDB"
TABLE_NAME  = "espn_cache"
TTL_ATTR    = "expires_at"


def create_table(ddb, region):
    try:
        table = ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "cache_key", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "cache_key", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Creating table '{TABLE_NAME}' in {region} ...")
        table.wait_until_exists()
        print("  Table ready.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table '{TABLE_NAME}' already exists — skipping.")
        else:
            raise

    # enable TTL (idempotent)
    client = boto3.client("dynamodb", region_name=region)
    client.update_time_to_live(
        TableName=TABLE_NAME,
        TimeToLiveSpecification={"AttributeName": TTL_ATTR, "Enabled": True},
    )
    print(f"  TTL enabled on '{TTL_ATTR}'.")


def attach_policy(iam_user, region):
    iam = boto3.client("iam")
    table_arn = f"arn:aws:dynamodb:{region}:{boto3.client('sts').get_caller_identity()['Account']}:table/{TABLE_NAME}"
    policy_doc = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
            "Resource": table_arn,
        }],
    })
    iam.put_user_policy(UserName=iam_user, PolicyName=POLICY_NAME, PolicyDocument=policy_doc)
    print(f"  Inline policy '{POLICY_NAME}' attached to user '{iam_user}'.")


def main():
    parser = argparse.ArgumentParser(description="Set up AWS resources for espn_results.py")
    parser.add_argument("--region",   default="us-east-1")
    parser.add_argument("--iam-user", help="IAM username to attach DynamoDB policy to (optional)")
    args = parser.parse_args()

    ddb = boto3.resource("dynamodb", region_name=args.region)

    print(f"\n=== ESPN Results CLI — AWS setup ===\n")
    create_table(ddb, args.region)

    if args.iam_user:
        attach_policy(args.iam_user, args.region)
    else:
        print("  Skipping IAM policy (no --iam-user provided).")
        print("  Make sure your AWS credentials have dynamodb:GetItem and dynamodb:PutItem on the table.")

    print("\nDone. You can now run espn_results.py.\n")


if __name__ == "__main__":
    main()
