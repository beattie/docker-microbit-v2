#!/usr/bin/env python3
"""
Test vibration motor control via BLE
Sends different vibration patterns to micro:bit
"""

import asyncio
from bleak import BleakClient, BleakScanner

# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
VIBRATION_UUID = "12345678-1234-5678-1234-56789abcdefa"

# Vibration patterns
PATTERNS = {
    0: "Off",
    1: "Short (50ms)",
    2: "Medium (150ms)",
    3: "Long (300ms)",
    4: "Double (2x 50ms)",
    5: "Triple (3x 50ms)"
}

async def find_microbit():
    """Scan for micro:bit device"""
    print("🔍 Scanning for micro:bit...")
    devices = await BleakScanner.discover(timeout=5.0)

    for device in devices:
        if device.name and "microbit" in device.name.lower():
            print(f"✅ Found: {device.name} ({device.address})")
            return device.address

    print("❌ micro:bit not found")
    return None

async def test_vibration():
    """Test all vibration patterns"""

    # Find device
    address = await find_microbit()
    if not address:
        print("\n💡 Make sure micro:bit is powered on and flashed with vibration firmware")
        return

    print(f"\n📡 Connecting to {address}...")

    async with BleakClient(address) as client:
        print("✅ Connected!")

        # Test each pattern
        for pattern_id, pattern_name in PATTERNS.items():
            print(f"\n🔊 Testing pattern {pattern_id}: {pattern_name}")
            print("   Writing to vibration characteristic...")

            await client.write_gatt_char(VIBRATION_UUID, bytes([pattern_id]))

            if pattern_id == 0:
                print("   ✅ Motor should be OFF")
                await asyncio.sleep(1)
            elif pattern_id == 1:
                print("   ✅ Should feel short pulse")
                await asyncio.sleep(1)
            elif pattern_id == 2:
                print("   ✅ Should feel medium pulse")
                await asyncio.sleep(1)
            elif pattern_id == 3:
                print("   ✅ Should feel long pulse")
                await asyncio.sleep(1)
            elif pattern_id == 4:
                print("   ✅ Should feel double pulse")
                await asyncio.sleep(1.5)
            elif pattern_id == 5:
                print("   ✅ Should feel triple pulse")
                await asyncio.sleep(2)

        print("\n✅ All patterns tested!")
        print("\n📊 Summary:")
        print("   - Pattern 0: Motor off")
        print("   - Pattern 1: Short (50ms)")
        print("   - Pattern 2: Medium (150ms)")
        print("   - Pattern 3: Long (300ms)")
        print("   - Pattern 4: Double pulse")
        print("   - Pattern 5: Triple pulse")

if __name__ == "__main__":
    print("=" * 50)
    print("  Vibration Motor BLE Test")
    print("=" * 50)

    try:
        asyncio.run(test_vibration())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
