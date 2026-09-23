# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import uuid
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore
from google.genai import types
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

# Hardcoded Project ID string as required for Agent Platform compatibility
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-3acfd04a83e5"


def get_firestore_client() -> firestore.Client:
    """Helper to instantiate Firestore client with explicit hardcoded project ID."""
    key_file = "/tmp/antigravity-sa-key.json"
    if os.path.exists(key_file):
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_file(key_file)
        return firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def get_plants(
    light_requirement: str = None, pet_safe_only: bool = False, max_price: float = None
) -> str:
    """Retrieves available plants from the Smart Greenhouse catalog stored in Firestore database.

    Args:
        light_requirement: Optional filter for light level (e.g., 'Low', 'Medium', 'High').
        pet_safe_only: If True, only returns plants that are pet safe (nontoxic to cats/dogs).
        max_price: Optional maximum price limit for the plants in USD.

    Returns:
        A formatted list or summary of plants matching the filter criteria.
    """
    db = get_firestore_client()
    plants_ref = db.collection("plants")
    docs = plants_ref.stream()

    results = []
    for doc in docs:
        plant = doc.to_dict()
        plant["id"] = doc.id

        if pet_safe_only and not plant.get("pet_safe", False):
            continue
        if max_price is not None and plant.get("price", 0.0) > float(max_price):
            continue
        if light_requirement and light_requirement.lower() not in str(
            plant.get("light_requirement", "")
        ).lower():
            continue

        results.append(plant)

    if not results:
        return "No plants found matching the given search criteria in Firestore database."

    return str(results)


def add_plant_to_inventory(
    name: str,
    light_requirement: str,
    pet_safe: bool,
    price: float,
    care_difficulty: str = "Easy",
    stock_quantity: int = 10,
    description: str = "",
) -> str:
    """Adds or updates a plant item in the Smart Greenhouse catalog stored in Firestore database.

    Args:
        name: Name of the plant.
        light_requirement: Light level required (e.g. 'Low', 'Medium', 'High').
        pet_safe: Boolean indicating whether the plant is pet safe.
        price: Price of the plant in USD.
        care_difficulty: Difficulty level (e.g. 'Easy', 'Moderate', 'Challenging').
        stock_quantity: Quantity available in stock.
        description: Brief description of the plant.

    Returns:
        A confirmation message indicating the plant has been saved to Firestore.
    """
    db = get_firestore_client()
    plant_id = name.lower().replace(" ", "-").replace("(", "").replace(")", "")
    plant_data = {
        "plant_id": plant_id,
        "name": name,
        "light_requirement": light_requirement,
        "pet_safe": pet_safe,
        "price": float(price),
        "care_difficulty": care_difficulty,
        "stock_quantity": int(stock_quantity),
        "description": description,
    }
    db.collection("plants").document(plant_id).set(plant_data)
    return f"Successfully saved plant '{name}' (ID: {plant_id}) to Firestore database."


def calculate_watering_schedule(
    plant_name: str,
    pot_size_inches: float = 6.0,
    temperature_f: float = 70.0,
    humidity_percent: float = 50.0,
    light_level: str = "Medium",
) -> str:
    """Calculates the recommended watering interval (in days) based on plant characteristics and environment.

    Args:
        plant_name: Name of the plant (e.g. 'Pothos', 'Fern', 'Succulent', 'Snake Plant').
        pot_size_inches: Pot diameter in inches. Defaults to 6.0.
        temperature_f: Room temperature in Fahrenheit. Defaults to 70.0.
        humidity_percent: Ambient relative humidity percentage. Defaults to 50.0.
        light_level: Light level ('Low', 'Medium', 'High'). Defaults to 'Medium'.

    Returns:
        A string summarizing the recommended watering interval in days and specific care tip.
    """
    name_lower = plant_name.lower()
    if any(k in name_lower for k in ["succulent", "cactus", "snake", "zz"]):
        base_days = 14
    elif any(k in name_lower for k in ["fern", "calathea", "peace lily"]):
        base_days = 5
    elif any(k in name_lower for k in ["pothos", "palm", "spider"]):
        base_days = 7
    else:
        base_days = 8

    if temperature_f > 75:
        base_days -= 1
    elif temperature_f < 65:
        base_days += 2

    if humidity_percent > 65:
        base_days += 2
    elif humidity_percent < 35:
        base_days -= 1

    if light_level.lower() == "high":
        base_days -= 1
    elif light_level.lower() == "low":
        base_days += 2

    if pot_size_inches <= 4:
        base_days -= 1

    final_days = max(2, base_days)

    return (
        f"Watering Schedule for '{plant_name}' (Pot: {pot_size_inches}\", Temp: {temperature_f}°F, Humidity: {humidity_percent}%, Light: {light_level}):\n"
        f"• Recommended Interval: Water every {final_days} days.\n"
        f"• Pro Tip: Always check top 1-2 inches of soil before watering. If still moist, wait 1-2 more days."
    )


