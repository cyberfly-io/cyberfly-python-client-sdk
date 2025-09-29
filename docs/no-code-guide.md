# No-Code IoT Device Setup Guide

This guide shows how to set up a CyberFly IoT device without writing any code. Everything is managed through the CLI tool and IoT platform UI.

## Quick Start

### 1. Install the SDK
```bash
pip install cyberfly-client-sdk
```

### 2. Set up your device
```bash
cyberfly-device setup
```

### 3. Run your device
```bash
cyberfly-device run
```

That's it! Your IoT device is now running and ready to receive commands from the IoT platform.

## Detailed Setup

### Device Setup
The setup wizard will ask you for:

1. **Device Information**
   - Device ID (unique identifier)
   - Device Name (optional, human-readable)
   - Description (optional)

2. **Network Configuration**
   - Testnet (for testing)
   - Mainnet (for production)

3. **API Credentials**
   - Public Key (from IoT platform)
   - Secret Key (from IoT platform)

4. **Sensor Configuration**
   - Auto-detect sensors
   - Manual configuration
   - Use sample configuration

### Sensor Auto-Detection

The tool can automatically detect common sensors:
- CPU temperature (Raspberry Pi)
- DHT11/DHT22 temperature/humidity sensors
- BMP280 pressure sensors
- PIR motion sensors
- LCD displays
- And more...

### Managing Your Device

#### Check device status
```bash
cyberfly-device status
```

#### Manage configuration
```bash
cyberfly-device config
```

#### View logs
Logs are automatically saved to `~/.cyberfly/device.log`

### Finding Your Sensor IDs

Sensor IDs are created in two places:

1. **During setup** – when you add a sensor manually, the wizard displays the generated `sensor_id` (for example, `dht11_1`). Make a note of it, or provide your own ID when prompted.
2. **In the configuration files** – open `~/.cyberfly/sensor_config.json` to see every sensor definition together with its `sensor_id`, type, inputs, and optional alias.

You can also list them at any time with:

```bash
cyberfly-device status
```

This command prints each configured sensor in the format:

```
sensor_id: sensor_type (enabled/disabled) alias
```

Use the `sensor_id` from this output in the IoT platform payloads (for example, `"sensor_id": "temp_sensor_1"`).

### Providing Sensor Inputs (GPIO pins, I2C addresses, etc.)

Some sensors need extra information—like the GPIO pin number or I2C address—so the SDK knows how to talk to them. You can set those values in three different ways:

1. **During manual setup (`cyberfly-device setup`)** – when you choose the manual option, the wizard prompts for the required inputs based on the sensor type (for example, `GPIO pin number` for a PIR sensor or `I2C address` for an LCD). You can accept the suggested defaults or enter your own values from your wiring diagram.
2. **By editing `sensor_config.json`** – every sensor in `~/.cyberfly/sensor_config.json` has an `inputs` block. Update those fields if you change your wiring later. Example: `"inputs": {"pin_no": 17}`.
3. **From the IoT platform UI (optional)** – if your UI can push configuration updates, send a `{"sensor_command": {"action": "configure", ...}}` payload with the new inputs. The SDK merges those values without restarting the device.

Make sure the `inputs` settings match your hardware wiring—the CLI uses them when it instantiates each sensor.

Whenever sensor settings change through the UI, the device automatically saves the new `sensor_config.json`, so the configuration persists across restarts.

## IoT Platform Commands

Once your device is running, you can send commands from the IoT platform UI:

### Read Sensor Data
```json
{
  "sensor_command": {
    "action": "read"
  }
}
```

### Read Specific Sensor
```json
{
  "sensor_command": {
    "action": "read",
    "sensor_id": "cpu_temp"
  }
}
```

### Get Sensor Status
```json
{
  "sensor_command": {
    "action": "status"
  }
}
```

### Configure or Update Sensors
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

The device applies the change immediately and writes the updated configuration to `~/.cyberfly/sensor_config.json`. Send a follow-up `{"sensor_command": {"action": "status", "sensor_id": "relay_1"}}` or `{"sensor_command": {"action": "list"}}` to confirm the update.

### Control Output Devices

#### Display Text on LCD
```json
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "display_1",
    "params": {
      "execute_action": "display_text",
      "execute_params": {
        "text": "Hello from IoT Platform!",
        "clear": true
      }
    }
  }
}
```

#### Toggle Relay/Output
```json
{
  "sensor_command": {
    "action": "execute",
    "sensor_id": "relay_1", 
    "params": {
      "execute_action": "toggle"
    }
  }
}
```

## Configuration Files

The CLI tool creates configuration files in `~/.cyberfly/`:

- `device_config.json` - Device and network settings
- `sensor_config.json` - Sensor definitions
- `device.log` - Device logs

### Example Sensor Configuration
```json
{
  "sensors": [
    {
      "sensor_id": "temp_sensor_1",
      "sensor_type": "dht11",
      "inputs": {"pin_no": 14},
      "enabled": true,
      "alias": "Living Room Temperature"
    },
    {
      "sensor_id": "pressure_1", 
      "sensor_type": "bmp280",
      "inputs": {"address": "0x77"},
      "enabled": true,
      "alias": "Atmospheric Pressure"
    }
  ]
}
```

## Troubleshooting

### Device won't connect
1. Check your API credentials
2. Verify network settings
3. Check internet connection

### Sensors not detected
1. Make sure sensors are properly connected
2. Check GPIO pin numbers
3. Verify I2C addresses
4. Install required sensor drivers

### View logs for debugging
```bash
tail -f ~/.cyberfly/device.log
```

## Supported Sensors

The SDK supports a wide range of sensors through the sensor library:

**Environmental Sensors:**
- DHT11/DHT22 (temperature, humidity)
- BMP280/BME280 (pressure, temperature, altitude)
- BME680 (gas, humidity, pressure, temperature)
- SHT31-D (temperature, humidity)
- CCS811 (air quality, CO2, TVOC)

**Motion & Proximity:**
- PIR motion sensors
- HC-SR04 ultrasonic distance
- VL53L0X time-of-flight distance

**Input/Output:**
- Digital inputs (buttons, switches)
- Digital outputs (relays, LEDs)
- Analog inputs (via ADS1115)

**Displays:**
- LCD1602 character displays
- HT16K33 7-segment displays

**System:**
- CPU temperature (Raspberry Pi)
- Hall effect sensors
- Water/rain sensors

## Next Steps

1. Set up your hardware with sensors
2. Run the setup wizard
3. Configure sensors in the IoT platform UI
4. Send commands and monitor your device remotely

No programming required!