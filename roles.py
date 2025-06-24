import boto3
from datetime import datetime, timezone

iam = boto3.client("iam")

def get_all_roles_last_used():
    roles_with_usage = []

    paginator = iam.get_paginator("list_roles")
    for page in paginator.paginate():
        for role in page["Roles"]:
            role_name = role["RoleName"]
            last_used_info = role.get("RoleLastUsed", {})
            last_used_date = last_used_info.get("LastUsedDate")

            if last_used_date:
                days_ago = (datetime.now(timezone.utc) - last_used_date).days
                roles_with_usage.append((role_name, last_used_date.strftime('%Y-%m-%d'), days_ago))
            else:
                roles_with_usage.append((role_name, "Never Used", "N/A"))

    return sorted(roles_with_usage, key=lambda x: (x[2] if isinstance(x[2], int) else -1), reverse=True)

for role, last_used, days in get_all_roles_last_used():
    print(f"{role:50} | Last Used: {last_used:15} | Days Ago: {days}")
