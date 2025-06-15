import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MQTT_PORT = int(os.getenv("MQTT_PORT"))
    DEVICE_NAME = os.getenv("DEVICE_NAME")
    API_URL = os.getenv(
        "API_URL", "http://localhost:5001"
    )  # Default to localhost if not set


config = Config()
