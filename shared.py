SCHEDULES = []
COMPLETED_SCHEDULES = []


def remove_schedule(schedule_id):
    SCHEDULES[:] = [item for item in SCHEDULES if item.id != schedule_id]
    COMPLETED_SCHEDULES[:] = [
        item for item in COMPLETED_SCHEDULES if item.id != schedule_id
    ]


def add_replace_schedule(schedule):
    remove_schedule(schedule.id)
    SCHEDULES.append(schedule)
