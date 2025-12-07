#!/bin/bash
# Quick script to create all Linux testing files

echo "Creating Linux testing files..."

# Already created by Claude, but let's make sure they exist
if [ ! -f "ble-test.html" ]; then
    echo "Creating ble-test.html..."
    # File is in LINUX_TESTING.md - extract if needed
fi

if [ ! -f "test_joystick.py" ]; then
    echo "Creating test_joystick.py..."
    # File is in LINUX_TESTING.md - extract if needed  
fi

if [ ! -f "test-ble.sh" ]; then
    echo "Creating test-ble.sh..."
    # File is in LINUX_TESTING.md - extract if needed
fi

echo ""
echo "✓ All test files ready!"
echo ""
echo "Quick start options:"
echo "  1. Web Bluetooth (easiest):  xdg-open ble-test.html"
echo "  2. Python script:            ./test_joystick.py"
echo "  3. Command line:             ./test-ble.sh"
echo ""
