import boto3
import json

iam = boto3.client('iam')

def policy_allows_create_bucket(statements):
    for stmt in statements:
        if stmt.get("Effect") != "Allow":
            continue
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        for action in actions:
            if action.lower() in ["s3:createbucket", "s3:*", "*"]:
                return True
    return False

def get_all_policies():
    paginator = iam.get_paginator('list_policies')
    for page in paginator.paginate(Scope='Local'):  # Scope='All' to include AWS-managed
        for policy in page['Policies']:
            yield policy

def get_policy_document(policy_arn, version_id):
    response = iam.get_policy_version(
        PolicyArn=policy_arn,
        VersionId=version_id
    )
    return response['PolicyVersion']['Document']

print("Scanning policies that allow s3:CreateBucket...\n")
for policy in get_all_policies():
    policy_arn = policy['Arn']
    default_version = policy['DefaultVersionId']
    doc = get_policy_document(policy_arn, default_version)
    statements = doc['Statement']
    if isinstance(statements, dict):  # Handle single-statement policy
        statements = [statements]
    if policy_allows_create_bucket(statements):
        print(f"[✓] {policy['PolicyName']} ({policy_arn}) allows s3:CreateBucket")
