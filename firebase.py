import time
from pymodbus.client.serial import ModbusSerialClient as ModbusClient
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pytz

# Firebase init
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://smart-energy-meter-6b162-default-rtdb.firebaseio.com/'
})

# Read and map Modbus registers
def read_modbus_data():
    client = ModbusClient(
        method='rtu',
        port='COM7',
        baudrate=19200,
        stopbits=1,
        bytesize=8,
        parity='N',
        timeout=1
    )

    if client.connect():
        result = client.read_holding_registers(address=0, count=40, slave=1)  # 40 to ensure all needed registers
        client.close()
        if not result.isError():
            registers = result.registers

            # Register mappings (0-based index)
            voltage = registers[0]
            current = registers[6]
            power_factor = registers[12]
            active_power = registers[18]
            reactive_power = registers[24]
            apparent_power = registers[30]
            frequency = registers[36]

            return {
                "voltage": voltage,
                "current": current,
                "power_factor": power_factor,
                "active_power": active_power,
                "reactive_power": reactive_power,
                "apparent_power": apparent_power,
                "frequency": frequency
            }
        else:
            print("❌ Error reading Modbus")
            return None
    else:
        print("❌ Failed to connect")
        return None

# Send data to Firebase
def send_to_firebase(data_dict):
    ref = db.reference("meter_readings")
    data = {
        "timestamp": datetime.now(pytz.utc).isoformat(),
        **data_dict  # Unpack the dictionary into the data payload
    }
    ref.push(data)
    print("✅ Data sent to Firebase:", data)

# Poll loop
while True:
    data = read_modbus_data()
    if data:
        send_to_firebase(data)
    time.sleep(5)
