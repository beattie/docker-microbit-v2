#!/usr/bin/env python3
"""
Test buzzer control via BLE
Sends different tone patterns to micro:bit
"""

import asyncio
from bleak import BleakClient, BleakScanner

# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
BUZZER_UUID = "12345678-1234-5678-1234-56789abcdefb"

# Buzzer tones
TONES = {
    0: "Off",
    1: "C4 (262 Hz)",
    2: "D4 (294 Hz)",
    3: "E4 (330 Hz)",
    4: "G4 (392 Hz)",
    5: "A4 (440 Hz)",
    6: "Beep (1000 Hz)",
    7: "Success (C4→E4→G4)",
    8: "Error (G4→E4→C4)"
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

async def test_buzzer():
    """Test all buzzer tones"""

    # Find device
    address = await find_microbit()
    if not address:
        print("\n💡 Make sure micro:bit is powered on and flashed with buzzer firmware")
        return

    print(f"\n📡 Connecting to {address}...")

    async with BleakClient(address) as client:
        print("✅ Connected!")

        # Check if buzzer characteristic exists
        print(f"\n🔍 Checking for buzzer characteristic {BUZZER_UUID}...")
        services = await client.get_services()
        buzzer_found = False
        for service in services:
            for char in service.characteristics:
                if char.uuid.lower() == BUZZER_UUID.lower():
                    print(f"✅ Found buzzer characteristic!")
                    print(f"   Properties: {char.properties}")
                    buzzer_found = True

        if not buzzer_found:
            print(f"❌ Buzzer characteristic not found!")
            print(f"   Make sure firmware is flashed with buzzer support")
            return

        # Test each tone
        for tone_id, tone_name in TONES.items():
            print(f"\n🔊 Testing tone {tone_id}: {tone_name}")
            print("   Writing to buzzer characteristic...")

            await client.write_gatt_char(BUZZER_UUID, bytes([tone_id]))

            if tone_id == 0:
                print("   ✅ Buzzer should be OFF")
                await asyncio.sleep(1)
            elif tone_id in [1, 2, 3, 4, 5]:
                print("   ✅ Should hear musical note (200ms)")
                await asyncio.sleep(0.5)
            elif tone_id == 6:
                print("   ✅ Should hear short beep")
                await asyncio.sleep(0.5)
            elif tone_id == 7:
                print("   ✅ Should hear rising success melody")
                await asyncio.sleep(0.5)
            elif tone_id == 8:
                print("   ✅ Should hear descending error melody")
                await asyncio.sleep(0.5)

        print("\n✅ All tones tested!")
        print("\n📊 Summary:")
        print("   - Tone 0: Buzzer off")
        print("   - Tones 1-5: Musical notes (C4, D4, E4, G4, A4)")
        print("   - Tone 6: 1000Hz beep")
        print("   - Tone 7: Success melody (rising)")
        print("   - Tone 8: Error melody (descending)")

if __name__ == "__main__":
    print("=" * 50)
    print("  Buzzer BLE Test")
    print("=" * 50)

    try:
        asyncio.run(test_buzzer())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
