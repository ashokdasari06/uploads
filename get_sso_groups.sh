#!/bin/bash

IDENTITY_STORE_ID="<your-identity-store-id>"
OUTPUT="group_users.csv"

echo "Group,Users" > "$OUTPUT"

# Get all groups
GROUPS=$(aws identitystore list-groups --identity-store-id "$IDENTITY_STORE_ID" --output json)

# Loop through groups starting with "gg"
echo "$GROUPS" | jq -c '.Groups[] | select(.DisplayName | startswith("gg"))' | while read -r group; do
  GROUP_ID=$(echo "$group" | jq -r '.GroupId')
  GROUP_NAME=$(echo "$group" | jq -r '.DisplayName')

  # Get group memberships
  MEMBERSHIPS=$(aws identitystore list-group-memberships --identity-store-id "$IDENTITY_STORE_ID" --group-id "$GROUP_ID" --output json)

  # Get user emails (UserName) for each member
  USER_IDS=$(echo "$MEMBERSHIPS" | jq -r '.GroupMemberships[].MemberId.UserId')

  USERS=()
  for USER_ID in $USER_IDS; do
    USERNAME=$(aws identitystore get-user --identity-store-id "$IDENTITY_STORE_ID" --user-id "$USER_ID" | jq -r '.UserName')
    USERS+=("$USERNAME")
  done

  # Join users with commas
  USER_LIST=$(IFS=, ; echo "${USERS[*]}")

  # Write to CSV
  echo "\"$GROUP_NAME\",\"$USER_LIST\"" >> "$OUTPUT"
done

echo "✅ Done. Output written to $OUTPUT"
