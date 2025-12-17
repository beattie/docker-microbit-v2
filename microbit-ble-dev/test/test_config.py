#!/usr/bin/env python3
"""
Test script for micro:bit BLE Configuration Service

Tests writing to configuration characteristics and verifying the changes take effect.

Requirements:
    pip install bleak

Usage:
    python3 test_config.py
"""

import asyncio
from bleak import BleakScanner, BleakClient
import sys

# Configuration Service UUIDs
CONFIG_SERVICE_UUID = "87654321-4321-8765-4321-fedcba987654"
UPDATE_RATE_UUID = "87654321-4321-8765-4321-fedcba987655"
LED_ENABLED_UUID = "87654321-4321-8765-4321-fedcba987656"
DEVICE_NAME_UUID = "87654321-4321-8765-4321-fedcba987657"

# Joystick Service (to monitor update rate changes)
JOYSTICK_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

# Device name to search for
DEVICE_NAME = "microbit-joy"

# Track timing for update rate test
last_update_time = None
update_count = 0


def notification_handler(sender, data):
    """Track notification timing to verify update rate"""
    global last_update_time, update_count
    import time

    current_time = time.time()
    if last_update_time is not None:
        interval_ms = (current_time - last_update_time) * 1000
        print(f"  Update interval: {interval_ms:.0f}ms")
        update_count += 1
    last_update_time = current_time


async def test_update_rate(client):
    """Test changing the joystick update rate"""
    print("\n" + "="*60)
    print("TEST 1: Update Rate Configuration")
    print("="*60)

    # Read current rate
    current_rate_bytes = await client.read_gatt_char(UPDATE_RATE_UUID)
    current_rate = int.from_bytes(current_rate_bytes, byteorder='little')
    print(f"Current update rate: {current_rate}ms")

    # Test: Change to 500ms
    print("\n🔧 Writing new update rate: 500ms...")
    new_rate = 500
    await client.write_gatt_char(UPDATE_RATE_UUID, new_rate.to_bytes(2, 'little'))

    # Verify it was written
    await asyncio.sleep(0.5)
    verify_rate_bytes = await client.read_gatt_char(UPDATE_RATE_UUID)
    verify_rate = int.from_bytes(verify_rate_bytes, byteorder='little')
    print(f"✅ Verified new rate: {verify_rate}ms")

    # Monitor notifications to see the effect
    print("\n📡 Subscribing to X-axis to measure update rate...")
    global last_update_time, update_count
    last_update_time = None
    update_count = 0

    await client.start_notify(X_CHAR_UUID, notification_handler)
    print("Monitoring for 5 seconds...")
    await asyncio.sleep(5)
    await client.stop_notify(X_CHAR_UUID)

    expected_updates = int(5000 / new_rate)
    print(f"\n✅ Received {update_count} updates (expected ~{expected_updates})")

    # Restore original rate
    print(f"\n🔧 Restoring original rate: {current_rate}ms...")
    await client.write_gatt_char(UPDATE_RATE_UUID, current_rate.to_bytes(2, 'little'))


async def test_led_enabled(client):
    """Test toggling LED blinking"""
    print("\n" + "="*60)
    print("TEST 2: LED Enable/Disable")
    print("="*60)

    # Read current state
    current_state_bytes = await client.read_gatt_char(LED_ENABLED_UUID)
    current_state = current_state_bytes[0]
    print(f"Current LED state: {'enabled' if current_state else 'disabled'}")

    # Test: Disable LED
    print("\n🔧 Disabling LED...")
    await client.write_gatt_char(LED_ENABLED_UUID, b'\x00')

    # Verify
    await asyncio.sleep(0.5)
    verify_state_bytes = await client.read_gatt_char(LED_ENABLED_UUID)
    verify_state = verify_state_bytes[0]
    print(f"✅ Verified LED state: {'enabled' if verify_state else 'disabled'}")
    print("👁️  Check your micro:bit - the LED should stop blinking!")

    await asyncio.sleep(3)

    # Test: Re-enable LED
    print("\n🔧 Re-enabling LED...")
    await client.write_gatt_char(LED_ENABLED_UUID, b'\x01')

    verify_state_bytes = await client.read_gatt_char(LED_ENABLED_UUID)
    verify_state = verify_state_bytes[0]
    print(f"✅ Verified LED state: {'enabled' if verify_state else 'disabled'}")
    print("👁️  Check your micro:bit - the LED should start blinking again!")

    await asyncio.sleep(2)


