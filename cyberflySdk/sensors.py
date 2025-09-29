"""
Sensor management module for CyberFly SDK.
Integrates with sensor-library-python to provide unified sensor operations.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


logger = logging.getLogger(__name__)


@dataclass
class SensorConfig:
    """Configuration for a sensor instance."""
    sensor_id: str
    sensor_type: str  # e.g., 'dht11', 'bmp280', 'mpu6050'
    inputs: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    alias: Optional[str] = None  # Optional human-readable name


@dataclass
class SensorReading:
    """Standardized sensor reading with metadata."""
    sensor_id: str
    sensor_type: str
    data: Dict[str, Any]
    timestamp: float
    status: str = "success"
    error: Optional[str] = None


class SensorManager:
    """
    Manages sensor instances and provides command interface for IoT platform.
    """
    
    def __init__(self):
        self.sensors: Dict[str, Any] = {}  # sensor_id -> sensor instance
        self.sensor_configs: Dict[str, SensorConfig] = {}  # sensor_id -> config
        self._sensor_factory = None
        self._config_save_hook = None

    def set_config_save_hook(self, callback):
        """Register a callback to persist sensor configurations."""
        self._config_save_hook = callback

    def _persist_configs(self):
        if self._config_save_hook:
            try:
                configs = [asdict(cfg) for cfg in self.sensor_configs.values()]
                self._config_save_hook(configs)
            except Exception as exc:
                logger.error(f"Failed to persist sensor configuration: {exc}")
        
    def _get_sensor_factory(self):
        """Lazy import of sensor library to avoid dependency issues."""
        if self._sensor_factory is None:
            try:
                from sensor_lib.main import create_sensor
                self._sensor_factory = create_sensor
            except ImportError as e:
                logger.error(f"Failed to import sensor library: {e}")
                raise RuntimeError(
                    "sensor-library-python is required for sensor functionality. "
                    "Install it with: pip install sensor-library-python"
                )
        return self._sensor_factory
        
    def add_sensor(self, config: SensorConfig) -> bool:
        """
        Add a new sensor to the manager.
        
        Args:
            config: Sensor configuration
            
        Returns:
            bool: True if sensor was added successfully
        """
        try:
            if not config.enabled:
                # Store config without instantiating hardware
                self.sensor_configs[config.sensor_id] = config
                if config.sensor_id in self.sensors:
                    del self.sensors[config.sensor_id]
                logger.info(f"Registered disabled sensor {config.sensor_id}")
                return True

            create_sensor = self._get_sensor_factory()
            sensor = create_sensor(config.sensor_type, config.inputs)

            self.sensors[config.sensor_id] = sensor
            self.sensor_configs[config.sensor_id] = config

            logger.info(f"Added sensor {config.sensor_id} of type {config.sensor_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to add sensor {config.sensor_id}: {e}")
            return False
    
    def remove_sensor(self, sensor_id: str) -> bool:
        """
        Remove a sensor from the manager.
        
        Args:
            sensor_id: ID of sensor to remove
            
        Returns:
            bool: True if sensor was removed successfully
        """
        try:
            if sensor_id in self.sensors:
                del self.sensors[sensor_id]
            if sensor_id in self.sensor_configs:
                del self.sensor_configs[sensor_id]
            logger.info(f"Removed sensor {sensor_id}")
            self._persist_configs()
            return True
        except Exception as e:
            logger.error(f"Failed to remove sensor {sensor_id}: {e}")
            return False
    
    def read_sensor(self, sensor_id: str) -> SensorReading:
        """
        Read data from a specific sensor.
        
        Args:
            sensor_id: ID of sensor to read
            
        Returns:
            SensorReading: Reading with data or error
        """
        import time
        
        if sensor_id not in self.sensors:
            return SensorReading(
                sensor_id=sensor_id,
                sensor_type="unknown",
                data={},
                timestamp=time.time(),
                status="error",
                error=f"Sensor {sensor_id} not found"
            )
        
        config = self.sensor_configs[sensor_id]
        if not config.enabled:
            return SensorReading(
                sensor_id=sensor_id,
                sensor_type=config.sensor_type,
                data={},
                timestamp=time.time(),
                status="error",
                error=f"Sensor {sensor_id} is disabled"
            )
        
        try:
            sensor = self.sensors[sensor_id]
            data = sensor.read()
            
            return SensorReading(
                sensor_id=sensor_id,
                sensor_type=config.sensor_type,
                data=data,
                timestamp=time.time(),
                status="success"
            )
            
        except Exception as e:
            logger.error(f"Failed to read sensor {sensor_id}: {e}")
            return SensorReading(
                sensor_id=sensor_id,
                sensor_type=config.sensor_type,
                data={},
                timestamp=time.time(),
                status="error",
                error=str(e)
            )
    
    def read_all_sensors(self) -> List[SensorReading]:
        """
        Read data from all enabled sensors.
        
        Returns:
            List[SensorReading]: List of readings from all sensors
        """
        readings = []
        for sensor_id in self.sensors:
            config = self.sensor_configs[sensor_id]
            if config.enabled:
                reading = self.read_sensor(sensor_id)
                readings.append(reading)
        return readings
    
    def execute_sensor_action(self, sensor_id: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a specific action on a sensor (for output sensors like displays, relays).
        
        Args:
            sensor_id: ID of sensor to control
            action: Action to execute (e.g., 'display_text', 'toggle', 'set_value')
            params: Parameters for the action
            
        Returns:
            Dict with execution result
        """
        import time
        
        if sensor_id not in self.sensors:
            return {
                "status": "error",
                "error": f"Sensor {sensor_id} not found",
                "timestamp": time.time()
            }
        
        config = self.sensor_configs[sensor_id]
        if not config.enabled:
            return {
                "status": "error", 
                "error": f"Sensor {sensor_id} is disabled",
                "timestamp": time.time()
            }
        
        try:
            sensor = self.sensors[sensor_id]
            params = params or {}
            
            # Handle different action types
            if action == "display_text" and hasattr(sensor, 'display_text'):
                text = params.get('text', '')
                clear = params.get('clear', True)
                sensor.display_text(text, clear=clear)
                
            elif action == "append_text" and hasattr(sensor, 'append_text'):
                text = params.get('text', '')
                sensor.append_text(text)
                
            elif action == "clear" and hasattr(sensor, 'clear'):
                sensor.clear()
                
            elif action == "toggle" and hasattr(sensor, 'device') and hasattr(sensor.device, 'toggle'):
                sensor.device.toggle()
                
            elif action == "set_output" and hasattr(sensor, 'device'):
                value = params.get('value', False)
                sensor.device.value = bool(value)
                
            else:
                return {
                    "status": "error",
                    "error": f"Action '{action}' not supported for sensor {sensor_id} of type {config.sensor_type}",
                    "timestamp": time.time()
                }
            
            return {
                "status": "success",
                "action": action,
                "params": params,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute action {action} on sensor {sensor_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_sensor_status(self, sensor_id: str = None) -> Dict[str, Any]:
        """
        Get status information for sensor(s).
        
        Args:
            sensor_id: Specific sensor ID, or None for all sensors
            
        Returns:
            Dict with sensor status information
        """
        import time
        
        if sensor_id:
            if sensor_id not in self.sensor_configs:
                return {
                    "status": "error",
                    "error": f"Sensor {sensor_id} not found",
                    "timestamp": time.time()
                }
            
            config = self.sensor_configs[sensor_id]
            sensor_exists = sensor_id in self.sensors
            
            return {
                "sensor_id": sensor_id,
                "sensor_type": config.sensor_type,
                "enabled": config.enabled,
                "alias": config.alias,
                "inputs": config.inputs,
                "initialized": sensor_exists,
                "timestamp": time.time()
            }
        else:
            # Return status for all sensors
            sensors_status = []
            for sid in self.sensor_configs:
                status = self.get_sensor_status(sid)
                sensors_status.append(status)
            
            return {
                "total_sensors": len(self.sensor_configs),
                "sensors": sensors_status,
                "timestamp": time.time()
            }
    
    def enable_sensor(self, sensor_id: str) -> bool:
        """Enable a sensor."""
        if sensor_id in self.sensor_configs:
            config = self.sensor_configs[sensor_id]
            config.enabled = True
            added = self.add_sensor(config)
            if added:
                self._persist_configs()
            return added
        return False
    
    def disable_sensor(self, sensor_id: str) -> bool:
        """Disable a sensor."""
        if sensor_id in self.sensor_configs:
            self.sensor_configs[sensor_id].enabled = False
            if sensor_id in self.sensors:
                del self.sensors[sensor_id]
            self._persist_configs()
            return True
        return False
    
    def configure_sensor(self, sensor_id: str, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a sensor configuration at runtime."""
        import time

        existing_config = self.sensor_configs.get(sensor_id)
        sensor_type = new_config.get('sensor_type') or (existing_config.sensor_type if existing_config else None)

        if not sensor_type:
            return {
                "status": "error",
                "error": "sensor_type is required when creating a new sensor",
                "timestamp": time.time()
            }

        inputs = new_config.get('inputs', existing_config.inputs if existing_config else {})
        enabled = new_config.get('enabled', existing_config.enabled if existing_config else True)
        alias = new_config.get('alias', existing_config.alias if existing_config else None)

        updated_config = SensorConfig(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            inputs=inputs,
            enabled=enabled,
            alias=alias
        )

        previous_sensor = self.sensors.get(sensor_id)
        previous_config = existing_config

        if sensor_id in self.sensors:
            del self.sensors[sensor_id]

        added = self.add_sensor(updated_config)

        if not added and enabled:
            # Roll back to previous configuration if creation failed
            if previous_config:
                self.sensor_configs[sensor_id] = previous_config
                if previous_sensor:
                    self.sensors[sensor_id] = previous_sensor
            return {
                "status": "error",
                "error": f"Failed to configure sensor {sensor_id}",
                "timestamp": time.time()
            }

        self._persist_configs()

        return {
            "status": "success",
            "sensor_id": sensor_id,
            "config": asdict(updated_config),
            "timestamp": time.time()
        }

    def load_sensor_configs(self, configs: List[Dict[str, Any]]) -> List[str]:
        """
        Load multiple sensor configurations.
        
        Args:
            configs: List of sensor configuration dictionaries
            
        Returns:
            List of sensor IDs that were successfully loaded
        """
        loaded_sensors = []
        
        for config_dict in configs:
            try:
                config = SensorConfig(
                    sensor_id=config_dict['sensor_id'],
                    sensor_type=config_dict['sensor_type'],
                    inputs=config_dict.get('inputs', {}),
                    enabled=config_dict.get('enabled', True),
                    alias=config_dict.get('alias')
                )
                
                if self.add_sensor(config):
                    loaded_sensors.append(config.sensor_id)
                    
            except Exception as e:
                logger.error(f"Failed to load sensor config {config_dict}: {e}")
        
        return loaded_sensors
    
    def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a sensor command from the IoT platform.
        
        Expected command format:
        {
            "action": "read|execute|status",
            "sensor_id": "optional_specific_sensor",
            "params": {...}  # optional parameters for the action
        }
        
        Args:
            command: Command dictionary from IoT platform
            
        Returns:
            Dict with command execution result
        """
        import time
        
        try:
            action = command.get('action')
            sensor_id = command.get('sensor_id')
            params = command.get('params', {})
            
            if action == 'read':
                if sensor_id:
                    reading = self.read_sensor(sensor_id)
                    return {
                        "command": "read",
                        "sensor_id": sensor_id,
                        "result": reading.__dict__,
                        "timestamp": time.time()
                    }
                else:
                    readings = self.read_all_sensors()
                    return {
                        "command": "read_all",
                        "result": [r.__dict__ for r in readings],
                        "count": len(readings),
                        "timestamp": time.time()
                    }
            
            elif action == 'execute':
                if not sensor_id:
                    return {
                        "command": "execute",
                        "status": "error",
                        "error": "sensor_id required for execute command",
                        "timestamp": time.time()
                    }
                
                execute_action = params.get('execute_action', 'read')
                execute_params = params.get('execute_params', {})
                
                result = self.execute_sensor_action(sensor_id, execute_action, execute_params)
                return {
                    "command": "execute",
                    "sensor_id": sensor_id,
                    "execute_action": execute_action,
                    "result": result,
                    "timestamp": time.time()
                }
            
            elif action == 'status':
                status = self.get_sensor_status(sensor_id)
                return {
                    "command": "status",
                    "sensor_id": sensor_id,
                    "result": status,
                    "timestamp": time.time()
                }

            elif action == 'configure':
                if not sensor_id:
                    return {
                        "command": "configure",
                        "status": "error",
                        "error": "sensor_id is required for configure command",
                        "timestamp": time.time()
                    }

                config_payload = command.get('config', {})
                result = self.configure_sensor(sensor_id, config_payload)
                return {
                    "command": "configure",
                    "sensor_id": sensor_id,
                    "result": result,
                    "timestamp": time.time()
                }
            
            else:
                return {
                    "command": action,
                    "status": "error",
                    "error": f"Unknown action: {action}. Supported actions: read, execute, status",
                    "timestamp": time.time()
                }
                
        except Exception as e:
            logger.error(f"Failed to process command {command}: {e}")
            return {
                "command": command.get('action', 'unknown'),
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }