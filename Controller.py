from time import sleep
from datetime import datetime
import requests
from config import config
from shared import SCHEDULES, COMPLETED_SCHEDULES
from mqtt import publish_request
from Schedule import Schedule


def fetch_schedules():
    """Fetch schedules from the API"""
    try:
        response = requests.get(f"{config.API_URL}/api/schedules")
        response.raise_for_status()  # Raise an exception for bad status codes
        schedules_data = response.json()

        # Clear existing schedules
        SCHEDULES.clear()
        COMPLETED_SCHEDULES.clear()

        # Add each schedule from the response
        for schedule_data in schedules_data:
            schedule = Schedule(
                id=schedule_data["id"],
                name=schedule_data["name"],
                monday=schedule_data["monday"],
                tuesday=schedule_data["tuesday"],
                wednesday=schedule_data["wednesday"],
                thursday=schedule_data["thursday"],
                friday=schedule_data["friday"],
                saturday=schedule_data["saturday"],
                sunday=schedule_data["sunday"],
                start_time=schedule_data["start_time"],
                duration=schedule_data["duration"],
            )
            SCHEDULES.append(schedule)

        print(f"Successfully loaded {len(SCHEDULES)} schedules")
    except requests.RequestException as e:
        print(f"Error fetching schedules: {e}")


def is_correct_day_and_time(schedule) -> bool:
    current_time = datetime.now()
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
                publish_request(mqtt_client, schedule)
                COMPLETED_SCHEDULES.append(schedule)
                SCHEDULES.remove(schedule)
                publish_request(mqtt_client, schedule)
                sleep(0.1)

        for schedule in COMPLETED_SCHEDULES[:]:  # also iterate over a copy here
            if not is_correct_day_and_time(schedule):
                COMPLETED_SCHEDULES.remove(schedule)
                SCHEDULES.append(schedule)

        sleep(1)
