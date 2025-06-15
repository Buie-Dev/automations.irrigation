import json
import uuid
import paho.mqtt.client as mqtt

from config import config
from shared import SCHEDULES, COMPLETED_SCHEDULES, add_replace_schedule, remove_schedule
from Schedule import Schedule

TOPIC_PUB_IRRIGATION_REQUEST = "irrigation/request"
TOPIC_SUB_HEALTH_CHECK_REQUEST = "healthcheck/request"
TOPIC_SUB_SCHEDULE_CREATE = "irrigation/schedule/create"
TOPIC_SUB_SCHEDULE_DELETE = "irrigation/schedule/delete"

TOPIC_PUB_HEALTH_CHECK_RESPONSE = "healthcheck/response"  # Topic to publish to

sub_topics = [
    TOPIC_SUB_HEALTH_CHECK_REQUEST,
    TOPIC_SUB_SCHEDULE_CREATE,
    TOPIC_SUB_SCHEDULE_DELETE,
]

print(
    "CONFIG.MQTT",
    config.MQTT_BROKER,
    config.MQTT_PASSWORD,
    config.MQTT_PORT,
    config.MQTT_USERNAME,
)


# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to broker!")
        for topic in sub_topics:
            client.subscribe(topic)  # Subscribe to a topic after connecting
        # Request initial schedules
    else:
        print(f"Connection failed with code {rc}")


def health_check_response(client):
    payload = {"device": config.DEVICE_NAME}
    publish_message(client, TOPIC_PUB_HEALTH_CHECK_RESPONSE, payload)


def publish_message(client, topic, payload, retain=False):
    try:
        message = json.dumps(payload)
        client.publish(topic, message, retain=retain)
        print(f"Published to {topic}: Retain: {retain}: {message}")
    except Exception as e:
        print(f"Error publishing message: {e}")


def publish_request(client, schedule):
    publish_message(client, TOPIC_PUB_IRRIGATION_REQUEST, schedule.command, False)


# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    # print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    try:
        print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
        if msg.topic == TOPIC_SUB_SCHEDULE_CREATE:
            payload = json.loads(msg.payload.decode())

            schedule = Schedule(
                id=payload["id"],
                monday=payload["monday"],
                tuesday=payload["tuesday"],
                wednesday=payload["wednesday"],
                thursday=payload["thursday"],
                friday=payload["friday"],
                saturday=payload["saturday"],
                sunday=payload["sunday"],
                start_time=payload["start_time"],
                command=payload["command"],
            )

            add_replace_schedule(schedule)

        elif msg.topic == TOPIC_SUB_SCHEDULE_DELETE:
            payload = json.loads(msg.payload.decode())
            schedule_id = payload["id"]
            remove_schedule(schedule_id)

        elif msg.topic == TOPIC_SUB_HEALTH_CHECK_REQUEST:
            health_check_response(client)

    except json.JSONDecodeError:
        print(f"Received non-JSON message: {msg.payload.decode()} on topic {msg.topic}")


def create_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    return client


def run_mqtt():
    try:
        client = create_mqtt_client()
        print(f"Connecting to broker {config.MQTT_BROKER} on port {config.MQTT_PORT}")
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        client.loop_start()
        return client

    finally:
        pass
