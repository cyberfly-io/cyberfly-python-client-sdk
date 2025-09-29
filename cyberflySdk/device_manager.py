#!/usr/bin/env python3
"""
CyberFly IoT Device Manager

No-code tool for setting up and managing IoT devices with sensors.
End users can configure everything through CLI prompts and IoT platform UI.

Usage:
    cyberfly-device setup    # Interactive device setup
    cyberfly-device run      # Run the IoT device
    cyberfly-device status   # Check device status
    cyberfly-device config   # Manage configuration
"""

import argparse
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

# Try to import the SDK components
try:
    from cyberflySdk import CyberflyClient
    from cyberflySdk.sensor_config import SensorConfigManager, create_sample_config_file
    from cyberflySdk.sensors import SensorManager, SensorConfig
except ImportError as e:
    print(f"Error: Cannot import CyberFly SDK. Please install with: pip install cyberfly-client-sdk")
    print(f"Details: {e}")
    sys.exit(1)


class CyberFlyDeviceManager:
    """No-code device manager for CyberFly IoT devices."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".cyberfly"
        self.device_config_file = self.config_dir / "device_config.json"
        self.sensor_config_file = self.config_dir / "sensor_config.json"
        self.log_file = self.config_dir / "device.log"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Set up logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Configure logging for the device."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def setup_device(self):
        """Interactive device setup wizard."""
        print("🚀 CyberFly IoT Device Setup")
        print("=" * 40)
        
        # Check if device is already configured
        if self.device_config_file.exists():
            print("Device configuration found.")
            overwrite = input("Do you want to reconfigure? (y/N): ").lower().strip()
            if overwrite != 'y':
                print("Setup cancelled.")
                return
        
        device_config = {}
        
        # Get device information
        print("\n📱 Device Information")
        device_config['device_id'] = input("Enter Device ID: ").strip()
        device_config['device_name'] = input("Enter Device Name (optional): ").strip()
        device_config['description'] = input("Enter Device Description (optional): ").strip()
        
        # Get network settings
        print("\n🌐 Network Configuration")
        print("Network options:")
        print("1. Testnet (recommended for testing)")
        print("2. Mainnet (for production)")
        network_choice = input("Select network (1/2): ").strip()
        
        if network_choice == "1":
            device_config['network_id'] = "testnet04"
            device_config['node_url'] = "https://node.cyberfly.io"
        else:
            device_config['network_id'] = "mainnet01"
            device_config['node_url'] = "https://node.cyberfly.io"
        
        # Get API credentials
        print("\n🔐 API Credentials")
        print("You can get these from the CyberFly IoT platform:")
        device_config['public_key'] = input("Enter Public Key: ").strip()
        device_config['secret_key'] = input("Enter Secret Key: ").strip()
        
        # Save device configuration
        with open(self.device_config_file, 'w') as f:
            json.dump(device_config, f, indent=2)
        
        print(f"\n✅ Device configuration saved to {self.device_config_file}")
        
        # Setup sensors
        self.setup_sensors()
        
        print("\n🎉 Setup Complete!")
        print("Next steps:")
        print("1. Run 'cyberfly-device run' to start your IoT device")
        print("2. Configure sensors in the IoT platform UI")
        print("3. Send commands to your device from the platform")
    
    def setup_sensors(self):
        """Interactive sensor setup."""
        print("\n🔧 Sensor Configuration")
        
        # Check if sensor config exists
        if self.sensor_config_file.exists():
            print("Sensor configuration found.")
            overwrite = input("Do you want to reconfigure sensors? (y/N): ").lower().strip()
            if overwrite != 'y':
                return
        
        print("Setting up sensors...")
        print("1. Auto-detect sensors")
        print("2. Manual configuration")
        print("3. Use sample configuration")
        
        choice = input("Select option (1/2/3): ").strip()
        
        if choice == "1":
            self.auto_detect_sensors()
        elif choice == "2":
            self.manual_sensor_setup()
        else:
            self.create_sample_sensor_config()
    
    def auto_detect_sensors(self):
        """Attempt to auto-detect available sensors."""
        print("\n🔍 Auto-detecting sensors...")
        
        detected_sensors = []
        
        # Try to detect common sensors
        sensor_types_to_try = [
            ("vcgen", {}, "CPU Temperature (Raspberry Pi)"),
            ("dht11", {"pin_no": 14}, "DHT11 Temperature/Humidity (GPIO 14)"),
            ("bmp280", {"address": 0x77}, "BMP280 Pressure Sensor (I2C 0x77)"),
            ("pir", {"pin_no": 4}, "PIR Motion Sensor (GPIO 4)"),
            ("lcd1602", {"address": 0x27}, "LCD Display (I2C 0x27)"),
        ]
        
        for sensor_type, inputs, description in sensor_types_to_try:
            try:
                # Try to create sensor to test if it's available
                from sensor_lib.main import create_sensor
                sensor = create_sensor(sensor_type, inputs)
                
                # If successful, add to detected sensors
                sensor_id = f"{sensor_type}_auto"
                detected_sensors.append({
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "inputs": inputs,
                    "description": description,
                    "enabled": True
                })
                print(f"✅ Detected: {description}")
                
            except Exception:
                print(f"❌ Not found: {description}")
        
        if detected_sensors:
            config = {"sensors": detected_sensors}
            with open(self.sensor_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n✅ Auto-detected {len(detected_sensors)} sensors")
        else:
            print("\n⚠️  No sensors auto-detected. Creating sample configuration...")
            self.create_sample_sensor_config()
    
    def manual_sensor_setup(self):
        """Manual sensor configuration."""
        print("\n✏️  Manual Sensor Setup")
        print("You can add sensors one by one. Press Enter with empty sensor type to finish.")
        
        sensors = []
        
        while True:
            print(f"\n--- Sensor #{len(sensors) + 1} ---")
            sensor_type = input("Sensor type (e.g., dht11, bmp280, pir): ").strip()
            
            if not sensor_type:
                break
            
            sensor_id = input(f"Sensor ID (default: {sensor_type}_1): ").strip()
            if not sensor_id:
                sensor_id = f"{sensor_type}_1"
            
            # Get inputs based on sensor type
            inputs = {}
            if sensor_type in ["dht11", "pir", "din", "dout"]:
                pin_no = input("GPIO pin number: ").strip()
                if pin_no.isdigit():
                    inputs["pin_no"] = int(pin_no)
            elif sensor_type in ["bmp280", "bme280", "bh1750", "lcd1602"]:
                address = input("I2C address (e.g., 0x77, 0x27): ").strip()
                if address.startswith("0x"):
                    inputs["address"] = int(address, 16)
            
            description = input("Description (optional): ").strip()
            
            sensor_config = {
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "inputs": inputs,
                "enabled": True
            }
            
            if description:
                sensor_config["alias"] = description
            
            sensors.append(sensor_config)
            print(f"✅ Added {sensor_id}")
        
        config = {"sensors": sensors}
        with open(self.sensor_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Configured {len(sensors)} sensors")
    
    def create_sample_sensor_config(self):
        """Create sample sensor configuration."""
        print("\n📝 Creating sample sensor configuration...")
        
        sample_config = {
            "sensors": [
                {
                    "sensor_id": "cpu_temp",
                    "sensor_type": "vcgen",
                    "inputs": {},
                    "enabled": True,
                    "alias": "CPU Temperature Monitor"
                }
            ]
        }
        
        with open(self.sensor_config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"✅ Sample configuration created at {self.sensor_config_file}")
        print("You can edit this file or use the IoT platform UI to configure sensors.")
    
    def run_device(self):
        """Run the IoT device."""
        print("🚀 Starting CyberFly IoT Device...")
        
        # Load device configuration
        if not self.device_config_file.exists():
            print("❌ Device not configured. Run 'cyberfly-device setup' first.")
            return
        
        with open(self.device_config_file, 'r') as f:
            device_config = json.load(f)
        
        # Create key pair
        key_pair = {
            "publicKey": device_config['public_key'],
            "secretKey": device_config['secret_key']
        }
        
        # Initialize client
        client = CyberflyClient(
            device_id=device_config['device_id'],
            key_pair=key_pair,
            node_url=device_config['node_url'],
            network_id=device_config['network_id']
        )
        
        self.logger.info(f"Device {device_config['device_id']} connected to {device_config['network_id']}")
        
        # Load sensors if configuration exists
        if self.sensor_config_file.exists():
            with open(self.sensor_config_file, 'r') as f:
                sensor_config = json.load(f)
            
            sensors = sensor_config.get('sensors', [])
            loaded_sensors = client.load_sensor_configs(sensors)
            self.logger.info(f"Loaded {len(loaded_sensors)} sensors: {loaded_sensors}")
        else:
            self.logger.warning("No sensor configuration found")

        def save_sensor_configs(configs: List[Dict[str, Any]]):
            try:
                payload = {"sensors": configs}
                with open(self.sensor_config_file, 'w') as f:
                    json.dump(payload, f, indent=2)
                self.logger.info("Sensor configuration updated from IoT platform")
            except Exception as exc:
                self.logger.error(f"Failed to persist sensor configuration: {exc}")

        client.sensor_manager.set_config_save_hook(save_sensor_configs)
        
        # Set up command handler
        @client.on_message()
        def handle_commands(command_data):
            self.logger.info(f"Received command: {command_data}")
            # Sensor commands are handled automatically by the SDK
        
        print("✅ Device is running and ready to receive commands")
        print("📊 Send commands from the IoT platform UI to:")
        print(f"   - Read sensor data")
        print(f"   - Control output devices")
        print(f"   - Get device status")
        print("\n📋 Available sensor commands:")
        print('   {"sensor_command": {"action": "read"}}')
        print('   {"sensor_command": {"action": "status"}}')
        print('   {"sensor_command": {"action": "read", "sensor_id": "cpu_temp"}}')
        print("\n🛑 Press Ctrl+C to stop the device")
        
        # Main loop with periodic sensor publishing
        try:
            last_publish = time.time()
            publish_interval = 60  # Publish every minute
            
            while True:
                current_time = time.time()
                
                # Publish sensor readings periodically
                if current_time - last_publish >= publish_interval:
                    try:
                        client.publish_all_sensor_readings()
                        self.logger.info("Published sensor readings")
                        last_publish = current_time
                    except Exception as e:
                        self.logger.error(f"Failed to publish readings: {e}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping device...")
            self.logger.info("Device stopped by user")
    
    def show_status(self):
        """Show device and sensor status."""
        print("📊 CyberFly Device Status")
        print("=" * 30)
        
        # Device configuration status
        if self.device_config_file.exists():
            with open(self.device_config_file, 'r') as f:
                device_config = json.load(f)
            
            print("✅ Device Configuration:")
            print(f"   Device ID: {device_config['device_id']}")
            print(f"   Network: {device_config['network_id']}")
            print(f"   Node URL: {device_config['node_url']}")
        else:
            print("❌ Device not configured")
        
        # Sensor configuration status
        if self.sensor_config_file.exists():
            with open(self.sensor_config_file, 'r') as f:
                sensor_config = json.load(f)
            
            sensors = sensor_config.get('sensors', [])
            print(f"\n✅ Sensor Configuration ({len(sensors)} sensors):")
            for sensor in sensors:
                status = "enabled" if sensor.get('enabled', True) else "disabled"
                alias = sensor.get('alias', '')
                print(f"   {sensor['sensor_id']}: {sensor['sensor_type']} ({status}) {alias}")
        else:
            print("\n❌ No sensors configured")
        
        # Log file status
        if self.log_file.exists():
            size = self.log_file.stat().st_size
            print(f"\n📋 Log file: {self.log_file} ({size} bytes)")
        
    def manage_config(self):
        """Configuration management menu."""
        while True:
            print("\n⚙️  Configuration Management")
            print("1. View device config")
            print("2. View sensor config") 
            print("3. Edit sensor config")
            print("4. Reset all configuration")
            print("5. Back to main menu")
            
            choice = input("Select option (1-5): ").strip()
            
            if choice == "1":
                self.view_device_config()
            elif choice == "2":
                self.view_sensor_config()
            elif choice == "3":
                self.edit_sensor_config()
            elif choice == "4":
                self.reset_config()
            elif choice == "5":
                break
            else:
                print("Invalid option")
    
    def view_device_config(self):
        """View device configuration."""
        if self.device_config_file.exists():
            with open(self.device_config_file, 'r') as f:
                config = json.load(f)
            print("\n📱 Device Configuration:")
            print(json.dumps(config, indent=2))
        else:
            print("❌ No device configuration found")
    
    def view_sensor_config(self):
        """View sensor configuration."""
        if self.sensor_config_file.exists():
            with open(self.sensor_config_file, 'r') as f:
                config = json.load(f)
            print("\n🔧 Sensor Configuration:")
            print(json.dumps(config, indent=2))
        else:
            print("❌ No sensor configuration found")
    
    def edit_sensor_config(self):
        """Edit sensor configuration."""
        print("\n✏️  Edit Sensor Configuration")
        print("Opening sensor config file for editing...")
        print(f"File location: {self.sensor_config_file}")
        
        if not self.sensor_config_file.exists():
            self.create_sample_sensor_config()
        
        # Try to open with default editor
        import subprocess
        try:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.call(['open', str(self.sensor_config_file)])
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.call(['xdg-open', str(self.sensor_config_file)])
            elif sys.platform.startswith('win'):  # Windows
                subprocess.call(['notepad', str(self.sensor_config_file)])
            else:
                print(f"Please edit the file manually: {self.sensor_config_file}")
        except Exception:
            print(f"Please edit the file manually: {self.sensor_config_file}")
    
    def reset_config(self):
        """Reset all configuration."""
        confirm = input("⚠️  This will delete all configuration. Are you sure? (y/N): ").lower().strip()
        if confirm == 'y':
            for config_file in [self.device_config_file, self.sensor_config_file]:
                if config_file.exists():
                    config_file.unlink()
            print("✅ All configuration reset")
        else:
            print("Reset cancelled")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CyberFly IoT Device Manager - No-code tool for IoT devices"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    subparsers.add_parser('setup', help='Interactive device setup')
    
    # Run command
    subparsers.add_parser('run', help='Run the IoT device')
    
    # Status command
    subparsers.add_parser('status', help='Show device status')
    
    # Config command
    subparsers.add_parser('config', help='Manage configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = CyberFlyDeviceManager()
    
    if args.command == 'setup':
        manager.setup_device()
    elif args.command == 'run':
        manager.run_device()
    elif args.command == 'status':
        manager.show_status()
    elif args.command == 'config':
        manager.manage_config()


if __name__ == "__main__":
    main()