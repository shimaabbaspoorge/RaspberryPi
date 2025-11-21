import paho.mqtt.client as mqtt
import json
from sense_hat import SenseHat
import time
import threading

sense = SenseHat()

# MQTT Configuration
BROKER = "u190296b.ala.eu-central-1.emqxsl.com"
PORT = 8883
TOPIC = "gridos/discoverylab/pi/data"
Temperature_threshold = 42
MQTT_USER = "discovery_lab"
MQTT_PASS = "discovery_lab"

# Light and message state tracking
light_state = None
last_light_on_time = 0
is_displaying_message = False

# Lock to prevent LED access conflicts
led_lock = threading.Lock()

# Selected device (set by user)
selected_device = "angela"

def show_temperature_message(device, value):
    global is_displaying_message

    message = (
        f"The temperature in {device}'s room is too high! ({value})"
        if value > Temperature_threshold
        else f"The temperature in {device}'s room is normal. ({value})"
    )

    with led_lock:
        is_displaying_message = True
        sense.show_message(message, scroll_speed=0.05)
        is_displaying_message = False

def on_message(client, userdata, msg):
    global light_state, last_light_on_time, selected_device

    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        print(data)

        device = data.get("device")
        parameter = data.get("parameter")
        value = float(data.get("value", 0))

        # Only process messages for the selected device
        if device != selected_device:
            return

        if parameter == "light":
            with led_lock:
                if value == 0:
                    light_state = "off"
                elif value == 1:
                    light_state = "on"
                    last_light_on_time = time.time()

    except Exception as e:
        print(f"Error processing message: {e}")

def led_control_loop():
    global light_state, last_light_on_time, is_displaying_message

    while True:
        with led_lock:
            if not is_displaying_message:  # Only update LEDs if no message is being shown
                if light_state == "off":
                    sense.clear(255, 0, 0)  # Red
                elif light_state == "on":
                    if time.time() - last_light_on_time < 2:
                        sense.clear(0, 150, 0)  # Green for 2 seconds
                    else:
                        sense.clear()  # Clear after green flash
        time.sleep(0.2)

def main():
    print(f"Subscribed to device: {selected_device}")

    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC)

    # Start LED control loop in a background thread
    threading.Thread(target=led_control_loop, daemon=True).start()

    client.loop_forever()

if __name__ == "__main__":
    main()


