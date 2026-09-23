# 🌿 Smart Greenhouse & Plant Shop Assistant

![Smart Greenhouse Assistant Demo](demo.gif)

A conversational AI agent built with Google Cloud Agent Development Kit (ADK) that helps plant owners manage greenhouse inventory, calculate precise watering schedules, discover nearby plant nurseries, and generate visual AI media for botanical care.

---

## 🚀 Features & Implemented Tools

Based on the codebase in `app/` and `agents-cli-manifest.yaml`, the agent implements the following features and integrations:

### 📱 Rich Interactive UI (A2UI v0.8)
- **A2UI Protocol Integration**: Uses `A2uiSchemaManager` (v0.8 with Basic Catalog) to render structured, interactive UI cards (Cards, Columns, Rows, Text, Images) for plant inventory, care guides, and generated media over the Agent-to-Agent (A2A) protocol.

### 🪴 Plant Inventory & Database (Firestore)
- **Firestore Plant Catalog**: Queries and mutates live greenhouse inventory stored in Google Cloud Firestore (`plants` collection).
- **Pet-Safe & Light Filtering**: Enables users to search for indoor plants by care difficulty, toxicity, light requirements, and price.

### 💧 Watering Math & Code Sandbox
- **Watering Schedule Calculator**: Calculates custom watering frequencies (in days) using pot size, light intensity, ambient temperature, and relative humidity.
- **Vertex AI Agent Engine Sandbox**: Executes custom Python math logic securely inside `AgentEngineSandboxCodeExecutor` (`PicklableAgentEngineSandboxCodeExecutor`).

### 🌦️ Real-Time Environmental Conditions
- **Weather API Integration**: Fetches real-time ambient temperature, relative humidity, and solar daylight status via Open-Meteo.

### 📍 Google Maps & Places Search
- **Geocoding & Nearby Places**: Converts street addresses into geographic coordinates (`geocode_address`) and finds nearby plant nurseries, florists, and greenhouses (`find_nearby_places`) using Google Maps APIs.

### 🎨 Visual AI Media Generation (Imagen & Omni)
- **AI Plant Photo Generation**: Generates high-resolution plant photographs using Google's `gemini-3.1-flash-lite-image` model in the `global` region, saves artifacts, and uploads them to a public Cloud Storage bucket (`smart-greenhouse-assets-3acfd04a83e5`).
- **AI Plant Video Generation**: Generates short plant videos using Google's `gemini-omni-flash-preview` model in the `global` region via the Interactions API, saves artifacts, and uploads them to public Cloud Storage.

### 🧠 Memory Bank (Long-Term User Memory)
- **Session Memory Persistence**: Uses `PreloadMemoryTool` and `generate_memories_callback` to store and recall user home light levels, pot sizes, plant care history, and preferences across sessions.

---

## 🔮 Planned Capabilities (Not Yet Implemented)

The following items from `project_brief.md` are planned for future releases:
- 🍃 **Leaf Disease Diagnosis**: Diagnostic classification from uploaded user photos (*Planned*).
- 🏡 **AR Room Placement Preview**: Augmented reality spatial preview of plants in indoor rooms (*Planned*).

---

## 🛠️ Architecture & Tech Stack

- **Agent Framework**: Google Cloud ADK (Agent Development Kit) & Python 3.13 / 3.14.
- **LLM / Foundation Models**: Gemini Models (`gemini-2.5-flash`, `gemini-3.1-flash-lite-image`, `gemini-omni-flash-preview`).
- **Database**: Google Cloud Firestore.
- **Storage**: Google Cloud Storage (`smart-greenhouse-assets-3acfd04a83e5`).
- **Sandbox Execution**: Vertex AI Agent Engine Sandbox Environment.
- **Frontend Proxy**: FastAPI + HTML5 / CSS3 Vanilla Dark Botanical Interface.

---

## 💻 Local Setup & Running Instructions

### Prerequisites
- Python 3.11+
- `uv` package manager installed (`pip install uv`)
- Google Cloud SDK (`gcloud`) authenticated with a project containing Firestore enabled.

### 1. Clone & Install Dependencies
```bash
# Clone repository
cd smart-greenhouse

# Install dependencies into virtual environment
uv sync
```

### 2. Configure Environment Variables
Set your Google Cloud project and bucket details:
```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_REGION="us-east1"
```

### 3. Run Agent Locally (ADK Playground)
Start the interactive Agent Development Kit playground:
```bash
uv run adk playground
```
Navigate to the terminal URL output by `adk playground` to chat with the agent and view A2UI cards and artifacts.

### 4. Run Frontend Web App Locally
Start the FastAPI proxy and lightweight chat web interface:
```bash
uv run python frontend/main.py
```
Open a browser and navigate to port 8080 on localhost to test the web interface.
