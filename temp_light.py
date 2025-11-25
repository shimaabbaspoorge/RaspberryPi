import paho.mqtt.client as mqtt
import json
import time
import threading
from sense_hat import SenseHat

BROKER = "u190296b.ala.eu-central-1.emqxsl.com"
PORT = 8883
TOPIC = "gridos/discoverylab/pi/data"
MQTT_USER = "discovery_lab"
MQTT_PASS = "discovery_lab"
TEMP_THRESHOLD = 42

# Select device you want to monitor!
SELECTED_DEVICE = "angela"

#State Tracking
light_state = None
last_light_on_time = 0
is_displaying_message = False
led_lock = threading.Lock()  # To prevent Sense HAT access conflicts

sense = SenseHat()

def show_temperature_message(device, value):
    """Show a scrolling message if temperature exceeds threshold."""
    message = (
        f"The temperature in {device}'s room is too high! ({value})"
        if value > TEMP_THRESHOLD
        else f"The temperature in {device}'s room is normal. ({value})"
    )
    with led_lock:
        global is_displaying_message
        is_displaying_message = True
        sense.show_message(message, scroll_speed=0.05)
        is_displaying_message = False

def on_message(client, userdata, msg):
    """Handle incoming MQTT message."""
    global light_state, last_light_on_time
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        print("Received:", data)
        device = data.get("device")
        parameter = data.get("parameter")
        value = float(data.get("value", 0))

        if device != SELECTED_DEVICE:
            return

        if parameter == "light":
            with led_lock:
                if value == 0:
                    light_state = "off"
                else:
                    light_state = "on"
                    last_light_on_time = time.time()

        elif parameter == "temperature":
            # Show temp warning/normal as a scrolling message
            show_temperature_message(device, value)

    except Exception as e:
        print(f"Error processing message: {e}")

def led_control_loop():
    """Background thread to control LEDs based on light state."""
    global light_state, last_light_on_time, is_displaying_message
    while True:
        with led_lock:
            if not is_displaying_message:
                if light_state == "off":
                    sense.clear(255, 0, 0)  # Red
                elif light_state == "on":
                    # Green for the first 2 seconds
                    if time.time() - last_light_on_time < 2:
                        sense.clear(0, 150, 0)  # Green
                    else:
                        sense.clear()
        time.sleep(0.2)

def main():
    print(f"Subscribed to device: {SELECTED_DEVICE}")

    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC)

    threading.Thread(target=led_control_loop, daemon=True).start()

    client.loop_forever()

if __name__ == "__main__":
    main()
