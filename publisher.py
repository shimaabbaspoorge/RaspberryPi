import paho.mqtt.client as mqtt
import time
import json
from sense_hat import SenseHat

# Configurable Section
MQTT_HOST = "u190296b.ala.eu-central-1.emqxsl.com"
MQTT_PORT = 8883
MQTT_USERNAME = "discovery_lab"
MQTT_PASSWORD = "discovery_lab"
ENV_PUBLISH_INTERVAL = 300  # seconds

SENSOR_TOPICS = {
    "temp": "gridos/shima/temp",
    "hum": "gridos/shima/hum",
    "pre": "gridos/shima/pre",
    "light": "gridos/shima/light"
}

# Sensor Init 
sense = SenseHat()
sense.colour.gain = 64
sense.colour.integration_cycles = 64

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with code: {rc}")

# MQTT Client Init 
mqttc = mqtt.Client()
mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqttc.tls_set()
mqttc.on_connect = on_connect
mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
mqttc.loop_start()  # Async

def get_sensor_data():
    """Return tuple of (temp, hum, press), rounded to 2 decimals."""
    return (
        round(sense.get_temperature(), 2),
        round(sense.get_humidity(), 2),
        round(sense.get_pressure(), 2),
    )

def get_light_status():
    """Return 1 if any RGB component is >=5, else 0."""
    red, green, blue, clear = sense.colour.colour
    return 0 if red < 5 and green < 5 and blue < 5 else 1

def publish_sensor_data(sensor_type, value, timestamp):
    """Prepare and publish sensor data over MQTT."""
    topic = SENSOR_TOPICS[sensor_type]
    payload = {
        "sensor": f"pi_shima_{sensor_type}",
        "time_stamp": timestamp,
        "value": value
    }
    mqttc.publish(topic, json.dumps(payload))
    print(f"Published to {topic}: {payload}")

def main():
    last_env_publish = 0
    prev_light_status = None  # So it always publishes the first time

    try:
        while True:
            now = time.time()
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
            
            if now - last_env_publish >= ENV_PUBLISH_INTERVAL:
                temperature, humidity, pressure = get_sensor_data()
                publish_sensor_data("temp", temperature, timestamp)
                publish_sensor_data("hum", humidity, timestamp)
                publish_sensor_data("pre", pressure, timestamp)
                last_env_publish = now

            # Light sensor: only report change
            current_light = get_light_status()
            if prev_light_status is None or current_light != prev_light_status:
                publish_sensor_data("light", current_light, timestamp)
                prev_light_status = current_light

            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping sensor publisher...")

    finally:
        mqttc.loop_stop()
        mqttc.disconnect()

if __name__ == "__main__":
    main()
