#!/bin/bash
curl -s 'https://poke.com/api/v1/inbound-sms/webhook' \
  -H "Authorization: Bearer YOUR_POKE_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"message": "This is an automated message being sent to you from Mac through your Poke API: Laptop has been closed"}'
