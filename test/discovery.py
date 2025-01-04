from bleak import BleakClient
from bleak import BleakScanner
import asyncio
import socket
import json

SUPPORTED_POWER_RANGE = "00002ad8-0000-1000-8000-00805f9b34fb" # Read
CYCLING_POWER_MEASUREMENT = "00002a63-0000-1000-8000-00805f9b34fb" # Notify
CYCLING_SPEED_CADENCE_MEASUREMENT = "00002a5b-0000-1000-8000-00805f9b34fb" # Notify 

def send_power(data):
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5005

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    message = json.dumps(data)
    sock.sendto(message.encode(), (UDP_IP, UDP_PORT))

def parse_csc_measurement(data):
    flags = data[0]
    print(f"csc Flgas: {flags}")
    wheel_rev_included_flag = 1
    crank_rev_included_flag = 2

    cumulative_wheel_revs = None
    last_wheel_event_time = None
    cumulative_crank_revs = None
    last_crank_event_time = None

    byte_offset = 1
    if flags & wheel_rev_included_flag:
        cumulative_wheel_revs = int.from_bytes(data[0 + byte_offset:4 + byte_offset], 'little')
        last_wheel_event_time = int.from_bytes(data[4 + byte_offset:6 + byte_offset], 'little')
        byte_offset += 6

    if flags & crank_rev_included_flag:
        cumulative_crank_revs = int.from_bytes(data[0 + byte_offset:2 + byte_offset], 'little')
        last_crank_event_time = int.from_bytes(data[2 + byte_offset:4 + byte_offset], 'little')

    parsed_data = {
        "type":"CSC",
        #"flags" : flags,
        "cumulative_wheel_revs": cumulative_wheel_revs,
        "last_wheel_event_time": last_wheel_event_time,
        "cumulative_crank_revs": cumulative_crank_revs,
        "last_crank_event_time": last_crank_event_time
    }
    
    return parsed_data

def parse_cps_measurement(data):
    flags = int.from_bytes(data[0:2], byteorder="little")
    instantaneous_power = int.from_bytes(data[2:4], byteorder="little", signed=True)
    parsed_data = {
        "type":"CP",
        #"flags": flags,
        "instantaneous_power": instantaneous_power,
    }

    if flags & 0x01: 
        cumulative_power = int.from_bytes(data[4:6], byteorder="little")
        parsed_data["cumulative_power"] = cumulative_power
    return parsed_data

def notification_handler2(sender, data):
    val = parse_csc_measurement(list(data))
    print(f"1.Notification from {sender}: {val}")
    send_power(val)

def notification_handler(sender, data):
    val=parse_cps_measurement(list(data))
    print(f"2.Notification from {sender}: {val}")
    send_power(val)

async def subscribe_to_notifications():
    address = None
    async with BleakScanner() as scanner:
        devices = await scanner.discover() 
        for dev in devices:
            if dev.name and "APX" in dev.name:
                address = dev.address
                print(f"Product:{dev.name}, {dev.address}")

    async with BleakClient(address) as client:
        range = await client.read_gatt_char(SUPPORTED_POWER_RANGE)

        await client.start_notify(CYCLING_POWER_MEASUREMENT, notification_handler)
        await client.start_notify(CYCLING_SPEED_CADENCE_MEASUREMENT, notification_handler2)
        print("Subscribed to notifications. Press Ctrl+C to stop.")
        await asyncio.sleep(180) 
        await client.stop_notify(CYCLING_SPEED_CADENCE_MEASUREMENT)
        reset_to_default_csc = {
            "type":"CSC",
            #"flags" : flags,
            "cumulative_wheel_revs": 0,
            "last_wheel_event_time": 0,
            "cumulative_crank_revs": 0,
            "last_crank_event_time": 0
        }
        send_power(reset_to_default_csc)
        reset_to_default_cp = {
            "type":"CP",
            # "flags": flags,
            "instantaneous_power": 0,
        }
        send_power(reset_to_default_cp)

if __name__ == "__main__":
    #device_address = BLE_ADDRESS # "C9:E9:20:F1:4F:AB" 
    asyncio.run(subscribe_to_notifications())