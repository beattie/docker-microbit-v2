#!/usr/bin/env python3
"""
Button Test - Diagnostic script to verify button notifications

Tests all 5 buttons (B, 1, 2, 3, 4) by monitoring BLE notifications.
Use this to verify buttons are working before using the GUI.

Requirements:
    pip install bleak

Usage:
    python3 test_buttons.py
"""

import asyncio
from bleak import BleakScanner, BleakClient

# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"
BTN_1_UUID = "12345678-1234-5678-1234-56789abcdef5"
BTN_2_UUID = "12345678-1234-5678-1234-56789abcdef6"
BTN_3_UUID = "12345678-1234-5678-1234-56789abcdef7"
BTN_4_UUID = "12345678-1234-5678-1234-56789abcdef8"

DEVICE_NAME = "microbit-joy"

button_states = {
    'B': False,
    '1': False,
    '2': False,
    '3': False,
    '4': False,
}

def notification_handler(sender, data):
    """Handle button notifications"""
    uuid = sender.uuid.lower()
    pressed = data[0] == 1

    button_name = None
    if uuid == BTN_B_UUID.lower():
        button_name = 'B'
    elif uuid == BTN_1_UUID.lower():
        button_name = '1'
    elif uuid == BTN_2_UUID.lower():
        button_name = '2'
    elif uuid == BTN_3_UUID.lower():
        button_name = '3'
    elif uuid == BTN_4_UUID.lower():
        button_name = '4'

    if button_name:
        button_states[button_name] = pressed
        status = "PRESSED" if pressed else "released"
        print(f"🔘 Button {button_name}: {status} (data={data[0]})")
        print_button_grid()

def print_button_grid():
    """Print visual button grid"""
    b = "🟢" if button_states['B'] else "⚪"
    btn1 = "🟢" if button_states['1'] else "⚪"
    btn2 = "🟢" if button_states['2'] else "⚪"
    btn3 = "🟢" if button_states['3'] else "⚪"
    btn4 = "🟢" if button_states['4'] else "⚪"

    print("\n┌─────────────────────────────────┐")
    print(f"│ {b}  B (micro:bit)               │")
    print(f"│ {btn1}  1 (P12)  {btn2}  2 (P13)      │")
    print(f"│ {btn3}  3 (P14)  {btn4}  4 (P15)      │")
    print("└─────────────────────────────────┘\n")

async def test_buttons():
    """Test all buttons"""
    print("=" * 50)
    print("Button Test - Monitoring all 5 buttons")
    print("=" * 50)
    print("\nSearching for micro:bit...")

    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)

    if device is None:
        print(f"❌ Could not find '{DEVICE_NAME}'")
        print("\nTroubleshooting:")
        print("1. Is the micro:bit powered on?")
        print("2. Is the firmware flashed?")
        print("3. Is Bluetooth enabled?")
        return

    print(f"✅ Found device: {device.name} ({device.address})")
    print("\nConnecting...")

    async with BleakClient(device, timeout=20.0) as client:
        print(f"✅ Connected!")

        # Read initial button states
        print("\n📖 Reading initial button states...")
        b_data = await client.read_gatt_char(BTN_B_UUID)
        btn_1_data = await client.read_gatt_char(BTN_1_UUID)
        btn_2_data = await client.read_gatt_char(BTN_2_UUID)
        btn_3_data = await client.read_gatt_char(BTN_3_UUID)
        btn_4_data = await client.read_gatt_char(BTN_4_UUID)

        button_states['B'] = b_data[0] == 1
        button_states['1'] = btn_1_data[0] == 1
        button_states['2'] = btn_2_data[0] == 1
        button_states['3'] = btn_3_data[0] == 1
        button_states['4'] = btn_4_data[0] == 1

        print(f"   Button B: {'PRESSED' if button_states['B'] else 'released'}")
        print(f"   Button 1: {'PRESSED' if button_states['1'] else 'released'}")
        print(f"   Button 2: {'PRESSED' if button_states['2'] else 'released'}")
        print(f"   Button 3: {'PRESSED' if button_states['3'] else 'released'}")
        print(f"   Button 4: {'PRESSED' if button_states['4'] else 'released'}")

        # Subscribe to notifications
        print("\n📡 Starting button notifications...")
        await client.start_notify(BTN_B_UUID, notification_handler)
        print("   ✅ Button B notifications enabled")
        await client.start_notify(BTN_1_UUID, notification_handler)
        print("   ✅ Button 1 notifications enabled")
        await client.start_notify(BTN_2_UUID, notification_handler)
        print("   ✅ Button 2 notifications enabled")
        await client.start_notify(BTN_3_UUID, notification_handler)
        print("   ✅ Button 3 notifications enabled")
        await client.start_notify(BTN_4_UUID, notification_handler)
        print("   ✅ Button 4 notifications enabled")

        print("\n" + "=" * 50)
        print("🎮 Press buttons on the micro:bit/Joystick:bit")
        print("   Press Ctrl+C to exit")
        print("=" * 50)

        print_button_grid()

        # Keep connection alive
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
            await client.stop_notify(BTN_B_UUID)
            await client.stop_notify(BTN_1_UUID)
            await client.stop_notify(BTN_2_UUID)
            await client.stop_notify(BTN_3_UUID)
            await client.stop_notify(BTN_4_UUID)
            print("✅ Disconnected")

if __name__ == "__main__":
    try:
        asyncio.run(test_buttons())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
