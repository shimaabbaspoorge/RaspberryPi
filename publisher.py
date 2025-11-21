import paho.mqtt.client as mqtt
import time
import json
from sense_hat import SenseHat

sense = SenseHat()

# MQTT Config
MQTT_HOST = "u190296b.ala.eu-central-1.emqxsl.com"
MQTT_PORT = 8883
USERNAME: "discovery_lab"
PASSWORD: "discovery_lab"

#sesor topics
TOPICS = {
    "temp": "gridos/shima/temp",
    "hum": "gridos/shima/hum",
    "pre": "gridos/shima/pre",
    "light": "gridos/shima/light",
    "mov": "gridos/shima/mov"
    }

#colour sensor setting
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)


#colour sensor setting
sense.colour.gain = 64
sense.colour.integration_cycles = 64

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with code:", rc)

# Initiate MQTT client
mqttc = mqtt.Client()
mqttc.username_pw_set("discovery_lab", "discovery_lab")
mqttc.tls_set()
mqttc.on_connect = on_connect
mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
mqttc.loop_start()  # Start loop in the background

# Helper function to get sensor data
def get_sensor_data():
    t = round(sense.get_temperature(), 2)
    h = round(sense.get_humidity(), 2)
    p = round(sense.get_pressure(), 2)
    return t, h, p


def get_light_status():
        red, green, blue, clear = sense.colour.colour
        #print(f"DEBUG light: R={red}, G={green}, B={blue}, C={clear}")
        if red < 5 and green < 5 and blue < 5:
            light_state = 0
        else:
            light_state = 1

        return light_state
# Motion sensor
def detect_movement(threshold=0.5):
    accel = sense.get_accelerometer_raw()
    x, y, z = accel['x'], accel['y'], accel['z']
    magnitude = (x**2 + y**2 + z**2) ** 0.5
    #print(f"DEBUG accel: x={x:.3f}, y={y:.3f}, z={z:.3f}, |magnitude|={magnitude:.3f}")
    return abs(magnitude - 1.0) > threshold

# Track previous states
prev_light_status = 1
prev_movement_state = 0


try:
    last_env_publish = 0
    ENV_INTERVAL = 300
    
    while True:
        now = time.time()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        
        if now - last_env_publish >= ENV_INTERVAL:
            temperature, humidity, pressure = get_sensor_data()
            # Prepare and send JSON messages
            payload_temp = json.dumps({
                "sensor": "pi_shima_temp",
                "time_stamp": timestamp,
                "value": temperature
            },indent=2)
            mqttc.publish("gridos/shima/temp", payload_temp)
            print(json.dumps(json.loads(payload_temp)))

            payload_hum = json.dumps({
                "sensor": "pi_shima_hum",
                "time_stamp": timestamp,
                "value": humidity
            }, indent=2)
            mqttc.publish("gridos/shima/hum", payload_hum)
            print(json.dumps(json.loads(payload_hum)))

            payload_pres = json.dumps({
                "sensor": "pi_shima_pre",
                "time_stamp": timestamp,
                "value": pressure
            }, indent=2)
            mqttc.publish("gridos/shima/pre", payload_pres)
            print(json.dumps(json.loads(payload_pres)))
            
            last_env_publish = now
            
        # Check light status
        current_light = get_light_status()
        if current_light is not None and current_light != prev_light_status:
            prev_light_status = current_light
            payload_light = json.dumps({
                "sensor": "pi_shima_light",
                "time_stamp": timestamp,
                "value": current_light
            }, indent=2)
            mqttc.publish("gridos/shima/light", payload_light)
            print(json.dumps(json.loads(payload_light)))

        # Check movement
        moved = detect_movement()
        if moved != prev_movement_state:
            prev_movement_state = moved
            motion_state = 1 if moved else 0
            payload_motion = json.dumps({
                "sensor": "pi_shima_mov",
                "time_stamp": timestamp,
                "value": motion_state
            }, indent=2)
            mqttc.publish("gridos/shima/mov", payload_motion)
            print(json.dumps(json.loads(payload_motion)))
            
            
except KeyboardInterrupt:
    print("Stopping motion/light publisher...")

finally:
    mqttc.loop_stop()
    mqttc.disconnect()
    
    
    
    
    

