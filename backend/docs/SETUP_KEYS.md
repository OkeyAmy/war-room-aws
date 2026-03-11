# How to Configure API Keys for WAR ROOM

This guide explains how to obtain and configure the necessary API keys and credentials required to run the **WAR ROOM** backend environment based on the `.env.example`.

---

## 1. Google Cloud Platform (GCP) & Firestore

GCP is utilized for Firestore (database state) and optionally Pub/Sub (events).

### Local Development (Free Emulators)

For local development, real GCP credentials are not required. You can utilize the local Google Cloud emulators.

1. Install the Google Cloud CLI.
2. Run the emulator suite:

   ```bash
   gcloud components install cloud-firestore-emulator pubsub-emulator
   gcloud emulators firestore start --host-port=localhost:8080
   gcloud emulators pubsub start --host-port=localhost:8085
   ```

3. Ensure these emulator endpoints are set in your `.env`:

   ```env
   FIRESTORE_EMULATOR_HOST=localhost:8080
   PUBSUB_EMULATOR_HOST=localhost:8085
   PUBSUB_TOPIC=war-room-events
   ```

### Production Deployment

1. Create a [GCP Project](https://console.cloud.google.com/) and enable the **Firestore API** and **Pub/Sub API**.
2. Create an IAM Service Account with the required roles (e.g., `Cloud Datastore User`, `Pub/Sub Admin`).
3. Generate and download a JSON service account key.
4. Set the path in your `.env` (ensure emulators are commented out for production):

   ```env
   GCP_PROJECT_ID=your-gcp-project-id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   ```

---

## 2. Amazon Nova API (Text Completions)

Amazon Nova models act as the primary cognitive engine for the AI agents' reasoning logs and scenario generation.

### How to get it

1. Navigate to the Amazon Nova API provisioning portal or your provider's dashboard.
2. Generate a standard Nova API Key.
3. Add the following to your `.env`:

   ```env
   NOVA_API_KEY=your-nova-api-key
   NOVA_BASE_URL=https://api.nova.amazon.com/v1

   # Recommended Default Models
   NOVA_SCENARIO_MODEL=nova-2-lite-v1
   NOVA_AGENT_MODEL=nova-2-lite-v1
   NOVA_FAST_MODEL=nova-2-lite-v1
   NOVA_VISION_MODEL=nova-2-lite-v1
   ```

---

## 3. AWS Credentials (for Nova Sonic via LiveKit + Bedrock)

AWS Bedrock credentials are required for the AI agents' voice output, powered by Amazon Nova Sonic and orchestrated by the LiveKit Pipeline.

### How to get it

1. Sign in to your [AWS Management Console](https://console.aws.amazon.com/).
2. Navigate to **Amazon Bedrock** and request model access for **Amazon Nova**.
3. Go to **IAM (Identity and Access Management)**, and create a user (or Role) with permissions to invoke Bedrock models (`bedrock:InvokeModel`).
4. Generate an Access Key ID and Secret Access Key.
5. Add the keys to your `.env`:

   ```env
   AWS_ACCESS_KEY_ID=your-aws-access-key-id
   AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
   AWS_REGION=us-east-1

   # Nova Sonic semantic voice configurations
   NOVA_SONIC_VOICE=tiffany
   NOVA_SONIC_TURN_DETECTION=MEDIUM
   ```

---

## 4. Google Gemini API Key (Fallback Systems)

Google Gemini is integrated as a highly resilient intelligent fallback. On startup, the backend validates AWS credentials. If it's invalid—or if AWS experiences an outage mid-session—the simulation seamlessly fails over to Gemini.

### How to get it

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create a new API Key within an existing or new project.
3. Add it to your `.env`:

   ```env
   GOOGLE_API_KEY=your-google-api-key

   # Gemini Flagship Models
   GEMINI_AGENT_MODEL=gemini-3-flash
   GEMINI_SCENARIO_MODEL=gemini-3-flash
   GEMINI_FAST_MODEL=gemini-3-flash
   GEMINI_VISION_MODEL=gemini-3-flash
   GEMINI_REALTIME_MODEL=gemini-2.5-flash-native-audio-preview-12-2025
   ```

---

## 5. LiveKit (Real-time WebRTC Audio)

LiveKit is required for the backend-managed WebRTC voice transport ensuring latency-free interaction between the Chairman and the Agents.

### How to get it

1. Create a free account at [LiveKit Cloud](https://cloud.livekit.io/).
2. Provision a new project.
3. In the project dashboard under Settings/Keys, locate your **WebSocket URL**, **API Key**, and **API Secret**.
4. Add them to your `.env`:

   ```env
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your-livekit-api-key
   LIVEKIT_API_SECRET=your-livekit-api-secret
   ```

---

## 6. General Application Settings

Finally, set up the standard FastAPI/application properties in your `.env`:

```env
# Network and Environment
HOST=0.0.0.0
PORT=8000
DEBUG=true
ENVIRONMENT=development  # Use "development" (local datastore) or "production" (Firebase)

# Voice and Agent Settings
VOICE_BACKEND=livekit_aws
SINGLE_AGENT_VOICE_MODE=false
MAX_AGENTS_PER_SESSION=4
```