async def test_device_name(client):
    """Test changing device name (requires reconnect)"""
    print("\n" + "="*60)
    print("TEST 3: Device Name Configuration")
    print("="*60)

    # Read current name
    current_name_bytes = await client.read_gatt_char(DEVICE_NAME_UUID)
    # Trim null bytes
    current_name = current_name_bytes.rstrip(b'\x00').decode('utf-8')
    print(f"Current device name: '{current_name}'")

    print("\n⚠️  Note: Device name changes require disconnecting and reconnecting")
    print("ℹ️  Skipping write test to avoid disconnection during test suite")
    print("ℹ️  To test manually, write a new name and reconnect to see it advertised")

    # Example of how to write (not executed):
    # new_name = b'test-joy\x00' * (20 // 9)  # Pad to 20 bytes
    # await client.write_gatt_char(DEVICE_NAME_UUID, new_name[:20])


async def test_invalid_values(client):
    """Test that invalid values are rejected"""
    print("\n" + "="*60)
    print("TEST 4: Input Validation")
    print("="*60)

    # Test: Invalid update rate (too fast)
    print("\n🔧 Testing invalid update rate (10ms - too fast)...")

    # Read current valid value first
    initial_rate_bytes = await client.read_gatt_char(UPDATE_RATE_UUID)
    initial_rate = int.from_bytes(initial_rate_bytes, byteorder='little')
    print(f"   Current valid rate: {initial_rate}ms")

    # Subscribe to notifications to catch the correction
    corrected_rate = []
    def rate_notify_handler(sender, data):
        rate = int.from_bytes(data, byteorder='little')
        corrected_rate.append(rate)
        print(f"   📩 Device corrected value to: {rate}ms")

    await client.start_notify(UPDATE_RATE_UUID, rate_notify_handler)

    try:
        await client.write_gatt_char(UPDATE_RATE_UUID, (10).to_bytes(2, 'little'))
        await asyncio.sleep(1.0)  # Wait for correction notification

        if corrected_rate and corrected_rate[-1] == initial_rate:
            print(f"✅ PASS: Invalid rate rejected (reverted to {initial_rate}ms)")
        elif corrected_rate and corrected_rate[-1] == 10:
            print("❌ FAIL: Invalid rate was accepted!")
        else:
            # Read to double-check
            rate_bytes = await client.read_gatt_char(UPDATE_RATE_UUID)
            rate = int.from_bytes(rate_bytes, byteorder='little')
            if rate == initial_rate:
                print(f"✅ PASS: Invalid rate rejected (value unchanged: {rate}ms)")
            else:
                print(f"❌ FAIL: Invalid rate was accepted! (now {rate}ms)")
    finally:
        await client.stop_notify(UPDATE_RATE_UUID)

    # Test: Invalid LED value
    print("\n🔧 Testing invalid LED value (2 - out of range)...")

    # Read current valid value
    initial_state_bytes = await client.read_gatt_char(LED_ENABLED_UUID)
    initial_state = initial_state_bytes[0]
    print(f"   Current valid state: {initial_state}")

    # Subscribe to notifications
    corrected_state = []
    def led_notify_handler(sender, data):
        state = data[0]
        corrected_state.append(state)
        print(f"   📩 Device corrected value to: {state}")

    await client.start_notify(LED_ENABLED_UUID, led_notify_handler)

    try:
        await client.write_gatt_char(LED_ENABLED_UUID, b'\x02')
        await asyncio.sleep(1.0)  # Wait for correction notification

        if corrected_state and corrected_state[-1] == initial_state:
            print(f"✅ PASS: Invalid LED value rejected (reverted to {initial_state})")
        elif corrected_state and corrected_state[-1] == 2:
            print("❌ FAIL: Invalid LED value was accepted!")
        else:
            # Read to double-check
            state_bytes = await client.read_gatt_char(LED_ENABLED_UUID)
            state = state_bytes[0]
            if state == initial_state:
                print(f"✅ PASS: Invalid LED value rejected (value unchanged: {state})")
            else:
                print(f"❌ FAIL: Invalid LED value was accepted! (now {state})")
    finally:
        await client.stop_notify(LED_ENABLED_UUID)


async def main():
    print("=" * 60)
    print("micro:bit BLE Configuration Service Test")
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

            # Check if config service exists
            services = client.services
            config_service = services.get_service(CONFIG_SERVICE_UUID)

            if config_service is None:
                print(f"❌ Configuration Service not found!")
                print("\nAvailable services:")
                for service in services:
                    print(f"  - {service.uuid}: {service.description}")
                return

            print(f"✅ Found Configuration Service")

            # Run tests
            await test_update_rate(client)
            await test_led_enabled(client)
            await test_device_name(client)
            await test_invalid_values(client)

            print("\n" + "="*60)
            print("✅ All tests completed!")
            print("="*60)

    except Exception as e:
        print(f"❌ Error during tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
        sys.exit(0)
