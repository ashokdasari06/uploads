import boto3

# --- Settings ---
role_name = "OrganizationAccountAccessRole"
region = "us-east-1"

org = boto3.client("organizations")
sts = boto3.client("sts")

# Get all account IDs
accounts = []
paginator = org.get_paginator('list_accounts')
for page in paginator.paginate():
    for acct in page['Accounts']:
        if acct['Status'] == 'ACTIVE':
            accounts.append(acct['Id'])

print(f"Found {len(accounts)} active accounts.")

# Collect subnet CIDRs per account
results = []

for acct_id in accounts:
    try:
        print(f"\n🔄 Assuming role in {acct_id}...")

        assumed = sts.assume_role(
            RoleArn=f"arn:aws:iam::{acct_id}:role/{role_name}",
            RoleSessionName="GetSubnets"
        )

        creds = assumed['Credentials']
        ec2 = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
        )

        subnets = ec2.describe_subnets()['Subnets']
        for subnet in subnets:
            results.append({
                'AccountId': acct_id,
                'SubnetId': subnet['SubnetId'],
                'VpcId': subnet['VpcId'],
                'CidrBlock': subnet['CidrBlock'],
                'AvailabilityZone': subnet['AvailabilityZone']
            })

    except Exception as e:
        print(f"❌ Failed for account {acct_id}: {str(e)}")

# Output results
print("\n📦 Subnet CIDRs collected:")
for r in results:
    print(r)
