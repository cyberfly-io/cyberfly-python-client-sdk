"""
Example: IoT Sensor Device with CyberFly SDK

This example demonstrates how to use the CyberFly SDK with integrated sensor library
to create an IoT device that can:
1. Read sensor data
2. Respond to commands from the IoT platform
3. Publish sensor readings automatically
4. Control output devices like displays and relays

Prerequisites:
- Raspberry Pi with connected sensors
- Install: pip install cyberfly-client-sdk sensor-library-python
"""

from cyberflySdk import CyberflyClient
from cyberflySdk.sensor_config import SensorConfigManager
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Device credentials - replace with your actual credentials
KEY_PAIR = {
    "publicKey": "d04bbd8f403e583248aa461896bd7518113f89b85c98f3d9596bbfbf30df0bcb",
    "secretKey": "a0ec3175c6c80e60bc8ef18bd7b73a631c507b9f0a42c973036c7f96d21b047a"
}

DEVICE_ID = "sensor-device-01"
NODE_URL = "https://node.cyberfly.io"
NETWORK_ID = "testnet04"


def main():
    # Initialize the CyberFly client
    client = CyberflyClient(
        device_id=DEVICE_ID,
        key_pair=KEY_PAIR,
        node_url=NODE_URL,
        network_id=NETWORK_ID
    )
    
    logger.info(f"Initialized CyberFly client for device: {DEVICE_ID}")
    
    # Option 1: Add sensors programmatically
    setup_sensors_programmatically(client)
    
    # Option 2: Load sensors from configuration file
    # setup_sensors_from_config(client)
    
    # Set up command handler for IoT platform commands
    @client.on_message()
    def handle_iot_commands(command_data):
        """
        Handle commands from the IoT platform UI.
        
        Expected command formats:
        1. Sensor read command:
           {"sensor_command": {"action": "read", "sensor_id": "temp_sensor_1"}}
        
        2. Sensor execute command:
           {"sensor_command": {"action": "execute", "sensor_id": "display_1", 
                              "params": {"execute_action": "display_text", 
                                       "execute_params": {"text": "Hello IoT!"}}}}
        
        3. Sensor status command:
           {"sensor_command": {"action": "status"}}
        """
        logger.info(f"Received command: {command_data}")
        
        # Commands with sensor_command are handled automatically by the SDK
        # This handler is for other types of commands
        if 'custom_action' in command_data:
            handle_custom_action(client, command_data['custom_action'])
    
    # Start the main loop
    try:
        logger.info("Starting IoT sensor device...")
        logger.info("Device is ready to receive commands from IoT platform")
        logger.info("Sensor status:")
        status = client.get_sensor_status()
        logger.info(f"Total sensors: {status['total_sensors']}")
        
        # Example: Periodically publish sensor readings
        last_publish_time = time.time()
        publish_interval = 30  # seconds
        
        while True:
            current_time = time.time()
            
            # Publish all sensor readings every 30 seconds
            if current_time - last_publish_time >= publish_interval:
                try:
                    client.publish_all_sensor_readings()
                    logger.info("Published sensor readings to platform")
                    last_publish_time = current_time
                except Exception as e:
                    logger.error(f"Failed to publish sensor readings: {e}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down IoT sensor device...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")


def setup_sensors_programmatically(client):
    """Set up sensors by adding them programmatically."""
    
    # Example sensors - uncomment and modify based on your hardware setup
    
    # Temperature and humidity sensor (DHT11 on GPIO pin 14)
    # client.add_sensor(
    #     sensor_id="temp_humidity_1",
    #     sensor_type="dht11", 
    #     inputs={"pin_no": 14},
    #     alias="Living Room Climate"
    # )
    
    # Atmospheric pressure sensor (BMP280 via I2C)
    # client.add_sensor(
    #     sensor_id="pressure_1",
    #     sensor_type="bmp280",
    #     inputs={"address": 0x77},
    #     alias="Atmospheric Pressure"
    # )
    
    # Motion sensor (PIR on GPIO pin 4)
    # client.add_sensor(
    #     sensor_id="motion_1",
    #     sensor_type="pir",
    #     inputs={"pin_no": 4},
    #     alias="Motion Detector"
    # )
    
    # LCD display for status (I2C)
    # client.add_sensor(
    #     sensor_id="display_1",
    #     sensor_type="lcd1602",
    #     inputs={"address": 0x27},
    #     alias="Status Display"
    # )
    
    # Digital output for relay control (GPIO pin 18)
    # client.add_sensor(
    #     sensor_id="relay_1",
    #     sensor_type="dout",
    #     inputs={"pin_no": 18, "initial_value": False},
    #     alias="Output Relay"
    # )
    
    # CPU temperature sensor (built-in)
    client.add_sensor(
        sensor_id="cpu_temp",
        sensor_type="vcgen",
        inputs={},
        alias="CPU Temperature"
    )
    
    logger.info("Sensors configured programmatically")


