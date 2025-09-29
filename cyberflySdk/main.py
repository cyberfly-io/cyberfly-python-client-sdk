import socketio
from cyberflySdk.config import node_url
from cyberflySdk import utils, api, auth
from cyberflySdk.sensors import SensorManager, SensorConfig
import rule_engine
import json
import logging


class CyberflyClient:
    def __init__(self, device_id: str, key_pair: dict,
                 network_id: str = "mainnet01", node_url=node_url):
        self.sio = socketio.Client()
        self.key_pair = key_pair
        self.network_id = network_id
        self.device_data = {}
        self.device_id = device_id
        self.topic = device_id
        self.account = "k:" + self.key_pair.get("publicKey")
        self.caller = default_callback
        self.node_url = node_url
        self.rules = []
        self.device_info = {}
        
        # Initialize sensor manager
        self.sensor_manager = SensorManager()
        self.logger = logging.getLogger(__name__)
        
        self.update_device()
        self.update_rules()
        self.connect()
        self.sio.on("onmessage", self.on_received)

    def on_received(self, data):
        try:
            msg = json.loads(data['message'])
            json_data = json.loads(msg)
            device_exec = json.loads(json_data.get('device_exec'))
            response_topic = device_exec.get('response_topic')
            if auth.validate_expiry(device_exec) \
                    and auth.check_auth(json_data, self.device_info):
                try:
                    if device_exec.get('update_rules'):
                        self.update_rules()
                    if device_exec.get('update_device'):
                        self.update_device()
                    
                    # Handle sensor commands
                    if device_exec.get('sensor_command'):
                        sensor_result = self.process_sensor_command(device_exec['sensor_command'])
                        if response_topic:
                            signed = utils.make_cmd(sensor_result, self.key_pair)
                            utils.sio_publish(self.sio, response_topic, signed)
                        return
                    
                    # Call the user-defined callback
                    self.caller(device_exec)
                    
                    if response_topic:
                        signed = utils.make_cmd({"info": "success"}, self.key_pair)
                        utils.sio_publish(self.sio, response_topic, signed)
                except Exception as e:
                    error_response = {"info": "error", "error": str(e)}
                    if response_topic:
                        signed = utils.make_cmd(error_response, self.key_pair)
                        utils.sio_publish(self.sio, response_topic, signed)
                    self.logger.error(f"Error processing message: {e}")
            else:
                self.logger.warning(f"Authentication failed for device {self.device_id}")
        except Exception as e:
            self.logger.error(f"Error in on_received: {e}")

    def connect(self):
        try:
            self.sio.connect(self.node_url)
            self.subscribe(self.topic)
        except Exception as e:
            print(e.__str__())
            self.connect()

    def subscribe(self, topic):
        try:
            self.sio.emit('subscribe', topic)
        except Exception as e:
            print(e.__str__())
            self.connect()

    def publish(self, topic, msg):
        signed = utils.make_cmd(msg, self.key_pair)
        utils.sio_publish(self.sio, topic, signed)

    def update_data(self, key: str, value):
        self.device_data.update({key: value})

    def on_message(self):
        def decorator(callback_function):
            self.caller = callback_function
        return decorator

    def process_rules(self, data: dict):
        rules = self.rules
        if len(rules) == 0:
            self.update_rules()
        context = rule_engine.Context(default_value=None)
        for rule in rules:
            rul = rule_engine.Rule(utils.make_rule(rule['rule']), context=context)
            try:
                if rul.matches(data):
                    utils.publish(self.sio, rule['action'], self.key_pair)
            except Exception as e:
                print(e.__str__())

    def process_schedule(self, data: dict):
        pass

    def update_rules(self):
        rules = api.get_rules(self.device_id, self.network_id, self.key_pair)
        self.rules = rules

    def update_device(self):
        device = api.get_device(self.device_id, self.network_id, self.key_pair)
        self.device_info = device

    def store_data(self, data):
        signed = utils.make_cmd_to_store(data, self.key_pair)
        #need to implement

    # Sensor Management Methods
    
    def add_sensor(self, sensor_id: str, sensor_type: str, inputs: dict = None, 
                   enabled: bool = True, alias: str = None) -> bool:
        """
        Add a sensor to this device.
        
        Args:
            sensor_id: Unique identifier for the sensor
            sensor_type: Type of sensor (e.g., 'dht11', 'bmp280', 'mpu6050')
            inputs: Configuration inputs for the sensor
            enabled: Whether the sensor is enabled
            alias: Optional human-readable name
            
        Returns:
            bool: True if sensor was added successfully
        """
        config = SensorConfig(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            inputs=inputs or {},
            enabled=enabled,
            alias=alias
        )
        return self.sensor_manager.add_sensor(config)
    
    def remove_sensor(self, sensor_id: str) -> bool:
        """Remove a sensor from this device."""
        return self.sensor_manager.remove_sensor(sensor_id)
    
    def read_sensor(self, sensor_id: str) -> dict:
        """Read data from a specific sensor."""
        reading = self.sensor_manager.read_sensor(sensor_id)
        return reading.__dict__
    
    def read_all_sensors(self) -> list:
        """Read data from all enabled sensors."""
        readings = self.sensor_manager.read_all_sensors()
        return [r.__dict__ for r in readings]
    
    def execute_sensor_action(self, sensor_id: str, action: str, params: dict = None) -> dict:
        """Execute an action on a sensor (for output sensors)."""
        return self.sensor_manager.execute_sensor_action(sensor_id, action, params)
    
    def get_sensor_status(self, sensor_id: str = None) -> dict:
        """Get status information for sensor(s)."""
        return self.sensor_manager.get_sensor_status(sensor_id)
    
    def enable_sensor(self, sensor_id: str) -> bool:
        """Enable a sensor."""
        return self.sensor_manager.enable_sensor(sensor_id)
    
    def disable_sensor(self, sensor_id: str) -> bool:
        """Disable a sensor."""
        return self.sensor_manager.disable_sensor(sensor_id)
    
    def load_sensor_configs(self, configs: list) -> list:
        """
        Load multiple sensor configurations.
        
        Args:
            configs: List of sensor configuration dictionaries
            
        Returns:
            List of sensor IDs that were successfully loaded
        """
        return self.sensor_manager.load_sensor_configs(configs)
    
    def process_sensor_command(self, command: dict) -> dict:
        """
        Process a sensor command from the IoT platform.
        
        Args:
            command: Command dictionary with 'action', optional 'sensor_id', and 'params'
            
        Returns:
            Dict with command execution result
        """
        return self.sensor_manager.process_command(command)
    
    def publish_sensor_reading(self, sensor_id: str, topic: str = None):
        """
        Read a sensor and publish the data to the specified topic.
        
        Args:
            sensor_id: ID of sensor to read
            topic: Topic to publish to (defaults to device topic)
        """
        reading = self.read_sensor(sensor_id)
        publish_topic = topic or self.topic
        self.publish(publish_topic, reading)
    
    def publish_all_sensor_readings(self, topic: str = None):
        """
        Read all sensors and publish their data to the specified topic.
        
        Args:
            topic: Topic to publish to (defaults to device topic)
        """
        readings = self.read_all_sensors()
        publish_topic = topic or self.topic
        sensor_data = {
            "device_id": self.device_id,
            "sensors": readings,
            "count": len(readings)
        }
        self.publish(publish_topic, sensor_data)


def default_callback(data):
    pass