"""
Configuration management for CyberFly SDK with sensor support.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class SensorConfigManager:
    """
    Manages sensor configurations for CyberFly devices.
    Supports loading from files, environment variables, or direct configuration.
    """
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.configs: Dict[str, Any] = {}
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load sensor configurations from a JSON file.
        
        Expected format:
        {
            "sensors": [
                {
                    "sensor_id": "temp_sensor_1",
                    "sensor_type": "dht11",
                    "inputs": {"pin_no": 14},
                    "enabled": true,
                    "alias": "Living Room Temperature"
                },
                ...
            ]
        }
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.configs = data
            return True
            
        except Exception as e:
            print(f"Failed to load config from {file_path}: {e}")
            return False
    
    def save_to_file(self, file_path: str = None) -> bool:
        """
        Save current configurations to a JSON file.
        
        Args:
            file_path: Path to save to (uses instance config_file if None)
            
        Returns:
            bool: True if saved successfully
        """
        save_path = file_path or self.config_file
        if not save_path:
            print("No file path specified for saving")
            return False
        
        try:
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(self.configs, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to save config to {save_path}: {e}")
            return False
    
    def get_sensor_configs(self) -> List[Dict[str, Any]]:
        """Get list of sensor configurations."""
        return self.configs.get('sensors', [])
    
    def add_sensor_config(self, sensor_config: Dict[str, Any]) -> bool:
        """
        Add a new sensor configuration.
        
        Args:
            sensor_config: Dictionary with sensor configuration
            
        Returns:
            bool: True if added successfully
        """
        try:
            if 'sensors' not in self.configs:
                self.configs['sensors'] = []
            
            # Check if sensor_id already exists
            sensor_id = sensor_config.get('sensor_id')
            if sensor_id:
                existing_ids = [s.get('sensor_id') for s in self.configs['sensors']]
                if sensor_id in existing_ids:
                    print(f"Sensor with ID {sensor_id} already exists")
                    return False
            
            self.configs['sensors'].append(sensor_config)
            return True
            
        except Exception as e:
            print(f"Failed to add sensor config: {e}")
            return False
    
    def remove_sensor_config(self, sensor_id: str) -> bool:
        """
        Remove a sensor configuration by ID.
        
        Args:
            sensor_id: ID of sensor to remove
            
        Returns:
            bool: True if removed successfully
        """
        try:
            if 'sensors' not in self.configs:
                return False
            
            original_count = len(self.configs['sensors'])
            self.configs['sensors'] = [
                s for s in self.configs['sensors'] 
                if s.get('sensor_id') != sensor_id
            ]
            
            return len(self.configs['sensors']) < original_count
            
        except Exception as e:
            print(f"Failed to remove sensor config: {e}")
            return False
    
    def update_sensor_config(self, sensor_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing sensor configuration.
        
        Args:
            sensor_id: ID of sensor to update
            updates: Dictionary of updates to apply
            
        Returns:
            bool: True if updated successfully
        """
        try:
            if 'sensors' not in self.configs:
                return False
            
            for sensor in self.configs['sensors']:
                if sensor.get('sensor_id') == sensor_id:
                    sensor.update(updates)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Failed to update sensor config: {e}")
            return False
    
    def get_sensor_config(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific sensor.
        
        Args:
            sensor_id: ID of sensor
            
        Returns:
            Dict with sensor configuration or None if not found
        """
        for sensor in self.get_sensor_configs():
            if sensor.get('sensor_id') == sensor_id:
                return sensor
        return None
    
    def set_device_config(self, config: Dict[str, Any]):
        """Set device-level configuration."""
        self.configs['device'] = config
    
    def get_device_config(self) -> Dict[str, Any]:
        """Get device-level configuration."""
        return self.configs.get('device', {})
    
    def validate_sensor_config(self, config: Dict[str, Any]) -> tuple:
        """
        Validate a sensor configuration.
        
        Args:
            config: Sensor configuration to validate
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        required_fields = ['sensor_id', 'sensor_type']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Validate sensor_id is string and not empty
        sensor_id = config['sensor_id']
        if not isinstance(sensor_id, str) or not sensor_id.strip():
            return False, "sensor_id must be a non-empty string"
        
        # Validate sensor_type is string and not empty
        sensor_type = config['sensor_type']
        if not isinstance(sensor_type, str) or not sensor_type.strip():
            return False, "sensor_type must be a non-empty string"
        
        # Validate inputs is a dict if present
        if 'inputs' in config and not isinstance(config['inputs'], dict):
            return False, "inputs must be a dictionary"
        
        # Validate enabled is boolean if present
        if 'enabled' in config and not isinstance(config['enabled'], bool):
            return False, "enabled must be a boolean"
        
        return True, ""
    
    def create_sample_config(self) -> Dict[str, Any]:
        """
        Create a sample configuration with common sensors.
        
        Returns:
            Dict with sample configuration
        """
        return {
            "device": {
                "device_id": "your-device-id",
                "description": "Sample IoT device with sensors"
            },
            "sensors": [
                {
                    "sensor_id": "temp_humidity_1",
                    "sensor_type": "dht11",
                    "inputs": {"pin_no": 14},
                    "enabled": True,
                    "alias": "Living Room Climate"
                },
                {
                    "sensor_id": "pressure_1",
                    "sensor_type": "bmp280",
                    "inputs": {"address": "0x77"},
                    "enabled": True,
                    "alias": "Atmospheric Pressure Sensor"
                },
                {
                    "sensor_id": "motion_1",
                    "sensor_type": "pir",
                    "inputs": {"pin_no": 4},
                    "enabled": True,
                    "alias": "Motion Detector"
                },
                {
                    "sensor_id": "display_1",
                    "sensor_type": "lcd1602",
                    "inputs": {"address": "0x27"},
                    "enabled": True,
                    "alias": "Status Display"
                },
                {
                    "sensor_id": "relay_1",
                    "sensor_type": "dout",
                    "inputs": {"pin_no": 18, "initial_value": False},
                    "enabled": True,
                    "alias": "Output Relay"
                }
            ]
        }


def create_sample_config_file(file_path: str = "sensor_config.json") -> bool:
    """
    Create a sample sensor configuration file.
    
    Args:
        file_path: Path where to create the sample file
        
    Returns:
        bool: True if created successfully
    """
    try:
        manager = SensorConfigManager()
        sample_config = manager.create_sample_config()
        
        with open(file_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"Sample configuration created at: {file_path}")
        return True
        
    except Exception as e:
        print(f"Failed to create sample config: {e}")
        return False


def load_env_config() -> Dict[str, Any]:
    """
    Load sensor configuration from environment variables.
    
    Environment variables:
    - CYBERFLY_SENSORS: JSON string with sensor configurations
    - CYBERFLY_DEVICE_CONFIG: JSON string with device configuration
    
    Returns:
        Dict with configuration from environment
    """
    config = {}
    
    # Load sensor configs
    sensors_env = os.getenv('CYBERFLY_SENSORS')
    if sensors_env:
        try:
            config['sensors'] = json.loads(sensors_env)
        except json.JSONDecodeError as e:
            print(f"Failed to parse CYBERFLY_SENSORS: {e}")
    
    # Load device config
    device_env = os.getenv('CYBERFLY_DEVICE_CONFIG')
    if device_env:
        try:
            config['device'] = json.loads(device_env)
        except json.JSONDecodeError as e:
            print(f"Failed to parse CYBERFLY_DEVICE_CONFIG: {e}")
    
    return config