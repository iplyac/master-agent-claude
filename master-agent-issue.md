# Master Agent: Google GenAI API Key Issue

## Problem Summary
The master-agent service fails to process messages due to Google GenAI API key not being passed correctly to the client.

## Error Message
```
Processing error: conversation_id=tg_dm_234759359, error=Missing key inputs argument!
To use the Google AI API, provide (`api_key`) arguments.
To use the Google Cloud API, provide (`vertexai`, `project` & `location`) arguments.
```

## Current Configuration
The service has these environment variables configured:
```yaml
env:
  - name: GCP_PROJECT_ID
    value: gen-lang-client-0741140892
  - name: MODEL_API_KEY
    valueFrom:
      secretKeyRef:
        key: latest
        name: GOOGLE_API_KEY
```

## Observations from Logs
1. Service starts successfully: `Starting ai-agent: port=8080, model=gemini-2.0-flash, region=europe-west4, api_key_configured=True`
2. API key is resolved: `API key resolved from MODEL_API_KEY env var`
3. But then fails when processing a message with the "Missing key inputs argument" error

## Root Cause Hypothesis
The API key is being read from the environment variable, but it's not being passed to the `google.genai` client during initialization or when making API calls.

Possible issues:
1. The `google.genai` client is created without the `api_key` parameter
2. The API key variable name expected by the SDK differs from `MODEL_API_KEY`
3. The client initialization happens before the API key is resolved

## What to Check
1. How is the `google.genai` client initialized? Look for `genai.Client()` or similar
2. Is the `api_key` parameter being passed explicitly?
3. The SDK might expect `GOOGLE_API_KEY` environment variable directly (not `MODEL_API_KEY`)

## Quick Fix Options
1. **Option A**: Pass `api_key` explicitly when creating the client:
   ```python
   client = genai.Client(api_key=os.getenv("MODEL_API_KEY"))
   ```

2. **Option B**: Set `GOOGLE_API_KEY` env var (which the SDK auto-detects):
   ```bash
   gcloud run services update master-agent --region=europe-west4 \
     --update-env-vars="GOOGLE_API_KEY=$(gcloud secrets versions access latest --secret=GOOGLE_API_KEY)"
   ```

3. **Option C**: Use the secret directly as `GOOGLE_API_KEY`:
   ```bash
   gcloud run services update master-agent --region=europe-west4 \
     --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest"
   ```

## Service Details
- **Service URL**: https://master-agent-298607833444.europe-west4.run.app
- **Region**: europe-west4
- **Health check**: Returns `{"status":"ok"}`
