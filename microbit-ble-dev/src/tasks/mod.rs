//! Task modules
//!
//! This module organizes all async tasks:
//! - `led`: LED status indication
//! - `joystick`: Joystick and button input reading
//! - `ble`: BLE stack and connection handling

pub mod led;
pub mod joystick;
pub mod ble;

// Re-export task functions for convenience
pub use led::led_blink_task;
pub use joystick::{joystick_read_task, button_read_task};
pub use ble::{mpsl_task, ble_runner_task, ble_app_task};
