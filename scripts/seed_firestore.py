import os
from google.cloud import firestore
from google.oauth2 import service_account

PROJECT_ID = "qwiklabs-gcp-03-3acfd04a83e5"

SEEDED_PLANTS = [
    {
        "plant_id": "pothos-golden",
        "name": "Golden Pothos",
        "light_requirement": "Low to Medium",
        "pet_safe": False,
        "price": 18.50,
        "care_difficulty": "Easy",
        "watering_frequency": "Every 1-2 weeks",
        "stock_quantity": 15,
        "description": "Hardy trailing vine with variegated green and yellow leaves.",
    },
    {
        "plant_id": "snake-plant",
        "name": "Snake Plant (Sansevieria)",
        "light_requirement": "Low",
        "pet_safe": False,
        "price": 24.00,
        "care_difficulty": "Easy",
        "watering_frequency": "Every 2-3 weeks",
        "stock_quantity": 20,
        "description": "Upright architectural leaves, extremely drought tolerant and low-light friendly.",
    },
    {
        "plant_id": "parlor-palm",
        "name": "Parlor Palm",
        "light_requirement": "Low to Medium",
        "pet_safe": True,
        "price": 28.00,
        "care_difficulty": "Easy",
        "watering_frequency": "Weekly",
        "stock_quantity": 10,
        "description": "Pet-safe compact palm that thrives in indirect light.",
    },
    {
        "plant_id": "spider-plant",
        "name": "Spider Plant",
        "light_requirement": "Medium",
        "pet_safe": True,
        "price": 16.00,
        "care_difficulty": "Easy",
        "watering_frequency": "Weekly",
        "stock_quantity": 12,
        "description": "Pet-safe classic houseplant with arching variegated leaves.",
    },
    {
        "plant_id": "peace-lily",
        "name": "Peace Lily",
        "light_requirement": "Low to Medium",
        "pet_safe": False,
        "price": 26.50,
        "care_difficulty": "Moderate",
        "watering_frequency": "Weekly",
        "stock_quantity": 8,
        "description": "Lush green leaves with elegant white spathes; tells you when it needs water.",
    },
]


def seed_database():
    key_file = "/tmp/antigravity-sa-key.json"
    if os.path.exists(key_file):
        creds = service_account.Credentials.from_service_account_file(key_file)
        db = firestore.Client(project=PROJECT_ID, credentials=creds)
    else:
        db = firestore.Client(project=PROJECT_ID)

    plants_ref = db.collection("plants")
    for plant in SEEDED_PLANTS:
        plants_ref.document(plant["plant_id"]).set(plant)
        print(f"Seeded plant: {plant['name']} ({plant['plant_id']})")
    print(f"Successfully seeded {len(SEEDED_PLANTS)} plants into Firestore collection 'plants'.")


if __name__ == "__main__":
    seed_database()