def get_environmental_conditions(location: str) -> str:
    """Fetches real-time ambient temperature (°F), relative humidity (%), and daylight status for a city/location using Open-Meteo API.

    Args:
        location: City name or location (e.g. 'San Francisco', 'New York', 'London').

    Returns:
        A formatted string with real-time temperature, humidity, daylight status, and plant care impact.
    """
    api_key = os.getenv("OPEN_METEO_API_KEY")
    try:
        import requests

        geo_params = {"name": location, "count": 1}
        if api_key:
            geo_params["apikey"] = api_key

        geo_res = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params=geo_params,
            timeout=5,
        ).json()

        results = geo_res.get("results")
        if not results:
            return f"Could not locate '{location}'. Please specify a valid city name."

        loc_data = results[0]
        lat, lon = loc_data["latitude"], loc_data["longitude"]
        city = loc_data.get("name", location)
        country = loc_data.get("country", "")

        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,is_day,precipitation",
            "temperature_unit": "fahrenheit",
        }
        if api_key:
            weather_params["apikey"] = api_key

        w_res = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=weather_params,
            timeout=5,
        ).json()

        current = w_res.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        is_day = "Daytime" if current.get("is_day") == 1 else "Nighttime"

        return (
            f"Real-time Environmental Conditions for {city}, {country}:\n"
            f"• Ambient Temperature: {temp}°F\n"
            f"• Relative Humidity: {humidity}%\n"
            f"• Sunlight/Daylight Status: {is_day}\n"
            f"• Plant Care Impact: Ambient humidity is {humidity}%. Adjust indoor watering frequency accordingly."
        )
    except Exception as e:
        return f"Error fetching real-time environmental conditions for '{location}': {e}"


def geocode_address(address: str) -> str:
    """Converts a street address, city, or landmark into latitude and longitude coordinates using Google Maps Geocoding API.

    Args:
        address: The address, city, or location name to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'San Francisco').

    Returns:
        A string formatted with the location name, formatted address, and coordinates (latitude, longitude).
    """
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not maps_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    try:
        import requests

        res = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": maps_key},
            timeout=5,
        ).json()

        results = res.get("results")
        if not results:
            return f"Geocoding found no coordinates for address: '{address}'."

        first = results[0]
        formatted_addr = first.get("formatted_address", address)
        location = first.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        return (
            f"Geocoding Result for '{address}':\n"
            f"• Formatted Address: {formatted_addr}\n"
            f"• Location Coordinates: latitude={lat}, longitude={lng}"
        )
    except Exception as e:
        return f"Error geocoding address '{address}': {e}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "florist",
    radius_meters: float = 5000.0,
) -> str:
    """Finds nearby places (e.g. plant nurseries, florists, greenhouses, stores) near given latitude/longitude coordinates using Google Places API (New).

    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        place_type: Type of place or category (e.g. 'florist', 'store', 'park', 'shopping_mall'). Defaults to 'florist'.
        radius_meters: Search radius in meters. Defaults to 5000.0.

    Returns:
        A formatted list of nearby places with key fields (name, formatted address, location coordinates).
    """
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not maps_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    try:
        import requests

        headers = {
            "X-Goog-Api-Key": maps_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
            "Content-Type": "application/json",
        }
        body = {
            "includedTypes": [place_type],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": float(latitude), "longitude": float(longitude)},
                    "radius": float(radius_meters),
                }
            },
        }

        res = requests.post(
            "https://places.googleapis.com/v1/places:searchNearby",
            headers=headers,
            json=body,
            timeout=5,
        ).json()

        places = res.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m of ({latitude}, {longitude})."

        results = []
        for p in places[:5]:
            display_name = p.get("displayName", {}).get("text", "Unknown Name")
            formatted_address = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            p_lat = loc.get("latitude")
            p_lng = loc.get("longitude")
            results.append(
                f"• {display_name}\n"
                f"  Address: {formatted_address}\n"
                f"  Location: (lat={p_lat}, lng={p_lng})"
            )

        return f"Nearby Places of type '{place_type}' near ({latitude}, {longitude}):\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error searching nearby places: {e}"


