#!/usr/bin/env python3
"""
GUI Test for micro:bit BLE Joystick + 5 Buttons + Vibration + Buzzer

A graphical interface to test the joystick (X/Y axes), 5 buttons
(B + 1,2,3,4), vibration motor, and buzzer with real-time visual
feedback and BLE control.

Button Configuration:
- Button B: micro:bit built-in (P23) - Emergency/Special
- Buttons 1-4: Joystick:bit (P12, P13, P14, P15)
- Note: Button 3 uses P14 (replaces micro:bit Button A)

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
# BTN_A_UUID = "12345678-1234-5678-1234-56789abcdef3"  # Unused (replaced by Button 3)
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"
BTN_1_UUID = "12345678-1234-5678-1234-56789abcdef5"
BTN_2_UUID = "12345678-1234-5678-1234-56789abcdef6"
BTN_3_UUID = "12345678-1234-5678-1234-56789abcdef7"
BTN_4_UUID = "12345678-1234-5678-1234-56789abcdef8"
VIBRATION_UUID = "12345678-1234-5678-1234-56789abcdefa"
BUZZER_UUID = "12345678-1234-5678-1234-56789abcdefb"

DEVICE_NAME = "microbit-joy"


class JoystickGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("micro:bit Joystick + 5 Buttons + Vibration + Buzzer Test")
        self.root.geometry("720x1200")  # Increased height for all controls
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
        self.button_b_pressed = False
        self.button_1_pressed = False
        self.button_2_pressed = False
        self.button_3_pressed = False
        self.button_4_pressed = False

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
            text="Joystick + 5 Buttons + Vibration + Buzzer BLE Test",
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
            text="🔘 Buttons (B=micro:bit, 1-4=Joystick:bit)",
            font=("Arial", 14, "bold"),
            bg='#f8f9fa',
            pady=20,
            padx=20
        )
        buttons_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Two rows of buttons
        button_grid_top = tk.Frame(buttons_frame, bg='#f8f9fa')
        button_grid_top.pack(pady=5)

        button_grid_bottom = tk.Frame(buttons_frame, bg='#f8f9fa')
        button_grid_bottom.pack(pady=5)

        # Button B display (micro:bit) - Special/Emergency button
        self.button_b_frame = tk.Frame(button_grid_top, bg='white', relief=tk.RAISED, borderwidth=3, width=130, height=80)
        self.button_b_frame.pack(side=tk.LEFT, padx=10)
        self.button_b_frame.pack_propagate(False)

        self.button_b_label = tk.Label(self.button_b_frame, text="Button B", font=("Arial", 14, "bold"), bg='white')
        self.button_b_label.pack(pady=(8, 2))
        self.button_b_pin = tk.Label(self.button_b_frame, text="(micro:bit)", font=("Arial", 8), bg='white', fg='#999')
        self.button_b_pin.pack()
        self.button_b_status = tk.Label(self.button_b_frame, text="Released", font=("Arial", 10), bg='white', fg='#666')
        self.button_b_status.pack()

        # Button 1 display (Joystick:bit P12)
        self.button_1_frame = tk.Frame(button_grid_top, bg='white', relief=tk.RAISED, borderwidth=3, width=130, height=80)
        self.button_1_frame.pack(side=tk.LEFT, padx=10)
        self.button_1_frame.pack_propagate(False)

        self.button_1_label = tk.Label(self.button_1_frame, text="Button 1", font=("Arial", 14, "bold"), bg='white')
        self.button_1_label.pack(pady=(8, 2))
        self.button_1_pin = tk.Label(self.button_1_frame, text="(P12)", font=("Arial", 8), bg='white', fg='#999')
        self.button_1_pin.pack()
        self.button_1_status = tk.Label(self.button_1_frame, text="Released", font=("Arial", 10), bg='white', fg='#666')
        self.button_1_status.pack()

        # Button 2 display (Joystick:bit P13)
        self.button_2_frame = tk.Frame(button_grid_top, bg='white', relief=tk.RAISED, borderwidth=3, width=130, height=80)
        self.button_2_frame.pack(side=tk.LEFT, padx=10)
        self.button_2_frame.pack_propagate(False)

        self.button_2_label = tk.Label(self.button_2_frame, text="Button 2", font=("Arial", 14, "bold"), bg='white')
        self.button_2_label.pack(pady=(8, 2))
        self.button_2_pin = tk.Label(self.button_2_frame, text="(P13)", font=("Arial", 8), bg='white', fg='#999')
        self.button_2_pin.pack()
        self.button_2_status = tk.Label(self.button_2_frame, text="Released", font=("Arial", 10), bg='white', fg='#666')
        self.button_2_status.pack()

        # Button 3 display (Joystick:bit P14 - replaces Button A)
        self.button_3_frame = tk.Frame(button_grid_bottom, bg='white', relief=tk.RAISED, borderwidth=3, width=130, height=80)
        self.button_3_frame.pack(side=tk.LEFT, padx=10)
        self.button_3_frame.pack_propagate(False)

        self.button_3_label = tk.Label(self.button_3_frame, text="Button 3", font=("Arial", 14, "bold"), bg='white')
        self.button_3_label.pack(pady=(8, 2))
        self.button_3_pin = tk.Label(self.button_3_frame, text="(P14/E)", font=("Arial", 8), bg='white', fg='#999')
        self.button_3_pin.pack()
        self.button_3_status = tk.Label(self.button_3_frame, text="Released", font=("Arial", 10), bg='white', fg='#666')
        self.button_3_status.pack()

        # Button 4 display (Joystick:bit P15)
        self.button_4_frame = tk.Frame(button_grid_bottom, bg='white', relief=tk.RAISED, borderwidth=3, width=130, height=80)
        self.button_4_frame.pack(side=tk.LEFT, padx=10)
        self.button_4_frame.pack_propagate(False)

        self.button_4_label = tk.Label(self.button_4_frame, text="Button 4", font=("Arial", 14, "bold"), bg='white')
        self.button_4_label.pack(pady=(8, 2))
        self.button_4_pin = tk.Label(self.button_4_frame, text="(P15)", font=("Arial", 8), bg='white', fg='#999')
        self.button_4_pin.pack()
        self.button_4_status = tk.Label(self.button_4_frame, text="Released", font=("Arial", 10), bg='white', fg='#666')
        self.button_4_status.pack()

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
        print(f"🎨 Updating GUI: Button {button} -> {'PRESSED' if pressed else 'Released'}")

        try:
            # Get the appropriate frame, label, pin label, and status widgets
            if button == 'B':
                frame = self.button_b_frame
                label = self.button_b_label
                pin_label = self.button_b_pin
                status = self.button_b_status
                color = '#e74c3c'  # Red for special/emergency button
            elif button == '1':
                frame = self.button_1_frame
                label = self.button_1_label
                pin_label = self.button_1_pin
                status = self.button_1_status
                color = '#667eea'  # Purple
            elif button == '2':
                frame = self.button_2_frame
                label = self.button_2_label
                pin_label = self.button_2_pin
                status = self.button_2_status
                color = '#667eea'  # Purple
            elif button == '3':
                frame = self.button_3_frame
                label = self.button_3_label
                pin_label = self.button_3_pin
                status = self.button_3_status
                color = '#667eea'  # Purple
            elif button == '4':
                frame = self.button_4_frame
                label = self.button_4_label
                pin_label = self.button_4_pin
                status = self.button_4_status
                color = '#667eea'  # Purple
            else:
                print(f"   ⚠️ Unknown button: {button}")
                return

            if pressed:
                frame.config(bg=color, relief=tk.SUNKEN)
                label.config(bg=color, fg='white')
                pin_label.config(bg=color, fg='white')
                status.config(text="PRESSED", bg=color, fg='white', font=("Arial", 10, "bold"))
            else:
                frame.config(bg='white', relief=tk.RAISED)
                label.config(bg='white', fg='black')
                pin_label.config(bg='white', fg='#999')
                status.config(text="Released", bg='white', fg='#666', font=("Arial", 10))

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

        elif uuid == BTN_B_UUID.lower():
            pressed = data[0] == 1
            self.button_b_pressed = pressed
            print(f"🔘 Button B notification: {'PRESSED' if pressed else 'released'} (data={data[0]})")
            self.root.after(0, lambda p=pressed: self.update_button_display('B', p))

        elif uuid == BTN_1_UUID.lower():
            pressed = data[0] == 1
            self.button_1_pressed = pressed
            print(f"🔘 Button 1 notification: {'PRESSED' if pressed else 'released'} (data={data[0]})")
            self.root.after(0, lambda p=pressed: self.update_button_display('1', p))

        elif uuid == BTN_2_UUID.lower():
            pressed = data[0] == 1
            self.button_2_pressed = pressed
            print(f"🔘 Button 2 notification: {'PRESSED' if pressed else 'released'} (data={data[0]})")
            self.root.after(0, lambda p=pressed: self.update_button_display('2', p))

        elif uuid == BTN_3_UUID.lower():
            pressed = data[0] == 1
            self.button_3_pressed = pressed
            print(f"🔘 Button 3 notification: {'PRESSED' if pressed else 'released'} (data={data[0]})")
            self.root.after(0, lambda p=pressed: self.update_button_display('3', p))

        elif uuid == BTN_4_UUID.lower():
            pressed = data[0] == 1
            self.button_4_pressed = pressed
            print(f"🔘 Button 4 notification: {'PRESSED' if pressed else 'released'} (data={data[0]})")
            self.root.after(0, lambda p=pressed: self.update_button_display('4', p))

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
                b_data = await client.read_gatt_char(BTN_B_UUID)
                btn_1_data = await client.read_gatt_char(BTN_1_UUID)
                btn_2_data = await client.read_gatt_char(BTN_2_UUID)
                btn_3_data = await client.read_gatt_char(BTN_3_UUID)
                btn_4_data = await client.read_gatt_char(BTN_4_UUID)

                self.joystick_x = int.from_bytes(x_data, byteorder='little', signed=False)
                self.joystick_y = int.from_bytes(y_data, byteorder='little', signed=False)

                print(f"   X-axis: {self.joystick_x}")
                print(f"   Y-axis: {self.joystick_y}")
                print(f"   Button B: {b_data[0]} ({'PRESSED' if b_data[0] == 1 else 'released'})")
                print(f"   Button 1: {btn_1_data[0]} ({'PRESSED' if btn_1_data[0] == 1 else 'released'})")
                print(f"   Button 2: {btn_2_data[0]} ({'PRESSED' if btn_2_data[0] == 1 else 'released'})")
                print(f"   Button 3: {btn_3_data[0]} ({'PRESSED' if btn_3_data[0] == 1 else 'released'})")
                print(f"   Button 4: {btn_4_data[0]} ({'PRESSED' if btn_4_data[0] == 1 else 'released'})")

                self.root.after(0, lambda: self.x_value_label.config(text=str(self.joystick_x)))
                self.root.after(0, lambda: self.y_value_label.config(text=str(self.joystick_y)))
                self.root.after(0, lambda: self.update_joystick_visual(self.joystick_x, self.joystick_y))
                # Fix lambda closure - capture values with default arguments
                btn_b_initial = b_data[0] == 1
                btn_1_initial = btn_1_data[0] == 1
                btn_2_initial = btn_2_data[0] == 1
                btn_3_initial = btn_3_data[0] == 1
                btn_4_initial = btn_4_data[0] == 1
                self.root.after(0, lambda b=btn_b_initial: self.update_button_display('B', b))
                self.root.after(0, lambda b1=btn_1_initial: self.update_button_display('1', b1))
                self.root.after(0, lambda b2=btn_2_initial: self.update_button_display('2', b2))
                self.root.after(0, lambda b3=btn_3_initial: self.update_button_display('3', b3))
                self.root.after(0, lambda b4=btn_4_initial: self.update_button_display('4', b4))

                # Start notifications
                print("📡 Starting notifications...")
                await client.start_notify(X_CHAR_UUID, self.notification_handler)
                print("   ✅ X-axis notifications enabled")
                await client.start_notify(Y_CHAR_UUID, self.notification_handler)
                print("   ✅ Y-axis notifications enabled")
                await client.start_notify(BTN_B_UUID, self.notification_handler)
                print("   ✅ Button B notifications enabled")
                await client.start_notify(BTN_1_UUID, self.notification_handler)
                print("   ✅ Button 1 notifications enabled")
                await client.start_notify(BTN_2_UUID, self.notification_handler)
                print("   ✅ Button 2 notifications enabled")
                await client.start_notify(BTN_3_UUID, self.notification_handler)
                print("   ✅ Button 3 notifications enabled")
                await client.start_notify(BTN_4_UUID, self.notification_handler)
                print("   ✅ Button 4 notifications enabled")

                self.root.after(0, lambda: self.update_status("✅ Connected to microbit-joy!", "green"))
                self.root.after(0, lambda: self.connect_btn.config(text="Disconnect"))

                # Enable vibration buttons
                for btn in self.vibration_buttons:
                    self.root.after(0, lambda b=btn: b.config(state=tk.NORMAL))

                print("✅ Connection complete - monitoring joystick + 5 buttons")

                # Keep connection alive
                while self.connected:
                    await asyncio.sleep(0.1)

                # Disconnection requested - clean shutdown
                print("🔌 Disconnecting - stopping notifications...")
                try:
                    await client.stop_notify(X_CHAR_UUID)
                    await client.stop_notify(Y_CHAR_UUID)
                    await client.stop_notify(BTN_B_UUID)
                    await client.stop_notify(BTN_1_UUID)
                    await client.stop_notify(BTN_2_UUID)
                    await client.stop_notify(BTN_3_UUID)
                    await client.stop_notify(BTN_4_UUID)
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
