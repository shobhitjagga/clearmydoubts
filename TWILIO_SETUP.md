# Twilio WhatsApp Integration Guide

## Overview

The application now supports **both** WhatsApp Cloud API (Meta/Facebook) and Twilio WhatsApp. The existing WhatsApp Cloud API functionality is preserved and continues to work.

## Provider Selection

Set the `WHATSAPP_PROVIDER` environment variable to choose which provider to use:
- `whatsapp_cloud` (default) - Uses Meta/Facebook WhatsApp Business API
- `twilio` - Uses Twilio WhatsApp API

## Environment Variables

### For Twilio WhatsApp:
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886  # Your Twilio WhatsApp number
WHATSAPP_PROVIDER=twilio
```

### For WhatsApp Cloud API (existing):
```bash
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_PROVIDER=whatsapp_cloud  # or omit (default)
```

## Webhook Endpoints

### WhatsApp Cloud API (Meta/Facebook)
- **POST** `/webhook` - Main webhook endpoint
- **POST** `/whatsapp_webhook` - Alternative endpoint (same functionality)
- **GET** `/webhook` - Webhook verification (for Meta)

### Twilio WhatsApp
- **POST** `/twilio_webhook` - Twilio webhook endpoint

## Setting Up Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to your WhatsApp Sandbox or WhatsApp-enabled number
3. Set the webhook URL to: `https://your-app.onrender.com/twilio_webhook`
4. Set HTTP method to: `POST`
5. Save the configuration

## Testing

### Test Twilio Webhook Locally

You can test the Twilio webhook using curl:

```bash
curl -X POST http://localhost:8000/twilio_webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+919876543210" \
  -d "Body=What is photosynthesis?" \
  -d "NumMedia=0"
```

### Test Twilio Image Message

```bash
curl -X POST http://localhost:8000/twilio_webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+919876543210" \
  -d "NumMedia=1" \
  -d "MediaUrl0=https://example.com/image.jpg"
```

## Code Structure

### Preserved Files
- `whatsapp_cloud_api.py` - Original WhatsApp Cloud API implementation (preserved)
- Existing webhook endpoints continue to work as before

### New Files
- `twilio_whatsapp.py` - Twilio WhatsApp integration
- `main.py` - Updated to support both providers

### Unified Functions
- `send_message(to, message, provider)` - Sends via configured provider
- `process_question_and_respond(sender, question, provider)` - Processes question and responds

## Message Length Limits

- **WhatsApp Cloud API**: 4096 characters (chunked at 4000)
- **Twilio**: 1600 characters (chunked at 1500)

Both implementations automatically split long messages into chunks.

## Switching Providers

To switch between providers, simply change the `WHATSAPP_PROVIDER` environment variable:

```bash
# Use Twilio
export WHATSAPP_PROVIDER=twilio

# Use WhatsApp Cloud API
export WHATSAPP_PROVIDER=whatsapp_cloud
# or just remove the variable (defaults to whatsapp_cloud)
```

## Troubleshooting

### Check Provider Status
Visit `/health` endpoint to see which providers are configured:
```bash
curl https://your-app.onrender.com/health
```

### View Logs
Check Render logs for:
- "Received WhatsApp Cloud API payload:" - WhatsApp Cloud API messages
- "Received Twilio WhatsApp payload:" - Twilio messages
- "Processing question using provider: twilio/whatsapp_cloud" - Shows active provider

### Common Issues

1. **Twilio messages not received**
   - Verify webhook URL is set correctly in Twilio Console
   - Check that `TWILIO_WHATSAPP_FROM` includes `whatsapp:` prefix
   - Ensure `WHATSAPP_PROVIDER=twilio` is set

2. **Both providers active**
   - The system uses the provider specified in `WHATSAPP_PROVIDER`
   - You can have both configured, but only one will be used based on the env var

3. **Media download errors**
   - Twilio media requires authentication (handled automatically)
   - WhatsApp Cloud API media requires token (handled automatically)

## Migration Notes

- **No breaking changes**: Existing WhatsApp Cloud API webhooks continue to work
- **Backward compatible**: Default provider is `whatsapp_cloud` if not specified
- **Separate endpoints**: Twilio uses `/twilio_webhook`, WhatsApp Cloud API uses `/webhook`