def generate_plant_image(
    item_name: str, prompt_description: str, tool_context: ToolContext = None
) -> str:
    """Generates an image for a plant, greenhouse item, or botanical product using the gemini-3.1-flash-lite-image model in global region, saves it as an artifact, uploads it to public Cloud Storage, and returns its public URL.

    Args:
        item_name: The name of the plant or greenhouse item (e.g. 'Golden Pothos', 'Peace Lily', 'Tropical Greenhouse').
        prompt_description: Detailed visual description for generating the plant/greenhouse image.
        tool_context: Context for saving the generated image artifact in ADK Playground.

    Returns:
        A string containing the public Cloud Storage URL of the generated image.
    """
    try:
        from google import genai
        from google.cloud import storage

        genai_client = genai.Client(
            vertexai=True, project="qwiklabs-gcp-03-3acfd04a83e5", location="global"
        )
        prompt = f"High quality photograph of {item_name}: {prompt_description}"
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        parts = response.candidates[0].content.parts
        inline_part = next((p for p in parts if p.inline_data), None)
        if not inline_part:
            return f"Failed to generate image for '{item_name}': No image payload returned."

        image_bytes = inline_part.inline_data.data
        mime_type = inline_part.inline_data.mime_type or "image/jpeg"
        ext = "png" if "png" in mime_type else "jpg"

        slug = "".join(c if c.isalnum() else "_" for c in item_name.lower())
        filename = f"{slug}_{uuid.uuid4().hex[:8]}.{ext}"

        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        bucket_name = "smart-greenhouse-assets-3acfd04a83e5"
        storage_client = storage.Client(project="qwiklabs-gcp-03-3acfd04a83e5")
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        return (
            f"Successfully generated image for '{item_name}':\n"
            f"• Saved Artifact: {filename}\n"
            f"• Public Image URL: {public_url}"
        )
    except Exception as e:
        return f"Error generating image for '{item_name}': {e}"


