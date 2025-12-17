#!/usr/bin/env python3
"""
Test script for micro:bit BLE Joystick + Buttons

Connects to the micro:bit and monitors all 4 characteristics:
- X-axis (joystick)
- Y-axis (joystick)
- Button A
- Button B

Requirements:
    pip install bleak

Usage:
    python3 test_buttons.py
"""

import asyncio
from bleak import BleakScanner, BleakClient
import sys

# BLE UUIDs for the joystick service
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
Y_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"
BTN_A_UUID = "12345678-1234-5678-1234-56789abcdef3"
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"

# Battery Service UUIDs (Standard Bluetooth SIG)
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

# Device name to search for
DEVICE_NAME = "microbit-joy"

# Global state for display
joystick_x = 512
joystick_y = 512
button_a_state = "released"
button_b_state = "released"
battery_level = 100


def notification_handler(sender, data):
    """Handle notifications from all characteristics"""
    global joystick_x, joystick_y, button_a_state, button_b_state, battery_level

    uuid = sender.uuid.lower()

    if uuid == X_CHAR_UUID.lower():
        # X-axis is u16 (little-endian)
        joystick_x = int.from_bytes(data, byteorder='little', signed=False)
        print(f"📍 Joystick X: {joystick_x:4d}", end="")
        print(f"  Y: {joystick_y:4d}  |  A: {button_a_state:8s}  B: {button_b_state:8s}  🔋 {battery_level}%")

    elif uuid == Y_CHAR_UUID.lower():
        # Y-axis is u16 (little-endian)
        joystick_y = int.from_bytes(data, byteorder='little', signed=False)

    elif uuid == BTN_A_UUID.lower():
        # Button A is u8 (0 = released, 1 = pressed)
        pressed = data[0] == 1
        button_a_state = "PRESSED" if pressed else "released"
        if pressed:
            print(f"🔘 Button A: PRESSED")
        else:
            print(f"   Button A: released")

    elif uuid == BTN_B_UUID.lower():
        # Button B is u8 (0 = released, 1 = pressed)
        pressed = data[0] == 1
        button_b_state = "PRESSED" if pressed else "released"
        if pressed:
            print(f"🔘 Button B: PRESSED")
        else:
            print(f"   Button B: released")

    elif uuid == BATTERY_LEVEL_UUID.lower():
        # Battery level is u8 (0-100%)
        battery_level = data[0]
        bars = int(battery_level / 10)
        battery_bar = "█" * bars + "░" * (10 - bars)
        print(f"🔋 Battery: {battery_level:3d}% [{battery_bar}]")


async def read_initial_values(client):
    """Read initial values from all characteristics"""
    print("\n📖 Reading initial values...")

    # Read X-axis
    x_data = await client.read_gatt_char(X_CHAR_UUID)
    x_value = int.from_bytes(x_data, byteorder='little', signed=False)
    print(f"   X-axis: {x_value}")

    # Read Y-axis
    y_data = await client.read_gatt_char(Y_CHAR_UUID)
    y_value = int.from_bytes(y_data, byteorder='little', signed=False)
    print(f"   Y-axis: {y_value}")

    # Read Button A
    btn_a_data = await client.read_gatt_char(BTN_A_UUID)
    btn_a = "PRESSED" if btn_a_data[0] == 1 else "released"
    print(f"   Button A: {btn_a}")

    # Read Button B
    btn_b_data = await client.read_gatt_char(BTN_B_UUID)
    btn_b = "PRESSED" if btn_b_data[0] == 1 else "released"
    print(f"   Button B: {btn_b}")

    # Read Battery Level
    try:
        batt_data = await client.read_gatt_char(BATTERY_LEVEL_UUID)
        batt_level = batt_data[0]
        bars = int(batt_level / 10)
        battery_bar = "█" * bars + "░" * (10 - bars)
        print(f"   Battery: {batt_level}% [{battery_bar}]")
    except Exception as e:
        print(f"   Battery: (not available)")


async def main():
    print("=" * 60)
    print("micro:bit BLE Joystick + Buttons Test")
    print("=" * 60)
    print(f"\n🔍 Scanning for '{DEVICE_NAME}'...")

    # Scan for device
    try:
        device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
    except Exception as e:
        print(f"❌ Scan error: {e}")
        return

    if device is None:
        print(f"❌ Device '{DEVICE_NAME}' not found!")
        print("\nTroubleshooting:")
        print("  1. Make sure micro:bit is powered on")
        print("  2. Check that firmware is flashed (cargo flash --release)")
        print("  3. Verify Bluetooth is enabled on this computer")
        print("  4. Try running: sudo systemctl restart bluetooth")
        return

    print(f"✅ Found device: {device.name} ({device.address})")
    print(f"\n🔗 Connecting...")

    # Connect to device
    try:
        async with BleakClient(device) as client:
            print(f"✅ Connected!")

            # Check if service exists
            services = await client.get_services()
            service = services.get_service(SERVICE_UUID)
            if service is None:
                print(f"❌ Service {SERVICE_UUID} not found!")
                return

            print(f"✅ Found joystick service")

            # Read initial values
            await read_initial_values(client)

            # Subscribe to notifications
            print(f"\n📡 Starting notifications...")
            await client.start_notify(X_CHAR_UUID, notification_handler)
            await client.start_notify(Y_CHAR_UUID, notification_handler)
            await client.start_notify(BTN_A_UUID, notification_handler)
            await client.start_notify(BTN_B_UUID, notification_handler)
            try:
                await client.start_notify(BATTERY_LEVEL_UUID, notification_handler)
                print("✅ Monitoring joystick, buttons, and battery...")
            except:
                print("✅ Monitoring joystick and buttons (battery not available)...")

            print("\nMove the joystick and press buttons A/B on the micro:bit")
            print("Press Ctrl+C to stop\n")
            print("-" * 60)

            # Keep connection alive and monitor for 60 seconds (or until Ctrl+C)
            try:
                await asyncio.sleep(3600)  # Monitor for 1 hour
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping...")

            # Unsubscribe
            print("📡 Stopping notifications...")
            await client.stop_notify(X_CHAR_UUID)
            await client.stop_notify(Y_CHAR_UUID)
            await client.stop_notify(BTN_A_UUID)
            await client.stop_notify(BTN_B_UUID)
            try:
                await client.stop_notify(BATTERY_LEVEL_UUID)
            except:
                pass

            print("✅ Disconnected")

    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
