#!/bin/bash

echo "Scanning AWSReservedSSO IAM roles for s3:* access..."

for role in $(aws iam list-roles --query 'Roles[?starts_with(RoleName, `AWSReservedSSO_`)].RoleName' --output text); do
  
  # Check inline policies
  for policy_name in $(aws iam list-role-policies --role-name "$role" --query 'PolicyNames' --output text); do
    policy_doc=$(aws iam get-role-policy --role-name "$role" --policy-name "$policy_name" --query 'PolicyDocument' --output json)
    has_s3_star=$(echo "$policy_doc" | jq -e '
      .Statement as $stmt |
      (if ($stmt | type) == "array" then $stmt else [$stmt] end)[] |
      select(.Action != null) |
      select(.Action | tostring | test("s3:\\*"))' 2>/dev/null)
    
    if [[ -n "$has_s3_star" ]]; then
      echo "Role: $role"
      echo "  Inline Policy: $policy_name grants s3:*"
    fi
  done

  # Check attached managed policies
  for policy_arn in $(aws iam list-attached-role-policies --role-name "$role" --query 'AttachedPolicies[*].PolicyArn' --output text); do
    version_id=$(aws iam list-policy-versions --policy-arn "$policy_arn" --query 'Versions[?IsDefaultVersion].VersionId' --output text)
    policy_doc=$(aws iam get-policy-version --policy-arn "$policy_arn" --version-id "$version_id" --query 'PolicyVersion.Document' --output json)
    has_s3_star=$(echo "$policy_doc" | jq -e '
      .Statement as $stmt |
      (if ($stmt | type) == "array" then $stmt else [$stmt] end)[] |
      select(.Action != null) |
      select(.Action | tostring | test("s3:\\*"))' 2>/dev/null)
    
    if [[ -n "$has_s3_star" ]]; then
      echo "Role: $role"
      echo "  Managed Policy: $policy_arn grants s3:*"
    fi
  done

done
