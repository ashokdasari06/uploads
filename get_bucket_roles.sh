#!/bin/bash

BUCKET_NAME="my-target-bucket"
BUCKET_ARN="arn:aws:s3:::${BUCKET_NAME}"

# Function to check policy for specific bucket access (non-wildcard)
check_policy_for_bucket() {
  POLICY_DOC="$1"
  echo "$POLICY_DOC" | jq -r --arg BUCKET_ARN "$BUCKET_ARN" '
    def normalize(x): if x|type == "array" then x else [x] end;
    .Statement as $stmt |
    normalize($stmt)[] |
    select(.Action and (.Action | tostring | contains("s3:*") | not)) |
    select(.Resource != null) |
    select(
      (.Resource | type == "string" and (. | contains($BUCKET_ARN))) or
      (.Resource | type == "array" and any(.[]; contains($BUCKET_ARN)))
    )
  '
}

echo "### Checking Inline Policies of Roles ###"
for role in $(aws iam list-roles --query 'Roles[*].RoleName' --output text); do
  for policy_name in $(aws iam list-role-policies --role-name "$role" --query 'PolicyNames' --output text); do
    policy_doc=$(aws iam get-role-policy --role-name "$role" --policy-name "$policy_name" --query 'PolicyDocument' --output json)
    match=$(check_policy_for_bucket "$policy_doc")
    if [[ -n "$match" ]]; then
      echo "Role: $role | Inline Policy: $policy_name"
    fi
  done
done

echo "### Checking Attached Managed Policies ###"
for policy_arn in $(aws iam list-policies --scope Local --query 'Policies[*].Arn' --output text); do
  default_version=$(aws iam list-policy-versions --policy-arn "$policy_arn" --query 'Versions[?IsDefaultVersion].VersionId' --output text)
  policy_doc=$(aws iam get-policy-version --policy-arn "$policy_arn" --version-id "$default_version" --query 'PolicyVersion.Document' --output json)
  match=$(check_policy_for_bucket "$policy_doc")
  if [[ -n "$match" ]]; then
    echo "Managed Policy: $policy_arn"
    aws iam list-entities-for-policy --policy-arn "$policy_arn" --query 'PolicyRoles[*].RoleName' --output text | awk '{print "  Attached to Role(s): " $0}'
  fi
done
