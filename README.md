# cyberfly-client-sdk
A Python client SDK to interact with CyberFly node for IoT devices with integrated sensor support.

**Features:**
- 📡 Pub/Sub messaging with CyberFly network
- 🔧 Integrated sensor library with 20+ sensor types
- 🖥️ No-code CLI tool for easy setup
- 🎮 Remote control via IoT platform UI
- 📊 Automatic sensor data publishing
- ⚙️ Auto-discovery of connected sensors


## Install

```shell
pip install cyberfly-client-sdk
```

## 🚀 No-Code Setup (Recommended)

For users who want to set up an IoT device without programming:

### 1. Install and Setup
```bash
pip install cyberfly-client-sdk
cyberfly-device setup
```

### 2. Run Your Device
```bash
cyberfly-device run
```

### 3. Control from IoT Platform
Send commands from the IoT platform UI:
```json
{"sensor_command": {"action": "read"}}
```

See the [No-Code Guide](docs/no-code-guide.md) for detailed instructions.

### 4. Configure Sensors from the IoT Platform UI
To add a new sensor or update wiring without touching the device, send a configuration payload from the IoT platform:

1. Open the device command composer in the IoT platform UI.
2. Choose the JSON payload mode.
3. Use the `configure` action to supply the sensor details.

Example — create or update a relay on GPIO17:

```json
{
  "sensor_command": {
    "action": "configure",
    "sensor_id": "relay_1",
    "config": {
      "sensor_type": "dout",
      "inputs": {"pin_no": 17},
      "alias": "Main Relay",
      "enabled": true
    }
  }
}
```

The device merges this into its live configuration and writes the updated settings to `~/.cyberfly/sensor_config.json`, so the change persists after reboot. Send a follow-up `{"sensor_command": {"action": "status", "sensor_id": "relay_1"}}` to confirm the update or use `{"sensor_command": {"action": "list"}}` to see every configured sensor.

## 👨‍💻 Developer Usage

## Example

### Basic Messaging

```python
from cyberflySdk import CyberflyClient

kp = {"publicKey": "your_public_key",
      "secretKey": "your_secret_key"}

client = CyberflyClient(
    node_url="https://node.cyberfly.io", 
    device_id="your-device-id",
    key_pair=kp, 
    network_id="testnet04"
)

@client.on_message()
def handle_message(data):
    print(f"Received: {data}")

while True:
    pass
```

### IoT Device with Sensors

```python
from cyberflySdk import CyberflyClient
import time

# Initialize client
client = CyberflyClient(node_url="https://node.cyberfly.io", 
                       device_id="sensor-device-01", 
                       key_pair=kp, network_id="testnet04")

# Add sensors
client.add_sensor("temp_1", "dht11", {"pin_no": 14}, alias="Room Temperature")
client.add_sensor("motion_1", "pir", {"pin_no": 4}, alias="Motion Detector")
client.add_sensor("display_1", "lcd1602", {"address": 0x27}, alias="Status Display")

# Handle commands from IoT platform
@client.on_message()
def handle_iot_commands(data):
    print(f"Command received: {data}")
    # Sensor commands are handled automatically

# Main loop
while True:
    # Publish all sensor readings every 30 seconds
    client.publish_all_sensor_readings()
    time.sleep(30)
```

### Publishing Data

```python
from cyberflySdk import CyberflyClient
import time

kp = {"publicKey": "your_public_key",
      "secretKey": "your_secret_key"}

client = CyberflyClient(
    node_url="https://node.cyberfly.io", 
    device_id="your-device-id",
    key_pair=kp, 
    network_id="testnet04"
)

# Add a sensor
client.add_sensor("temp_sensor", "dht11", {"pin_no": 14})

while True:
    # Manual data publishing
    client.publish("your-topic", {"temperature": 22.5, "humidity": 60})
    
    # Or publish sensor readings
    client.publish_sensor_reading("temp_sensor")
    
    time.sleep(30)
```

## 🔧 Sensor Integration

### Supported Sensors

The SDK includes integrated support for 20+ sensor types:

- **Environmental**: DHT11/22, BMP280, BME280, BME680, SHT31-D, CCS811
- **Motion**: PIR, HC-SR04 ultrasonic, VL53L0X time-of-flight
- **Input/Output**: Digital I/O, Analog (ADS1115), relays
- **Displays**: LCD1602, HT16K33 7-segment
- **System**: CPU temperature, hall effect, water sensors

### Sensor Commands from IoT Platform

Send these commands from your IoT platform UI:

> 💡 **Finding your sensor IDs**
>
> - Run `cyberfly-device status` to print every configured sensor in the format `sensor_id: sensor_type (enabled/disabled) alias`.
> - The same information lives in `~/.cyberfly/sensor_config.json`; open it to copy the IDs directly.
> - When you add sensors manually during `cyberfly-device setup`, you can supply a custom ID or accept the suggested one (e.g., `dht11_1`).
> - The setup wizard also asks for required inputs (like `pin_no` or `address`). You can edit them later in `sensor_config.json` or via a `{"sensor_command": {"action": "configure"}}` payload from the platform UI.
>
> Use those `sensor_id` values in the payloads below.