def generate_plant_video(
    item_name: str, prompt_description: str, tool_context: ToolContext = None
) -> str:
    """Generates a short video for a plant, greenhouse item, or botanical feature using Google's Omni model (gemini-omni-flash-preview) in global region, saves it as an artifact, uploads it to public Cloud Storage, and returns its public URL.

    Args:
        item_name: The name of the plant or greenhouse item (e.g. 'Monstera Deliciosa', 'Terrarium Mist', 'Tropical Greenhouse Canopy').
        prompt_description: Detailed visual description for generating the plant/greenhouse video.
        tool_context: Context for saving the generated video artifact in ADK Playground.

    Returns:
        A string containing the public Cloud Storage URL of the generated video.
    """
    try:
        import base64
        from google import genai
        from google.cloud import storage

        genai_client = genai.Client(
            vertexai=True, project="qwiklabs-gcp-03-3acfd04a83e5", location="global"
        )
        prompt = f"Short high quality video of {item_name}: {prompt_description}"

        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        video_bytes = None
        mime_type = "video/mp4"

        if hasattr(interaction, "output_video") and interaction.output_video:
            out_v = interaction.output_video
            if hasattr(out_v, "data") and out_v.data:
                video_bytes = out_v.data if isinstance(out_v.data, bytes) else base64.b64decode(out_v.data)
            if hasattr(out_v, "mime_type") and out_v.mime_type:
                mime_type = out_v.mime_type
            elif hasattr(out_v, "uri") and out_v.uri and not video_bytes:
                import requests
                video_bytes = requests.get(out_v.uri).content

        if not video_bytes and hasattr(interaction, "steps") and interaction.steps:
            for step in interaction.steps:
                if hasattr(step, "outputs") and step.outputs:
                    for out in step.outputs:
                        if hasattr(out, "data") and out.data:
                            import base64
                            video_bytes = out.data if isinstance(out.data, bytes) else base64.b64decode(out.data)
                            if hasattr(out, "mime_type") and out.mime_type:
                                mime_type = out.mime_type
                            break

        if not video_bytes and hasattr(interaction, "outputs"):
            for out in interaction.outputs:
                if hasattr(out, "data") and out.data:
                    import base64
                    video_bytes = out.data if isinstance(out.data, bytes) else base64.b64decode(out.data)
                    break

        if not video_bytes:
            return f"Failed to generate video for '{item_name}': No video payload returned by model."

        ext = "mp4"
        if "webm" in mime_type:
            ext = "webm"

        slug = "".join(c if c.isalnum() else "_" for c in item_name.lower())
        filename = f"{slug}_{uuid.uuid4().hex[:8]}.{ext}"

        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        bucket_name = "smart-greenhouse-assets-3acfd04a83e5"
        storage_client = storage.Client(project="qwiklabs-gcp-03-3acfd04a83e5")
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        return (
            f"Successfully generated video for '{item_name}':\n"
            f"• Saved Artifact: {filename}\n"
            f"• Public Video URL: {public_url}"
        )
    except Exception as e:
        return f"Error generating video for '{item_name}': {e}"


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


import threading


class PicklableAgentEngineSandboxCodeExecutor(AgentEngineSandboxCodeExecutor):
    """Picklable wrapper for AgentEngineSandboxCodeExecutor supporting cloudpickle serialization for Agent Engine deployment."""

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_agent_engine_creation_lock"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._agent_engine_creation_lock = threading.Lock()


SANDBOX_RESOURCE_NAME = (
    "projects/qwiklabs-gcp-03-3acfd04a83e5/locations/us-east1/reasoningEngines/2306874351120547840/sandboxEnvironments/7181921991702609920"
)

sandbox_code_executor = PicklableAgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME
)


a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = a2ui_schema_manager.generate_system_prompt(
    role_description=(
        "You are a helpful Smart Greenhouse & Plant Shop assistant. "
        "You remember the user's stated preferences, plant collection, home environmental conditions "
        "(such as light level, humidity, pet presence), and past plant care history from previous conversations, "
        "and use them to personalize your recommendations and care advice. "
        "You can query the Firestore database to check plant inventory catalog using `get_plants`, "
        "add new plants to inventory using `add_plant_to_inventory`, calculate tailored watering schedules "
        "using `calculate_watering_schedule`, fetch real-time ambient temperature and humidity for any location "
        "using `get_environmental_conditions`, geocode address into coordinates using `geocode_address`, "
        "search for nearby florists or plant shops using `find_nearby_places`, generate plant/greenhouse "
        "images using `generate_plant_image`, generate plant/greenhouse videos using `generate_plant_video`, "
        "and execute Python code safely in a sandbox using code execution."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=sandbox_code_executor,
    tools=[
        PreloadMemoryTool(),
        get_plants,
        add_plant_to_inventory,
        calculate_watering_schedule,
        get_environmental_conditions,
        geocode_address,
        find_nearby_places,
        generate_plant_image,
        generate_plant_video,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

