# CLAUDE.md

## What this repo is

Python service that polls the API for irrigation schedules on startup, then runs a 1-second loop checking if any schedule's day and time match now (America/Vancouver, within a 2-second window). When a schedule fires, it publishes the schedule's command to `irrigation/request` over MQTT. Also subscribes to MQTT for live schedule management (create, delete, status queries) and responds to health checks.

## Related repos

- [home-server.infra](https://github.com/Buie-Dev/home-server.infra) — Docker Compose infrastructure, runs the Mosquitto MQTT broker this service publishes to
- [home-server.api](https://github.com/Buie-Dev/home-server.api) — Flask REST API, serves `GET /irrigations/schedules/automation`
- [irrigation-controller](https://github.com/Buie-Dev/irrigation-controller) — Raspberry Pi service that subscribes to `irrigation/request` and manages the priority queue
- [controllers.garden](https://github.com/Buie-Dev/controllers.garden) — Raspberry Pi Zero 2W that sets GPIO relays based on zone states
- [devices.flow-sensor](https://github.com/Buie-Dev/devices.flow-sensor) — ESP32 flow sensor that publishes pulse counts to MQTT
- [home-server.web](https://github.com/Buie-Dev/home-server.web) — React web app
- [home-server.mobile](https://github.com/Buie-Dev/home-server.mobile) — React Native mobile app

## Stack

- Python 3.9
- paho-mqtt for MQTT pub/sub
- requests for REST API calls
- pytz for timezone handling
- Docker Compose (host network mode)

## Commands

```bash
docker compose up -d       # Start the service
docker compose logs -f     # Tail logs
docker compose down        # Stop the service
```

## File layout

```
index.py              # Entry point — starts MQTT client, then runs the schedule loop
Controller.py         # Schedule loop — fetches schedules from API, checks day/time, publishes commands
mqtt.py               # MQTT client — subscribes to schedule CRUD and healthcheck topics
Schedule.py           # Schedule data class (id, days, start_time, command)
shared.py             # Shared state — SCHEDULES and COMPLETED_SCHEDULES lists, add/remove helpers
config.py             # Config class reading from environment variables, logging setup
docker-compose.yaml   # Single service, host network, .env file
Dockerfile            # Python 3.9 base, installs requirements
requirements.txt      # paho-mqtt, python-dotenv, requests, pytz, uuid, certifi
.env                  # Credentials and config (gitignored)
.env.example          # Template for .env
```

## MQTT topics

| Direction | Topic | Payload |
|---|---|---|
| Publish | `irrigation/request` | Schedule command object (on time match) |
| Subscribe | `healthcheck/request` | Any message triggers a health response |
| Publish | `healthcheck/response` | `{ device: DEVICE_NAME }` |
| Subscribe | `irrigation/schedule/create` | Add or update a schedule in memory |
| Subscribe | `irrigation/schedule/delete` | Remove a schedule by id |
| Subscribe | `irrigation/schedule/status/request` | Triggers full schedule list response |
| Publish | `irrigation/schedule/status/response` | All schedules currently in memory |

## Standards

- Two long-lived branches: `main` (stable) and `dev` (ongoing work)
- Spec branches named `spec/NNN-short-name`, branched from `dev`, merged back to `dev`
- Commit messages: imperative, sentence case, no AI attribution
- `.gitignore` covers `.env` and `__pycache__/`
- `.env.example` lists every variable with placeholder values
- No license file

## Boundaries

- Never push. Give commands and wait for confirmation.
- Never change app behavior unless a spec says to.
- Never commit `.env`, real IPs, or credentials.
- Never merge a pull request. I review and merge.
- Only write things that are true in the code.

## Workflow

Changes start as specs in `docs/specs/`. Claude Code implements them on a spec branch, and I review and merge every pull request.
