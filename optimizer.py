import boto3
import datetime

workspaces = boto3.client("workspaces")
ses = boto3.client("ses")

WARNING_DAYS = 23
CUTOFF_DAYS = 30
SENDER_EMAIL = "admin@example.com"

def lambda_handler(event, context):
    now = datetime.datetime.utcnow()

    # Get all workspaces
    paginator = workspaces.get_paginator("describe_workspaces")
    for page in paginator.paginate():
        for ws in page["Workspaces"]:
            ws_id = ws["WorkspaceId"]
            user = ws["UserName"]

            # Get last connection timestamp
            status = workspaces.describe_workspaces_connection_status(
                WorkspaceIds=[ws_id]
            )["WorkspacesConnectionStatus"][0]

            last_conn = status.get("LastKnownUserConnectionTimestamp")

            if last_conn:
                days_inactive = (now - last_conn.replace(tzinfo=None)).days
            else:
                days_inactive = 999  # never connected

            # Send warning at 23 days
            if days_inactive == WARNING_DAYS:
                send_warning_email(user, ws_id)

            # Convert to AUTO_STOP at 30 days
            if days_inactive >= CUTOFF_DAYS:
                workspaces.modify_workspace_properties(
                    WorkspaceId=ws_id,
                    WorkspaceProperties={
                        "RunningMode": "AUTO_STOP",
                        "RunningModeAutoStopTimeoutInMinutes": 60  # adjust as needed
                    }
                )
                print(f"Converted {ws_id} for user {user} to AUTO_STOP")

def send_warning_email(user, workspace_id):
    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [f"{user}@example.com"]},
        Message={
            "Subject": {"Data": "Your WorkSpace will switch to AutoStop soon"},
            "Body": {
                "Text": {
                    "Data": f"""
Hello {user},

Your AWS WorkSpace {workspace_id} has been inactive for 23 days.
If unused for 7 more days, it will automatically switch from ALWAYS_ON to AUTO_STOP mode.

If you want to keep it in ALWAYS_ON, please log in at least once before then.
"""
                }
            },
        },
    )
