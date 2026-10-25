![CI](https://github.com/Buie-Dev/automations.irrigation/actions/workflows/ci.yml/badge.svg?branch=dev)

# automations.irrigation

Python service that triggers irrigation schedules over MQTT based on day and time.

## Why I built it

I wanted irrigation to run automatically on a schedule without needing the app open. This service polls the API for active schedules on startup, then checks every second whether any schedule matches the current day and time. When one fires, it publishes the schedule's command to MQTT and the irrigation-controller picks it up.

## How it fits

This runs on the home server alongside the API and WebSocket services. It bridges scheduled irrigation between the REST API (where schedules are stored) and the MQTT broker (where the irrigation-controller listens).

- [home-server.infra](https://github.com/Buie-Dev/home-server.infra) runs the Mosquitto MQTT broker and shared infrastructure
- [home-server.api](https://github.com/Buie-Dev/home-server.api) is the Flask REST API that serves schedule data at `GET /irrigations/schedules/automation`
- [irrigation-controller](https://github.com/Buie-Dev/irrigation-controller) subscribes to `irrigation/request` and manages the priority queue
- [controllers.garden](https://github.com/Buie-Dev/controllers.garden) sets GPIO relays on the Raspberry Pi based on zone states
- [devices.flow-sensor](https://github.com/Buie-Dev/devices.flow-sensor) publishes flow sensor pulse data to MQTT
- [home-server.web](https://github.com/Buie-Dev/home-server.web) and [home-server.mobile](https://github.com/Buie-Dev/home-server.mobile) let me create and manage schedules

## Stack

- Python 3.9
- paho-mqtt for MQTT pub/sub
- requests for REST API calls
- pytz for America/Vancouver timezone
- Docker Compose (host network mode)

## Running it locally

### Prerequisites

- Docker and Docker Compose
- Network access to the MQTT broker and the API

### First time setup

1. Clone the repo

```bash
git clone https://github.com/Buie-Dev/automations.irrigation.git
cd automations.irrigation
```

2. Create `.env` from the example and fill in your credentials

```bash
cp .env.example .env
```

3. Start the service

```bash
docker compose up -d
```

## Configuration

| Variable | Purpose |
|---|---|
| `MQTT_USERNAME` | MQTT broker username |
| `MQTT_PASSWORD` | MQTT broker password |
| `MQTT_BROKER` | MQTT broker IP address |
| `MQTT_PORT` | MQTT broker port (1883) |
| `DEVICE_NAME` | Device name used in health check responses |
| `API_URL` | Full URL to the REST API (e.g. `http://192.168.x.x:5001`) |

## Tests

There are no automated tests. CI runs flake8 to lint the Python code. The service can be tested by creating a schedule in the app set to fire within the next minute and watching the Docker logs.

```bash
docker compose logs -f
```

## How I work on it

Changes start as specs in `docs/specs/`. Claude Code implements them on a branch and I review and merge every pull request.
