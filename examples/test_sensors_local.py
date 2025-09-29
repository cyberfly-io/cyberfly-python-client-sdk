"""
Local Sensor Testing Example

This example demonstrates how to test sensor functionality locally
without needing IoT platform connectivity.
"""

from cyberflySdk.sensors import SensorManager, SensorConfig
import json
import time

def main():
    # Create sensor manager
    sensor_manager = SensorManager()
    
    print("=== CyberFly Sensor Manager Test ===\n")
    
    # Add CPU temperature sensor (works on most systems)
    print("1. Adding CPU temperature sensor...")
    config = SensorConfig(
        sensor_id="cpu_temp",
        sensor_type="vcgen", 
        inputs={},
        alias="CPU Temperature"
    )
    
    if sensor_manager.add_sensor(config):
        print("✓ CPU temperature sensor added successfully")
    else:
        print("✗ Failed to add CPU temperature sensor")
        print("Note: vcgen sensor requires RaspberryPiVcgencmd package on Raspberry Pi")
    
    # You can add more sensors here (uncomment based on your hardware):
    
    # # DHT11 temperature/humidity sensor on GPIO pin 14
    # dht_config = SensorConfig(
    #     sensor_id="temp_humid_1",
    #     sensor_type="dht11",
    #     inputs={"pin_no": 14},
    #     alias="Room Climate"
    # )
    # if sensor_manager.add_sensor(dht_config):
    #     print("✓ DHT11 sensor added successfully")
    
    # # PIR motion sensor on GPIO pin 4  
    # pir_config = SensorConfig(
    #     sensor_id="motion_1",
    #     sensor_type="pir",
    #     inputs={"pin_no": 4},
    #     alias="Motion Detector"
    # )
    # if sensor_manager.add_sensor(pir_config):
    #     print("✓ PIR sensor added successfully")
    
    print("\n2. Getting sensor status...")
    status = sensor_manager.get_sensor_status()
    print(f"Total sensors: {status['total_sensors']}")
    for sensor in status['sensors']:
        print(f"  - {sensor['sensor_id']}: {sensor['sensor_type']} ({'enabled' if sensor['enabled'] else 'disabled'})")
    
    print("\n3. Reading sensor data...")
    readings = sensor_manager.read_all_sensors()
    for reading in readings:
        print(f"  {reading.sensor_id} ({reading.sensor_type}): {reading.data}")
        if reading.status != "success":
            print(f"    Error: {reading.error}")
    
    print("\n4. Testing sensor commands...")
    test_commands(sensor_manager)
    
    print("\n5. Monitoring sensors (press Ctrl+C to stop)...")
    try:
        monitor_sensors(sensor_manager)
    except KeyboardInterrupt:
        print("\nStopped monitoring")

def test_commands(sensor_manager):
    """Test different sensor commands."""
    
    # Test read command
    print("\n  Testing READ command...")
    read_cmd = {"action": "read", "sensor_id": "cpu_temp"}
    result = sensor_manager.process_command(read_cmd)
    print(f"  Result: {json.dumps(result, indent=2)}")
    
    # Test read all command
    print("\n  Testing READ ALL command...")
    read_all_cmd = {"action": "read"}
    result = sensor_manager.process_command(read_all_cmd)
    print(f"  Found {result.get('count', 0)} sensor readings")
    
    # Test status command
    print("\n  Testing STATUS command...")
    status_cmd = {"action": "status"}
    result = sensor_manager.process_command(status_cmd)
    print(f"  Total sensors: {result['result']['total_sensors']}")

def monitor_sensors(sensor_manager):
    """Monitor sensors continuously."""
    
    while True:
        print(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        readings = sensor_manager.read_all_sensors()
        for reading in readings:
            if reading.status == "success":
                data_str = ", ".join([f"{k}: {v}" for k, v in reading.data.items()])
                print(f"{reading.sensor_id}: {data_str}")
            else:
                print(f"{reading.sensor_id}: ERROR - {reading.error}")
        
        time.sleep(5)

if __name__ == "__main__":
    main()