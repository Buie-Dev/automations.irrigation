from Controller import run
from mqtt import run_mqtt

if __name__ == "__main__":
    mqtt_client = run_mqtt()
    run(mqtt_client)