#### 📖 **Basic Commands**
```json
// Read all sensors
{"sensor_command": {"action": "read"}}

// Read specific sensor  
{"sensor_command": {"action": "read", "sensor_id": "temp_1"}}

// Get sensor status
{"sensor_command": {"action": "status"}}

// List all configured sensors
{"sensor_command": {"action": "list"}}
```

#### 🌡️ **Environmental Sensors**
```json
// DHT11/DHT22 Temperature & Humidity
{"sensor_command": {"action": "read", "sensor_id": "dht_sensor"}}

// BMP280 Pressure & Temperature
{"sensor_command": {"action": "read", "sensor_id": "pressure_sensor"}}

// BME680 Air Quality (temp, humidity, pressure, gas)
{"sensor_command": {"action": "read", "sensor_id": "air_quality"}}

// SHT31-D High Precision Temperature & Humidity
{"sensor_command": {"action": "read", "sensor_id": "precision_temp"}}
```

#### 🚶 **Motion & Distance Sensors**
```json
// PIR Motion Detection
{"sensor_command": {"action": "read", "sensor_id": "motion_detector"}}

// HC-SR04 Ultrasonic Distance
{"sensor_command": {"action": "read", "sensor_id": "distance_sensor"}}

// VL53L0X Time-of-Flight Distance
{"sensor_command": {"action": "read", "sensor_id": "tof_sensor"}}
```

#### 🔌 **Digital I/O Control**
```json
// Read digital input
{"sensor_command": {"action": "read", "sensor_id": "button_1"}}

// Control digital output (LED/Relay)
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "led_1",
    "params": {
      "execute_action": "set_state",
      "execute_params": {"state": 1}
    }
  }
}

// Toggle relay
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "relay_1",
    "params": {"execute_action": "toggle"}
  }
}

// Pulse output (temporary activation)
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "buzzer_1",
    "params": {
      "execute_action": "pulse",
      "execute_params": {"duration": 2000}
    }
  }
}
```

#### 📊 **Analog Sensors (ADS1115)**
```json
// Read analog value
{"sensor_command": {"action": "read", "sensor_id": "analog_sensor"}}

// Read specific channel
{
  "sensor_command": {
    "action": "read",
    "sensor_id": "ads1115_1",
    "params": {"channel": 0}
  }
}
```

#### 🖥️ **Display Control**
```json
// LCD1602 Display Control
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "lcd_display",
    "params": {
      "execute_action": "display_text",
      "execute_params": {
        "text": "Hello IoT!",
        "line": 0,
        "position": 0
      }
    }
  }
}

// Clear LCD display
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "lcd_display",
    "params": {"execute_action": "clear"}
  }
}

// HT16K33 7-Segment Display
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "seven_segment",
    "params": {
      "execute_action": "display_number",
      "execute_params": {"number": 1234}
    }
  }
}

// Set display brightness
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "seven_segment",
    "params": {
      "execute_action": "set_brightness",
      "execute_params": {"brightness": 8}
    }
  }
}
```

#### 🔧 **System Sensors**
```json
// CPU Temperature
{"sensor_command": {"action": "read", "sensor_id": "cpu_temp"}}

// Hall Effect Sensor
{"sensor_command": {"action": "read", "sensor_id": "hall_sensor"}}

// Water Level Sensor
{"sensor_command": {"action": "read", "sensor_id": "water_level"}}
```

#### 🔄 **Batch Operations**
```json
// Read multiple specific sensors
{
  "sensor_command": {
    "action": "read_multiple",
    "sensor_ids": ["temp_1", "humidity_1", "motion_1"]
  }
}

// Execute multiple commands
{
  "sensor_command": {
    "action": "batch_execute",
    "commands": [
      {
        "sensor_id": "led_1",
        "execute_action": "set_state",
        "execute_params": {"state": 1}
      },
      {
        "sensor_id": "lcd_display",
        "execute_action": "display_text",
        "execute_params": {"text": "System ON"}
      }
    ]
  }
}
```

#### ⚙️ **Configuration Commands**
```json
// Update sensor configuration
{
  "sensor_command": {
    "action": "configure",
    "sensor_id": "temp_sensor",
    "config": {
      "reading_interval": 30,
      "auto_publish": true,
      "threshold_alerts": {
        "max_temp": 35.0,
        "min_temp": 10.0
      }
    }
  }
}

// Enable/disable sensor
{
  "sensor_command": {
    "action": "configure",
    "sensor_id": "motion_detector",
    "config": {"enabled": false}
  }
}
```

## 📁 Examples

- [No-Code Setup Guide](docs/no-code-guide.md)
- [IoT Sensor Device](examples/iot_sensor_device.py)
- [Simple Sensor Example](examples/simple_sensor_example.py)
- [Local Sensor Testing](examples/test_sensors_local.py)

## 🛠️ CLI Commands

```bash
# Setup device interactively
cyberfly-device setup

# Run device
cyberfly-device run

# Check status
cyberfly-device status

# Manage configuration
cyberfly-device config
```
