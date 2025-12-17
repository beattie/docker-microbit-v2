use embassy_sync::blocking_mutex::raw::ThreadModeRawMutex;
use embassy_sync::mutex::Mutex;
use heapless::String;

/// Device configuration that can be modified via BLE
#[derive(Clone, Debug)]
pub struct DeviceConfig {
    /// Joystick update rate in milliseconds (50-1000ms)
    pub update_rate_ms: u16,

    /// Whether LED blinking is enabled
    pub led_enabled: bool,

    /// BLE advertised device name (max 20 characters)
    pub device_name: String<20>,
}

impl Default for DeviceConfig {
    fn default() -> Self {
        Self {
            update_rate_ms: 100,
            led_enabled: true,
            device_name: String::try_from("microbit-joy").unwrap(),
        }
    }
}

/// Global shared configuration accessible from all tasks
pub static CONFIG: Mutex<ThreadModeRawMutex, DeviceConfig> =
    Mutex::new(DeviceConfig {
        update_rate_ms: 100,
        led_enabled: true,
        device_name: String::new(),
    });
