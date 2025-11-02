#!/usr/bin/env python3
"""
GUI Test for micro:bit BLE Joystick + Buttons + Vibration

A graphical interface to test the joystick, buttons, and vibration motor
with real-time visual feedback and BLE control.

Requirements:
    pip install bleak

Usage:
    python3 gui_test.py
"""

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakScanner, BleakClient
import threading
import sys

# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
Y_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"
BTN_A_UUID = "12345678-1234-5678-1234-56789abcdef3"
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"
VIBRATION_UUID = "12345678-1234-5678-1234-56789abcdefa"

DEVICE_NAME = "microbit-joy"


class JoystickGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("micro:bit Joystick + Buttons + Vibration Test")
        self.root.geometry("720x1200")  # Increased height for vibration controls
        self.root.minsize(720, 1200)  # Set minimum size
        self.root.configure(bg='#f0f0f0')

        # BLE connection state
        self.client = None
        self.connected = False
        self.ble_thread = None
        self.ble_loop = None  # Store event loop reference
        self.shutting_down = False  # Flag to stop processing notifications

        # Joystick state
        self.joystick_x = 512
        self.joystick_y = 512
        self.button_a_pressed = False
        self.button_b_pressed = False

        self.setup_ui()

    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#667eea', pady=20)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text="🎮 micro:bit Gamepad",
            font=("Arial", 24, "bold"),
            bg='#667eea',
            fg='white'
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_frame,
            text="Joystick + Buttons + Vibration BLE Test",
            font=("Arial", 12),
            bg='#667eea',
            fg='white'
        )
        subtitle_label.pack()

        # Connection frame
        conn_frame = tk.Frame(self.root, bg='#f0f0f0', pady=15)
        conn_frame.pack(fill=tk.X, padx=20)

        self.connect_btn = tk.Button(
            conn_frame,
            text="Connect to micro:bit",
            command=self.toggle_connection,
            font=("Arial", 14, "bold"),
            bg='#667eea',
            fg='white',
            relief=tk.FLAT,
            pady=10,
            cursor='hand2'
        )
        self.connect_btn.pack(fill=tk.X)

        # Status label
        self.status_label = tk.Label(
            conn_frame,
            text="Disconnected",
            font=("Arial", 12),
            bg='#fee',
            fg='#c33',
            pady=10,
            relief=tk.GROOVE,
            borderwidth=2
        )
        self.status_label.pack(fill=tk.X, pady=(10, 0))

        # Joystick visual frame
        joystick_frame = tk.LabelFrame(
            self.root,
            text="📍 Joystick Position",
            font=("Arial", 14, "bold"),
            bg='#f8f9fa',
            pady=20,
            padx=20
        )
        joystick_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Canvas for joystick
        self.canvas = tk.Canvas(
            joystick_frame,
            width=300,
            height=300,
            bg='#e9ecef',
            highlightthickness=2,
            highlightbackground='#dee2e6'
        )
        self.canvas.pack()

        # Draw joystick background
        self.canvas.create_oval(10, 10, 290, 290, fill='#e9ecef', outline='#dee2e6', width=4)

        # Draw crosshair
        self.canvas.create_line(150, 10, 150, 290, fill='#adb5bd', width=2)
        self.canvas.create_line(10, 150, 290, 150, fill='#adb5bd', width=2)

        # Draw center circle (will be moved)
        self.joystick_dot = self.canvas.create_oval(
            130, 130, 170, 170,
            fill='#667eea',
            outline='white',
            width=3
        )

        # Value labels
        values_frame = tk.Frame(joystick_frame, bg='#f8f9fa')
        values_frame.pack(pady=10)

        x_frame = tk.Frame(values_frame, bg='white', relief=tk.RAISED, borderwidth=2)
        x_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(x_frame, text="X-AXIS", font=("Courier", 10), bg='white', fg='#666').pack(pady=(5, 0))
        self.x_value_label = tk.Label(x_frame, text="512", font=("Courier", 28, "bold"), bg='white', fg='#333')
        self.x_value_label.pack(pady=(0, 5), padx=20)

        y_frame = tk.Frame(values_frame, bg='white', relief=tk.RAISED, borderwidth=2)
        y_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(y_frame, text="Y-AXIS", font=("Courier", 10), bg='white', fg='#666').pack(pady=(5, 0))
        self.y_value_label = tk.Label(y_frame, text="512", font=("Courier", 28, "bold"), bg='white', fg='#333')
        self.y_value_label.pack(pady=(0, 5), padx=20)

        # Buttons frame
        buttons_frame = tk.LabelFrame(
            self.root,
            text="🔘 Buttons",
            font=("Arial", 14, "bold"),
            bg='#f8f9fa',
            pady=20,
            padx=20
        )
        buttons_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        button_grid = tk.Frame(buttons_frame, bg='#f8f9fa')
        button_grid.pack()

        # Button A display
        self.button_a_frame = tk.Frame(button_grid, bg='white', relief=tk.RAISED, borderwidth=3, width=120, height=80)
        self.button_a_frame.pack(side=tk.LEFT, padx=20)
        self.button_a_frame.pack_propagate(False)

        self.button_a_label = tk.Label(self.button_a_frame, text="Button A", font=("Arial", 16, "bold"), bg='white')
        self.button_a_label.pack(pady=(10, 5))
        self.button_a_status = tk.Label(self.button_a_frame, text="Released", font=("Arial", 11), bg='white', fg='#666')
        self.button_a_status.pack()

        # Button B display
        self.button_b_frame = tk.Frame(button_grid, bg='white', relief=tk.RAISED, borderwidth=3, width=120, height=80)
        self.button_b_frame.pack(side=tk.LEFT, padx=20)
        self.button_b_frame.pack_propagate(False)

        self.button_b_label = tk.Label(self.button_b_frame, text="Button B", font=("Arial", 16, "bold"), bg='white')
        self.button_b_label.pack(pady=(10, 5))
        self.button_b_status = tk.Label(self.button_b_frame, text="Released", font=("Arial", 11), bg='white', fg='#666')
        self.button_b_status.pack()

        # Vibration control frame
        vibration_frame = tk.LabelFrame(
            self.root,
            text="🔊 Vibration Motor Control",
            font=("Arial", 14, "bold"),
            bg='#f8f9fa',
            pady=20,
            padx=20
        )
        vibration_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        vib_label = tk.Label(
            vibration_frame,
            text="Click buttons to trigger vibration patterns via BLE\n(Motor vibrates when you press pattern buttons)",
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#666',
            justify=tk.CENTER
        )
        vib_label.pack(pady=(0, 10))

        # Create grid for vibration buttons
        vib_grid1 = tk.Frame(vibration_frame, bg='#f8f9fa')
        vib_grid1.pack(pady=5)

        vib_grid2 = tk.Frame(vibration_frame, bg='#f8f9fa')
        vib_grid2.pack(pady=5)

        # Define vibration patterns
        patterns = [
            ("Off", 0, '#e74c3c'),
            ("Short\n50ms", 1, '#667eea'),
            ("Medium\n150ms", 2, '#667eea'),
            ("Long\n300ms", 3, '#667eea'),
            ("Double\nPulse", 4, '#5f27cd'),
            ("Triple\nPulse", 5, '#5f27cd')
        ]

        # Create buttons for each pattern
        for i, (label, pattern_id, color) in enumerate(patterns):
            parent = vib_grid1 if i < 3 else vib_grid2

            # Create button with fixed size
            btn = tk.Button(
                parent,
                text=label,
                command=lambda p=pattern_id: self.send_vibration(p),
                font=("Arial", 10, "bold"),
                bg=color,
                fg='white',
                relief=tk.RAISED,
                borderwidth=3,
                width=12,
                height=3,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=8, pady=8)

            # Disable vibration buttons until connected
            if i == 0:
                self.vib_off_btn = btn
            elif i == 1:
                self.vib_short_btn = btn
            elif i == 2:
                self.vib_medium_btn = btn
            elif i == 3:
                self.vib_long_btn = btn
            elif i == 4:
                self.vib_double_btn = btn
            elif i == 5:
                self.vib_triple_btn = btn

        # Store all vibration buttons for enable/disable
        self.vibration_buttons = [
            self.vib_off_btn,
            self.vib_short_btn,
            self.vib_medium_btn,
            self.vib_long_btn,
            self.vib_double_btn,
            self.vib_triple_btn
        ]

        # Disable all vibration buttons initially
        for btn in self.vibration_buttons:
            btn.config(state=tk.DISABLED)

    def update_status(self, message, color):
        """Update connection status"""
        self.status_label.config(text=message)
        if color == "green":
            self.status_label.config(bg='#efe', fg='#3c3')
        elif color == "red":
            self.status_label.config(bg='#fee', fg='#c33')
        elif color == "yellow":
            self.status_label.config(bg='#ffeaa7', fg='#d63031')

    def update_joystick_visual(self, x, y):
        """Update joystick dot position"""
        # Convert 0-1023 range to canvas coordinates
        # Canvas center is at 150, 150
        # Range: -135 to +135 pixels from center
        x_pos = 150 - ((x - 512) / 512) * 135
        y_pos = 150 - ((y - 512) / 512) * 135

        # Update dot position
        self.canvas.coords(self.joystick_dot, x_pos - 20, y_pos - 20, x_pos + 20, y_pos + 20)

    def update_button_display(self, button, pressed):
        """Update button display"""
        print(f"🎨 Updating GUI: Button {button} -> {'PRESSED' if pressed else 'Released'}")  # DEBUG

        try:
            if button == 'A':
                if pressed:
                    print(f"   → Setting Button A to PRESSED (purple)")
                    self.button_a_frame.config(bg='#667eea', relief=tk.SUNKEN)
                    self.button_a_label.config(bg='#667eea', fg='white')
                    self.button_a_status.config(text="PRESSED", bg='#667eea', fg='white', font=("Arial", 11, "bold"))
                else:
                    print(f"   → Setting Button A to Released (white)")
                    self.button_a_frame.config(bg='white', relief=tk.RAISED)
                    self.button_a_label.config(bg='white', fg='black')
                    self.button_a_status.config(text="Released", bg='white', fg='#666', font=("Arial", 11))

            elif button == 'B':
                if pressed:
                    print(f"   → Setting Button B to PRESSED (purple)")
                    self.button_b_frame.config(bg='#667eea', relief=tk.SUNKEN)
                    self.button_b_label.config(bg='#667eea', fg='white')
                    self.button_b_status.config(text="PRESSED", bg='#667eea', fg='white', font=("Arial", 11, "bold"))
                else:
                    print(f"   → Setting Button B to Released (white)")
                    self.button_b_frame.config(bg='white', relief=tk.RAISED)
                    self.button_b_label.config(bg='white', fg='black')
                    self.button_b_status.config(text="Released", bg='white', fg='#666', font=("Arial", 11))

            # Force GUI update
            self.root.update_idletasks()
            print(f"   ✓ GUI updated")

        except Exception as e:
            print(f"   ✗ Error updating button display: {e}")
            import traceback
            traceback.print_exc()

    def send_vibration(self, pattern):
        """Send vibration command via BLE"""
        if not self.connected or not self.client or not self.ble_loop:
            messagebox.showwarning("Not Connected", "Please connect to micro:bit first!")
            return

        pattern_names = ["Off", "Short", "Medium", "Long", "Double", "Triple"]
        print(f"🔊 Sending vibration pattern: {pattern} ({pattern_names[pattern]})")

        # Schedule write in the BLE event loop (thread-safe)
        async def write_vibration():
            try:
                await self.client.write_gatt_char(VIBRATION_UUID, bytes([pattern]))
                print(f"   ✅ Vibration command sent successfully")
            except Exception as e:
                print(f"   ❌ Error sending vibration: {e}")
                self.root.after(0, lambda err=str(e): messagebox.showerror("BLE Error", f"Failed to send vibration: {err}"))

        # Use run_coroutine_threadsafe to schedule in the BLE loop
        try:
            asyncio.run_coroutine_threadsafe(write_vibration(), self.ble_loop)
        except Exception as e:
            print(f"   ❌ Error scheduling vibration: {e}")
            messagebox.showerror("BLE Error", f"Failed to schedule vibration: {e}")

    def notification_handler(self, sender, data):
        """Handle BLE notifications"""
        # Ignore notifications if shutting down
        if self.shutting_down:
            return

        uuid = sender.uuid.lower()

        if uuid == X_CHAR_UUID.lower():
            x = int.from_bytes(data, byteorder='little', signed=False)
            self.joystick_x = x
            self.root.after(0, lambda: self.x_value_label.config(text=str(x)))
            self.root.after(0, lambda: self.update_joystick_visual(self.joystick_x, self.joystick_y))

        elif uuid == Y_CHAR_UUID.lower():
            y = int.from_bytes(data, byteorder='little', signed=False)
            self.joystick_y = y
            self.root.after(0, lambda: self.y_value_label.config(text=str(y)))
            self.root.after(0, lambda: self.update_joystick_visual(self.joystick_x, self.joystick_y))

        elif uuid == BTN_A_UUID.lower():
            pressed = data[0] == 1
            self.button_a_pressed = pressed
            print(f"🔘 Button A notification: {'PRESSED' if pressed else 'released'} (data={data[0]})")  # DEBUG
            # Fix lambda closure issue by using default argument
            self.root.after(0, lambda p=pressed: self.update_button_display('A', p))

        elif uuid == BTN_B_UUID.lower():
            pressed = data[0] == 1
            self.button_b_pressed = pressed
            print(f"🔘 Button B notification: {'PRESSED' if pressed else 'released'} (data={data[0]})")  # DEBUG
            # Fix lambda closure issue by using default argument
            self.root.after(0, lambda p=pressed: self.update_button_display('B', p))

    async def connect_ble(self):
        """Connect to BLE device"""
        try:
            # Reset shutdown flag for new connection
            self.shutting_down = False

            # Store event loop reference for thread-safe operations
            self.ble_loop = asyncio.get_event_loop()

            self.root.after(0, lambda: self.update_status("Scanning for micro:bit...", "yellow"))

            device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)

            if device is None:
                self.root.after(0, lambda: self.update_status("Device not found!", "red"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Connection Error",
                    f"Could not find '{DEVICE_NAME}'.\n\n"
                    "Make sure:\n"
                    "1. micro:bit is powered on\n"
                    "2. Firmware is flashed\n"
                    "3. Bluetooth is enabled"
                ))
                self.connected = False
                self.root.after(0, lambda: self.connect_btn.config(text="Connect to micro:bit", state=tk.NORMAL))
                return

            self.root.after(0, lambda: self.update_status("Connecting...", "yellow"))

            async with BleakClient(device, timeout=20.0) as client:
                self.client = client
                self.connected = True

                print(f"🔗 BLE client connected: {client.is_connected}")

                # Read initial values
                print("📖 Reading initial values...")
                x_data = await client.read_gatt_char(X_CHAR_UUID)
                y_data = await client.read_gatt_char(Y_CHAR_UUID)
                a_data = await client.read_gatt_char(BTN_A_UUID)
                b_data = await client.read_gatt_char(BTN_B_UUID)

                self.joystick_x = int.from_bytes(x_data, byteorder='little', signed=False)
                self.joystick_y = int.from_bytes(y_data, byteorder='little', signed=False)

                print(f"   X-axis: {self.joystick_x}")
                print(f"   Y-axis: {self.joystick_y}")
                print(f"   Button A: {a_data[0]} ({'PRESSED' if a_data[0] == 1 else 'released'})")
                print(f"   Button B: {b_data[0]} ({'PRESSED' if b_data[0] == 1 else 'released'})")

                self.root.after(0, lambda: self.x_value_label.config(text=str(self.joystick_x)))
                self.root.after(0, lambda: self.y_value_label.config(text=str(self.joystick_y)))
                self.root.after(0, lambda: self.update_joystick_visual(self.joystick_x, self.joystick_y))
                # Fix lambda closure - capture values with default arguments
                btn_a_initial = a_data[0] == 1
                btn_b_initial = b_data[0] == 1
                self.root.after(0, lambda a=btn_a_initial: self.update_button_display('A', a))
                self.root.after(0, lambda b=btn_b_initial: self.update_button_display('B', b))

                # Start notifications
                print("📡 Starting notifications...")
                await client.start_notify(X_CHAR_UUID, self.notification_handler)
                print("   ✅ X-axis notifications enabled")
                await client.start_notify(Y_CHAR_UUID, self.notification_handler)
                print("   ✅ Y-axis notifications enabled")
                await client.start_notify(BTN_A_UUID, self.notification_handler)
                print("   ✅ Button A notifications enabled")
                await client.start_notify(BTN_B_UUID, self.notification_handler)
                print("   ✅ Button B notifications enabled")

                self.root.after(0, lambda: self.update_status("✅ Connected!", "green"))
                self.root.after(0, lambda: self.connect_btn.config(text="Disconnect"))

                # Enable vibration buttons
                for btn in self.vibration_buttons:
                    self.root.after(0, lambda b=btn: b.config(state=tk.NORMAL))

                # Keep connection alive
                while self.connected:
                    await asyncio.sleep(0.1)

                # Disconnection requested - clean shutdown
                print("🔌 Disconnecting - stopping notifications...")
                try:
                    await client.stop_notify(X_CHAR_UUID)
                    await client.stop_notify(Y_CHAR_UUID)
                    await client.stop_notify(BTN_A_UUID)
                    await client.stop_notify(BTN_B_UUID)
                    print("   ✅ Notifications stopped")
                except Exception as e:
                    print(f"   ⚠️ Error stopping notifications: {e}")

                # Explicitly disconnect before exiting context
                print("🔌 Explicitly disconnecting BLE client...")
                try:
                    if client.is_connected:
                        await client.disconnect()
                        print("   ✅ Client disconnected")
                    else:
                        print("   ℹ️ Client already disconnected")
                except Exception as e:
                    print(f"   ⚠️ Error disconnecting: {e}")

                # Small delay to ensure disconnect completes
                await asyncio.sleep(0.3)

        except Exception as e:
            self.connected = False
            self.ble_loop = None  # Clear loop reference

            print(f"❌ BLE Error: {e}")

            # Try to disconnect if we have a client reference
            if self.client:
                try:
                    print("🔌 Attempting emergency disconnect...")
                    if self.client.is_connected:
                        await self.client.disconnect()
                        print("   ✅ Emergency disconnect successful")
                except Exception as disc_err:
                    print(f"   ⚠️ Emergency disconnect failed: {disc_err}")

            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", "red"))
            self.root.after(0, lambda: messagebox.showerror("BLE Error", str(e)))
            self.root.after(0, lambda: self.connect_btn.config(text="Connect to micro:bit", state=tk.NORMAL))

            # Disable vibration buttons
            for btn in self.vibration_buttons:
                self.root.after(0, lambda b=btn: b.config(state=tk.DISABLED))
        finally:
            # Ensure cleanup
            self.ble_loop = None
            self.client = None
            self.connected = False
            self.shutting_down = False  # Reset for next connection
            print("🔌 BLE connection fully closed")

            # Update UI
            self.root.after(0, lambda: self.update_status("Disconnected", "red"))
            self.root.after(0, lambda: self.connect_btn.config(text="Connect to micro:bit", state=tk.NORMAL))
            for btn in self.vibration_buttons:
                self.root.after(0, lambda b=btn: b.config(state=tk.DISABLED))

    def toggle_connection(self):
        """Toggle BLE connection"""
        if not self.connected:
            self.connect_btn.config(state=tk.DISABLED)
            self.ble_thread = threading.Thread(target=lambda: asyncio.run(self.connect_ble()), daemon=True)
            self.ble_thread.start()
        else:
            print("🔌 User requested disconnect...")
            self.shutting_down = True  # Stop processing notifications
            self.connected = False
            self.ble_loop = None  # Clear loop reference
            self.update_status("Disconnected", "red")
            self.connect_btn.config(text="Connect to micro:bit", state=tk.NORMAL)

            # Disable vibration buttons
            for btn in self.vibration_buttons:
                btn.config(state=tk.DISABLED)

    def on_closing(self):
        """Handle window close"""
        print("\n🛑 Window closing - cleaning up BLE connection...")

        # Stop processing notifications immediately
        self.shutting_down = True
        print("   🛑 Stopped processing notifications")

        # Signal disconnect
        self.connected = False
        self.ble_loop = None

        # Give the async loop a moment to wake up and process the disconnect signal
        import time
        time.sleep(0.3)

        # Wait for BLE thread to finish cleanup
        if self.ble_thread and self.ble_thread.is_alive():
            print("   Waiting for BLE thread to finish (up to 5 seconds)...")
            self.ble_thread.join(timeout=5.0)  # Increased timeout for proper cleanup

            if self.ble_thread.is_alive():
                print("   ⚠️ WARNING: BLE thread did not finish in time!")
                print("   ⚠️ This may cause connection issues on next run")
                print("   💡 Consider power-cycling the micro:bit if reconnection fails")
            else:
                print("   ✅ BLE thread finished cleanly")

        print("   ✅ Cleanup complete - destroying window")
        self.root.destroy()


def main():
    root = tk.Tk()
    app = JoystickGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
