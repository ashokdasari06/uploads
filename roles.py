import boto3
import time
from datetime import datetime, timezone

iam = boto3.client("iam")

def wait_for_job(job_id):
    while True:
        result = iam.get_service_last_accessed_details(JobId=job_id)
        if result["JobStatus"] == "COMPLETED":
            return result
        time.sleep(1)

def get_roles_latest_service_access():
    paginator = iam.get_paginator("list_roles")
    summary = []

    for page in paginator.paginate():
        for role in page["Roles"]:
            role_name = role["RoleName"]
            role_arn = role["Arn"]

            # Start job
            job = iam.generate_service_last_accessed_details(Arn=role_arn)
            job_id = job["JobId"]

            # Wait for job to complete
            result = wait_for_job(job_id)
            services = result["ServicesLastAccessed"]

            # Find the most recently accessed service
            last_used_info = [
                (svc["LastAuthenticated"], svc["ServiceName"])
                for svc in services if "LastAuthenticated" in svc
            ]

            if last_used_info:
                most_recent, service_name = max(last_used_info)
                days_ago = (datetime.now(timezone.utc) - most_recent).days
                summary.append((role_name, role_arn, most_recent.strftime("%Y-%m-%d"), days_ago))
            else:
                summary.append((role_name, role_arn, "Never Accessed", "N/A"))

    return summary

# Output
for role_name, arn, last_accessed, days in get_roles_latest_service_access():
    print(f"{role_name:40} | {arn:80} | Last Accessed: {last_accessed:12} | Days Ago: {days}")
