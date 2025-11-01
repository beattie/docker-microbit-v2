#!/bin/bash
# Simple HTTP server for testing Web Bluetooth
# Web Bluetooth requires HTTP/HTTPS, not file:// protocol

cd "$(dirname "$0")"

echo "================================"
echo "Web Bluetooth Test Server"
echo "================================"
echo ""
echo "Starting HTTP server on port 8000..."
echo ""
echo "Open in your browser:"
echo "  http://localhost:8000/ble-test.html"
echo ""
echo "Press Ctrl+C to stop"
echo "================================"
echo ""

python3 -m http.server 8000
