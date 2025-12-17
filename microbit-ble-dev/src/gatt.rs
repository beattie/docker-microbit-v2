//! GATT service definitions for the micro:bit BLE Joystick
//!
//! This module defines the Bluetooth GATT services and characteristics
//! that the device exposes to connected clients.

use embassy_sync::blocking_mutex::raw::ThreadModeRawMutex;
use embassy_sync::signal::Signal;
use trouble_host::prelude::*;

// Joystick data structure for sharing between tasks
#[derive(Clone, Copy, Debug, defmt::Format)]
pub struct JoystickData {
    pub x: u16,            // 0-1023 range, center at 512
    pub y: u16,            // 0-1023 range, center at 512
    pub button_a: u8,      // 0 = released, 1 = pressed
    pub button_b: u8,      // 0 = released, 1 = pressed
    pub battery_level: u8, // 0-100
}

// Global signal for joystick data (always latest value)
pub static JOYSTICK_SIGNAL: Signal<ThreadModeRawMutex, JoystickData> = Signal::new();

// Max number of connections
pub const CONNECTIONS_MAX: usize = 1;

// Max number of L2CAP channels
pub const L2CAP_CHANNELS_MAX: usize = 2; // Signal + att

// BLE GATT Server definition
#[gatt_server]
pub struct JoystickServer {
    pub joystick_service: JoystickService,
    pub battery_service: BatteryService,
}

// Custom Joystick Service
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
pub struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    pub x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    pub y_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef3", read, notify)]
    pub button_a: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    pub button_b: u8,
}

// Standard Battery Service (Bluetooth SIG)
#[gatt_service(uuid = "180F")] // - Standard 16-bit UUID!
pub struct BatteryService {
    #[characteristic(uuid = "2A19", read, notify)]
    pub battery_level: u8, // 0-100%
}
