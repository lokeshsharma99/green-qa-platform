# Start Dashboard with Real API

## Quick Start (3 Steps)

### Step 1: Get Your API URL

If your Lambda API is already deployed:

```bash
# Get the API URL from CloudFormation
aws cloudformation describe-stacks \
  --stack-name green-qa-platform \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
```

This will output something like:
```
https://abc123xyz.execute-api.eu-west-2.amazonaws.com/Prod
```

### Step 2: Update JavaScript

Open `public/climatiq-validation.js` and update line 4:

```javascript
baseUrl: 'https://YOUR-ACTUAL-API-URL.execute-api.eu-west-2.amazonaws.com/Prod',
```

Replace with your actual API URL from Step 1.

### Step 3: Start Web Server

```bash
cd green-qa-platform/dashboard/public
python -m http.server 8000
```

Then open: http://localhost:8000/climatiq-validation.html

---

## If API Not Deployed Yet

### Deploy the Lambda API:

```bash
cd green-qa-platform

# Build
sam build

# Deploy (first time - interactive)
sam deploy --guided

# Or deploy with existing config
sam deploy
```

After deployment, go back to Step 1 to get your API URL.

---

## Verify API is Working

Test the endpoints directly:

```bash
# Test search endpoint
curl "https://YOUR-API-URL/Prod/climatiq/search?query=electricity&limit=5"

# Test validate endpoint
curl -X POST "https://YOUR-API-URL/Prod/climatiq/validate" \
  -H "Content-Type: application/json" \
  -d '{"region":"eu-west-2"}'
```

---

## Environment Variables

The Lambda needs the Climatiq API key (already set):

```bash
CLIMATIQ_API_KEY=QQP3JPFPK11TF0ADEAMD9XECG0
```

This is the free tier key that supports:
- ✅ Search endpoint (unlimited)
- ❌ Cloud compute (premium only)
- ❌ Procurement (premium only)

---

## Troubleshooting

### "Failed to fetch" Error
- Make sure you're accessing via HTTP (not file://)
- Check the API URL is correct
- Verify the Lambda is deployed

### CORS Error
- The Lambda handler already has CORS headers
- Make sure you're using the correct API URL
- Check CloudWatch logs: `sam logs -n ApiFunction --tail`

### "No results" from Search
- Try broader search terms: "electricity" instead of "electricity UK grid 2023"
- The free tier search has limited results
- Check Lambda logs for API errors

---

## Alternative: Use Existing Dashboard Server

If you have the main dashboard running, you can access it there:

```bash
# If dashboard is already running on port 8000
http://localhost:8000/climatiq-validation.html
```

---

## Production Setup

For production, update the JavaScript to use environment variables:

```javascript
const API_CONFIG = {
    baseUrl: window.ENV?.API_URL || 'https://your-production-api.com/Prod',
    // ...
};
```

Then inject the URL via a config file or build process.
