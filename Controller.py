from time import sleep
from datetime import datetime
import logging
import requests
import pytz
from config import config
from shared import SCHEDULES, COMPLETED_SCHEDULES
from mqtt import publish_request
from Schedule import Schedule

logger = logging.getLogger(__name__)

FETCH_RETRY_DELAY = 5  # seconds between retries


def fetch_schedules():
    """Fetch schedules from the API, retrying indefinitely until successful"""
    while True:
        try:
            response = requests.get(f"{config.API_URL}/irrigations/schedules/automation", timeout=10)
            response.raise_for_status()
            schedules_data = response.json()

            completed_ids = {schedule.id for schedule in COMPLETED_SCHEDULES}

            SCHEDULES.clear()
            COMPLETED_SCHEDULES.clear()

            for schedule_data in schedules_data:
                schedule = Schedule(
                    id=schedule_data["id"],
                    monday=schedule_data["monday"],
                    tuesday=schedule_data["tuesday"],
                    wednesday=schedule_data["wednesday"],
                    thursday=schedule_data["thursday"],
                    friday=schedule_data["friday"],
                    saturday=schedule_data["saturday"],
                    sunday=schedule_data["sunday"],
                    start_time=schedule_data["start_time"],
                    command=schedule_data["command"],
                )
                if schedule.id in completed_ids:
                    COMPLETED_SCHEDULES.append(schedule)
                else:
                    SCHEDULES.append(schedule)

            logger.info("Fetched %d schedules", len(schedules_data))
            return

        except requests.RequestException as e:
            logger.error("Error fetching schedules: %s — retrying in %ds", e, FETCH_RETRY_DELAY)
            sleep(FETCH_RETRY_DELAY)


def is_correct_day_and_time(schedule) -> bool:
    pacific_tz = pytz.timezone("America/Vancouver")
    current_time = datetime.now(pacific_tz)
    current_day = current_time.strftime("%A").lower()

    # Check if the schedule is enabled for the current day
    if not getattr(schedule, current_day, False):
        return False

    # Parse the schedule time (format "HH:MM")
    schedule_hours, schedule_minutes = map(int, schedule.start_time.split(":"))

    # Get current hours and minutes
    current_hours = current_time.hour
    current_minutes = current_time.minute
    current_seconds = current_time.second

    # First check if hours and minutes match
    if current_hours != schedule_hours or current_minutes != schedule_minutes:
        return False

    # If we get here, hours and minutes match, now check if we're within 2 seconds
    return current_seconds <= 2


def run(mqtt_client) -> None:
    # Fetch initial schedules when starting up
    fetch_schedules()

    while True:
        for schedule in SCHEDULES[:]:  # iterate over a shallow copy
            if is_correct_day_and_time(schedule):
                SCHEDULES.remove(schedule)
                COMPLETED_SCHEDULES.append(schedule)
                publish_request(mqtt_client, schedule)

                sleep(0.1)

        for schedule in COMPLETED_SCHEDULES[:]:  # also iterate over a copy here
            if not is_correct_day_and_time(schedule):
                COMPLETED_SCHEDULES.remove(schedule)
                SCHEDULES.append(schedule)

        sleep(1)
