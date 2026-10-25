import json
import logging
import time
import paho.mqtt.client as mqtt

from config import config
from shared import SCHEDULES, COMPLETED_SCHEDULES, add_replace_schedule, remove_schedule
from Schedule import Schedule

logger = logging.getLogger(__name__)

TOPIC_PUB_IRRIGATION_REQUEST = "irrigation/request"
TOPIC_SUB_HEALTH_CHECK_REQUEST = "healthcheck/request"
TOPIC_SUB_SCHEDULE_CREATE = "irrigation/schedule/create"
TOPIC_SUB_SCHEDULE_DELETE = "irrigation/schedule/delete"
TOPIC_SUB_SCHEDULE_STATUS_REQUEST = "irrigation/schedule/status/request"

TOPIC_PUB_HEALTH_CHECK_RESPONSE = "healthcheck/response"  # Topic to publish to
TOPIC_PUB_SCHEDULE_STATUS_RESPONSE = "irrigation/schedule/status/response"

sub_topics = [
    TOPIC_SUB_HEALTH_CHECK_REQUEST,
    TOPIC_SUB_SCHEDULE_CREATE,
    TOPIC_SUB_SCHEDULE_DELETE,
    TOPIC_SUB_SCHEDULE_STATUS_REQUEST,
]

logger.info("CONFIG.MQTT %s %s %s", config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USERNAME)


# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected successfully to broker!")
        for topic in sub_topics:
            client.subscribe(topic)
    else:
        logger.error("Connection failed with code %s", rc)


def health_check_response(client):
    payload = {"device": config.DEVICE_NAME}
    publish_message(client, TOPIC_PUB_HEALTH_CHECK_RESPONSE, payload)


def publish_message(client, topic, payload, retain=False):
    try:
        message = json.dumps(payload)
        client.publish(topic, message, retain=retain)
        logger.info("Published to %s: Retain: %s: %s", topic, retain, message)
    except Exception as e:
        logger.error("Error publishing message: %s", e)


def publish_request(client, schedule):
    publish_message(client, TOPIC_PUB_IRRIGATION_REQUEST, schedule.command, False)


# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    # print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    try:
        logger.info("Received message: %s on topic %s", msg.payload.decode(), msg.topic)
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

            logger.info(
                "Schedule created/updated: id=%s start_time=%s command=%s",
                schedule.id, schedule.start_time, schedule.command,
            )
            add_replace_schedule(schedule)

        elif msg.topic == TOPIC_SUB_SCHEDULE_DELETE:
            payload = json.loads(msg.payload.decode())
            schedule_id = payload["id"]
            logger.info("Schedule deleted: id=%s", schedule_id)
            remove_schedule(schedule_id)

        elif msg.topic == TOPIC_SUB_HEALTH_CHECK_REQUEST:
            health_check_response(client)

        elif msg.topic == TOPIC_SUB_SCHEDULE_STATUS_REQUEST:
            all_schedules = SCHEDULES + COMPLETED_SCHEDULES
            payload = {
                "schedules": [
                    {
                        "id": s.id,
                        "monday": s.monday,
                        "tuesday": s.tuesday,
                        "wednesday": s.wednesday,
                        "thursday": s.thursday,
                        "friday": s.friday,
                        "saturday": s.saturday,
                        "sunday": s.sunday,
                        "start_time": s.start_time,
                        "command": s.command,
                    }
                    for s in all_schedules
                ]
            }
            publish_message(client, TOPIC_PUB_SCHEDULE_STATUS_RESPONSE, payload)

    except json.JSONDecodeError:
        logger.warning("Received non-JSON message: %s on topic %s", msg.payload.decode(), msg.topic)


def create_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    return client


def run_mqtt():
    client = create_mqtt_client()
    while True:
        try:
            logger.info("Connecting to broker %s:%s...", config.MQTT_BROKER, config.MQTT_PORT)
            client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
            break
        except Exception as e:
            logger.error("MQTT connect failed: %s — retrying in 5s", e)
            time.sleep(5)
    client.loop_start()
    return client
