#!/bin/bash
# Runs on every EC2 start via systemd.
# Updates Route 53 A records for all sdd-demo subdomains to the current public IP,
# then sends a SendGrid notification email with the new IP and site links.
# Requires: IAM role with route53:ChangeResourceRecordSets + ListHostedZones
set -euo pipefail

DOMAIN="4eng.online"
SUBDOMAINS="wp astro docu next"
TTL=60
ENV_FILE="/var/www/sdd-demo/.env"

LOG() { echo "$(date '+%F %T') $*"; }

# ── Public IP via IMDSv2 ───────────────────────────────────────────────────────
TOKEN=$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
PUBLIC_IP=$(curl -sf -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/public-ipv4)

LOG "Public IP: $PUBLIC_IP"

# ── Route 53 update ───────────────────────────────────────────────────────────
ZONE_ID=$(aws route53 list-hosted-zones \
  --query "HostedZones[?Name=='${DOMAIN}.'].Id" --output text | cut -d/ -f3)

LOG "Hosted zone: $ZONE_ID"

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

# ── SendGrid notification ─────────────────────────────────────────────────────
[ -f "$ENV_FILE" ] && { set -a; source "$ENV_FILE"; set +a; }

if [ -z "${SENDGRID_API_KEY:-}" ]; then
  LOG "SENDGRID_API_KEY not set — skipping email"
  exit 0
fi

python3 - <<PYEOF
import json, os, urllib.request, urllib.error, datetime, zoneinfo

prague = zoneinfo.ZoneInfo("Europe/Prague")
now    = datetime.datetime.now(prague).strftime("%H:%M %Z, %d %b %Y")
ip     = "$PUBLIC_IP"
domain = "$DOMAIN"
subs   = "$SUBDOMAINS".split()

def link(sub):
    url = f"https://{sub}.{domain}"
    return f'  <a href="{url}" style="color:#1a73e8;text-decoration:none;">{url}</a>'

body_html = (
    '<pre style="font-family:monospace;font-size:14px;line-height:1.8">\n'
    f'EC2 started — DNS updated\n'
    f'{now}\n\n'
    f'New IP: <b>{ip}</b>\n\n'
    'Sites:\n'
    + "\n".join(link(s) for s in subs)
    + "\n</pre>"
)

payload = {
    "personalizations": [{"to": [{"email": "eugenio.besson@gmail.com"}]}],
    "from": {"email": "noreply@4eng.online", "name": "4eng"},
    "subject": f"EC2 started — {ip}",
    "content": [{"type": "text/html", "value": body_html}],
}

req = urllib.request.Request(
    "https://api.sendgrid.com/v3/mail/send",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {os.environ['SENDGRID_API_KEY']}",
        "Content-Type": "application/json",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(req) as r:
        print(f"Email sent — HTTP {r.status}")
except urllib.error.HTTPError as e:
    print(f"SendGrid error — HTTP {e.code}: {e.read().decode()}")
    raise
PYEOF

LOG "Email sent to eugenio.besson@gmail.com"