def setup_sensors_from_config(client):
    """Set up sensors by loading from a configuration file."""
    
    # Load configuration from file
    config_manager = SensorConfigManager("sensor_config.json")
    
    if not config_manager.get_sensor_configs():
        logger.warning("No sensor configs found. Creating sample config file...")
        from cyberflySdk.sensor_config import create_sample_config_file
        create_sample_config_file("sensor_config.json")
        logger.info("Sample config created. Please edit 'sensor_config.json' and restart.")
        return
    
    # Load all sensor configurations
    sensor_configs = config_manager.get_sensor_configs()
    loaded_sensors = client.load_sensor_configs(sensor_configs)
    
    logger.info(f"Loaded {len(loaded_sensors)} sensors from configuration file")
    for sensor_id in loaded_sensors:
        logger.info(f"  - {sensor_id}")


def handle_custom_action(client, action_data):
    """Handle custom actions from the IoT platform."""
    
    action_type = action_data.get('type')
    
    if action_type == 'publish_readings':
        # Publish all current sensor readings
        client.publish_all_sensor_readings()
        logger.info("Published sensor readings on demand")
        
    elif action_type == 'display_message':
        # Display a message on the LCD (if available)
        message = action_data.get('message', 'Hello IoT!')
        try:
            result = client.execute_sensor_action('display_1', 'display_text', {'text': message})
            logger.info(f"Displayed message: {message}, result: {result}")
        except Exception as e:
            logger.error(f"Failed to display message: {e}")
            
    elif action_type == 'toggle_relay':
        # Toggle the relay output (if available)
        try:
            result = client.execute_sensor_action('relay_1', 'toggle')
            logger.info(f"Toggled relay, result: {result}")
        except Exception as e:
            logger.error(f"Failed to toggle relay: {e}")
            
    else:
        logger.warning(f"Unknown custom action type: {action_type}")


def test_sensor_commands():
    """
    Test function to demonstrate sensor commands that can be sent from IoT platform.
    This shows the format of commands that the IoT platform UI should send.
    """
    
    # Example commands that can be sent from IoT platform:
    
    # 1. Read specific sensor
    read_command = {
        "sensor_command": {
            "action": "read",
            "sensor_id": "cpu_temp"
        }
    }
    
    # 2. Read all sensors
    read_all_command = {
        "sensor_command": {
            "action": "read"
        }
    }
    
    # 3. Get sensor status
    status_command = {
        "sensor_command": {
            "action": "status"
        }
    }
    
    # 4. Execute action on output sensor (display text)
    execute_display_command = {
        "sensor_command": {
            "action": "execute",
            "sensor_id": "display_1",
            "params": {
                "execute_action": "display_text",
                "execute_params": {
                    "text": "Hello from IoT Platform!",
                    "clear": True
                }
            }
        }
    }
    
    # 5. Execute action on output sensor (toggle relay)
    execute_relay_command = {
        "sensor_command": {
            "action": "execute", 
            "sensor_id": "relay_1",
            "params": {
                "execute_action": "toggle"
            }
        }
    }
    
    print("Example commands for IoT platform:")
    print("1. Read sensor:", read_command)
    print("2. Read all:", read_all_command) 
    print("3. Status:", status_command)
    print("4. Display text:", execute_display_command)
    print("5. Toggle relay:", execute_relay_command)


if __name__ == "__main__":
    # Uncomment to see example commands
    # test_sensor_commands()
    
    main()