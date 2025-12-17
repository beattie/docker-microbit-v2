#!/usr/bin/env python3
"""
Test script for micro:bit BLE Battery Service

Connects to the micro:bit and monitors the battery level characteristic.

Requirements:
    pip install bleak

Usage:
    python3 test_battery.py
"""

import asyncio
from bleak import BleakScanner, BleakClient
import sys

# Standard Battery Service UUIDs (Bluetooth SIG)
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

# Device name to search for
DEVICE_NAME = "microbit-joy"


def battery_notification_handler(sender, data):
    """Handle battery level notifications"""
    battery_level = data[0]

    # Visual battery indicator
    bars = int(battery_level / 10)
    battery_bar = "█" * bars + "░" * (10 - bars)

    print(f"🔋 Battery: {battery_level:3d}% [{battery_bar}]")


async def main():
    print("=" * 60)
    print("micro:bit BLE Battery Service Test")
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
        return

    print(f"✅ Found device: {device.name} ({device.address})")
    print(f"\n🔗 Connecting...")

    # Connect to device
    try:
        async with BleakClient(device) as client:
            print(f"✅ Connected!")

            # Check if battery service exists
            services = client.services
            battery_service = services.get_service(BATTERY_SERVICE_UUID)

            if battery_service is None:
                print(f"❌ Battery Service not found!")
                print("\nAvailable services:")
                for service in services:
                    print(f"  - {service.uuid}: {service.description}")
                return

            print(f"✅ Found Battery Service")

            # Read initial battery level
            print(f"\n📖 Reading initial battery level...")
            battery_data = await client.read_gatt_char(BATTERY_LEVEL_UUID)
            battery_level = battery_data[0]
            bars = int(battery_level / 10)
            battery_bar = "█" * bars + "░" * (10 - bars)
            print(f"   Battery Level: {battery_level}% [{battery_bar}]")

            # Subscribe to battery notifications
            print(f"\n📡 Starting battery notifications...")
            await client.start_notify(BATTERY_LEVEL_UUID, battery_notification_handler)

            print("✅ Monitoring battery level...")
            print("\nBattery updates will appear below.")
            print("Press Ctrl+C to stop\n")
            print("-" * 60)

            # Keep connection alive and monitor
            try:
                await asyncio.sleep(3600)  # Monitor for 1 hour
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping...")

            # Unsubscribe
            print("📡 Stopping notifications...")
            await client.stop_notify(BATTERY_LEVEL_UUID)

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
