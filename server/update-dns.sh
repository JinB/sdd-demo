#!/bin/bash
# Runs on every EC2 start via systemd.
# Updates Route 53 A records for all sdd-demo subdomains to the current public IP.
# Requires: IAM role with route53:ChangeResourceRecordSets + ListHostedZones
set -euo pipefail

DOMAIN="4eng.online"
SUBDOMAINS="wp astro docu next"
TTL=60

LOG() { echo "$(date '+%F %T') $*"; }

# IMDSv2 — get current public IP
TOKEN=$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
PUBLIC_IP=$(curl -sf -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/public-ipv4)

LOG "Public IP: $PUBLIC_IP"

# Resolve hosted zone ID dynamically
ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name "${DOMAIN}." \
  --query "HostedZones[0].Id" --output text | cut -d/ -f3)

LOG "Hosted zone: $ZONE_ID"

# Build Changes JSON array
CHANGES="["
FIRST=1
for SUB in $SUBDOMAINS; do
  [ $FIRST -eq 0 ] && CHANGES+=","
  CHANGES+=$(printf '{"Action":"UPSERT","ResourceRecordSet":{"Name":"%s.%s.","Type":"A","TTL":%d,"ResourceRecords":[{"Value":"%s"}]}}' \
    "$SUB" "$DOMAIN" "$TTL" "$PUBLIC_IP")
  FIRST=0
done
CHANGES+="]"

RESULT=$(aws route53 change-resource-record-sets \
  --hosted-zone-id "$ZONE_ID" \
  --change-batch "{\"Comment\":\"EC2 start ${PUBLIC_IP}\",\"Changes\":${CHANGES}}" \
  --query "ChangeInfo.[Status,Id]" --output text)

LOG "Route 53 change: $RESULT"
LOG "DNS updated: $(echo $SUBDOMAINS | tr ' ' ',').${DOMAIN} → ${PUBLIC_IP}"
