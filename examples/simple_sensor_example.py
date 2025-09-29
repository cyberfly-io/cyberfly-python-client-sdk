"""
Simple Sensor Example with CyberFly SDK

This example shows basic sensor integration:
- Adding a CPU temperature sensor
- Reading sensor data
- Publishing sensor data to the IoT platform
"""

from cyberflySdk import CyberflyClient
import time

# Device credentials
kp = {
    "publicKey": "d04bbd8f403e583248aa461896bd7518113f89b85c98f3d9596bbfbf30df0bcb",
    "secretKey": "a0ec3175c6c80e60bc8ef18bd7b73a631c507b9f0a42c973036c7f96d21b047a"
}

# Initialize client
client = CyberflyClient(
    node_url="https://node.cyberfly.io", 
    device_id="simple-sensor-device", 
    key_pair=kp, 
    network_id="testnet04"
)

# Add a CPU temperature sensor (works on Raspberry Pi)
client.add_sensor(
    sensor_id="cpu_temp", 
    sensor_type="vcgen",
    inputs={},
    alias="CPU Temperature Monitor"
)

print("Added CPU temperature sensor")

# Set up message handler for commands from IoT platform
@client.on_message()
def handle_commands(data):
    print(f"Received command: {data}")
    # Sensor commands are handled automatically by the SDK

# Main loop
print("Starting sensor monitoring...")
print("Send commands from IoT platform with format:")
print('{"sensor_command": {"action": "read", "sensor_id": "cpu_temp"}}')

while True:
    try:
        # Read and publish sensor data every 10 seconds
        reading = client.read_sensor("cpu_temp")
        print(f"CPU Temperature: {reading['data']}")
        
        # Publish to platform
        client.publish_sensor_reading("cpu_temp")
        
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\nStopping...")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)