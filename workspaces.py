import boto3
from datetime import datetime, timezone
from tabulate import tabulate

# Create clients
ws_client = boto3.client('workspaces')

# Get all WorkSpaces in AVAILABLE state
workspaces = ws_client.describe_workspaces()['Workspaces']
available_workspaces = [ws for ws in workspaces if ws['State'] == 'AVAILABLE']

# Prepare data list
results = []

for ws in available_workspaces:
    ws_id = ws['WorkspaceId']
    state = ws['State']
    running_mode = ws['WorkspaceProperties'].get('RunningMode', 'N/A')

    # Get connection status
    conn_status = ws_client.describe_workspace_connection_status(WorkspaceIds=[ws_id])
    status_info = conn_status['WorkspaceConnectionStatus'][0] if conn_status['WorkspaceConnectionStatus'] else {}

    connection_state = status_info.get('ConnectionState', 'N/A')
    last_conn_time = status_info.get('LastKnownUserConnectionTimestamp')

    # Calculate days since last login
    if last_conn_time:
        now = datetime.now(timezone.utc)
        delta_days = (now - last_conn_time).days
        last_conn_str = last_conn_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        delta_days = "N/A"
        last_conn_str = "Never"

    # Append result row
    results.append([
        ws_id,
        state,
        running_mode,
        connection_state,
        last_conn_str,
        delta_days
    ])

# Print results as table
headers = ["WorkspaceId", "State", "Mode", "ConnectionState", "LastLogin", "DaysAgo"]
print(tabulate(results, headers=headers, tablefmt="github"))
