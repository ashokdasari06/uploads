BUCKET_NAME="my-target-bucket"
BUCKET_ARN="arn:aws:s3:::${BUCKET_NAME}"

# Function to check if a policy grants access to the specific bucket
check_policy_for_bucket() {
  POLICY_DOC="$1"
  echo "$POLICY_DOC" | jq -r '.Statement[] | select(.Action | type == "string" or type == "array") |
    select((.Action | tostring | contains("s3:*") | not)) |
    select(.Resource != null) |
    select((.Resource | tostring | contains("'"$BUCKET_ARN"'")) or (contains("'"$BUCKET_ARN"/*")))'
}

echo "### Checking Inline Policies of Roles ###"
for role in $(aws iam list-roles --query 'Roles[*].RoleName' --output text); do
  inline_policies=$(aws iam list-role-policies --role-name "$role" --query 'PolicyNames' --output text)
  for policy_name in $inline_policies; do
    policy_doc=$(aws iam get-role-policy --role-name "$role" --policy-name "$policy_name" --query 'PolicyDocument' --output json)
    match=$(check_policy_for_bucket "$policy_doc")
    if [[ -n "$match" ]]; then
      echo "Role: $role | Inline Policy: $policy_name"
    fi
  done
done

echo "### Checking Attached Managed Policies ###"
for policy_arn in $(aws iam list-policies --scope Local --query 'Policies[*].Arn' --output text); do
  versions=$(aws iam list-policy-versions --policy-arn "$policy_arn" --query 'Versions[?IsDefaultVersion].VersionId' --output text)
  policy_doc=$(aws iam get-policy-version --policy-arn "$policy_arn" --version-id "$versions" --query 'PolicyVersion.Document' --output json)
  match=$(check_policy_for_bucket "$policy_doc")
  if [[ -n "$match" ]]; then
    echo "Policy ARN: $policy_arn"
    aws iam list-entities-for-policy --policy-arn "$policy_arn" --query 'PolicyRoles[*].RoleName' --output text | awk '{print "  Attached to Role(s): " $0}'
  fi
done
