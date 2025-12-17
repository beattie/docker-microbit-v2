//! BLE stack tasks and connection handling
//!
//! This module contains all BLE-related tasks and helper functions:
//! - MPSL task (MultiProtocol Service Layer)
//! - BLE runner task
//! - Advertising and connection handling
//! - GATT characteristic notifications

use defmt::{info, warn, Debug2Format};
use embassy_futures::select::select;
use embassy_time::{Duration, Timer};
use microbit_bsp::ble::MultiprotocolServiceLayer;
use trouble_host::prelude::*;

// Import from gatt and config modules
use crate::config::CONFIG;
use crate::gatt::{JoystickServer, JOYSTICK_SIGNAL};

// MPSL task - required to run BLE stack
#[embassy_executor::task]
pub async fn mpsl_task(mpsl: &'static MultiprotocolServiceLayer<'static>) -> ! {
    mpsl.run().await
}

// BLE runner task - handles BLE protocol
pub async fn ble_runner_task<C: Controller, P: PacketPool>(
    mut runner: Runner<'_, C, P>,
) -> Result<(), BleHostError<C::Error>> {
    runner.run().await
}

// Advertise and wait for connection
async fn advertise<'a, 'b, C: Controller>(
    peripheral: &mut Peripheral<'a, C, DefaultPacketPool>,
    server: &'b JoystickServer<'_>,
) -> Result<GattConnection<'a, 'b, DefaultPacketPool>, BleHostError<C::Error>> {
    // Get device name from CONFIG
    let name = CONFIG.lock().await.device_name.clone();

    let mut advertiser_data = [0; 31];
    AdStructure::encode_slice(
        &[
            AdStructure::Flags(LE_GENERAL_DISCOVERABLE | BR_EDR_NOT_SUPPORTED),
            AdStructure::CompleteLocalName(name.as_bytes()),
        ],
        &mut advertiser_data[..],
    )?;

    let advertiser = peripheral
        .advertise(
            &Default::default(),
            Advertisement::ConnectableScannableUndirected {
                adv_data: &advertiser_data[..],
                scan_data: &[],
            },
        )
        .await?;

    info!("[BLE] Advertising as '{}'...", name.as_str());
    let conn = advertiser.accept().await?.with_attribute_server(server)?;
    info!("[BLE] Connection established!");
    Ok(conn)
}

// Handle GATT connection and send joystick notifications
async fn connection_task<P: PacketPool>(
    server: &JoystickServer<'_>,
    conn: &GattConnection<'_, '_, P>,
) {
    // Joystick service characteristics
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;
    let btn_b_char = server.joystick_service.button_b;

    // Battery service characteristic
    let batt_char = server.battery_service.battery_level;

    // Config service characteristics
    let update_rate_char = server.config_service.update_rate_ms;
    let led_enabled_char = server.config_service.led_enabled;
    let device_name_char = server.config_service.device_name;

    // Set initial joystick values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0u8);
    let _ = btn_b_char.set(server, &0u8);
    let _ = batt_char.set(server, &100u8);

    // Set initial config values from CONFIG
    {
        let config = CONFIG.lock().await;
        let _ = update_rate_char.set(server, &config.update_rate_ms);
        let _ = led_enabled_char.set(server, &(config.led_enabled as u8));

        // Convert heapless::String to [u8; 20]
        let mut name_bytes = [0u8; 20];
        let name_str = config.device_name.as_bytes();
        let len = name_str.len().min(20);
        name_bytes[..len].copy_from_slice(&name_str[..len]);
        let _ = device_name_char.set(server, &name_bytes);
    }

    info!("[BLE] Starting notification loop...");

    loop {
        // Use select to handle both GATT events and joystick updates
        let gatt_event_future = conn.next();
        let joystick_update_future = JOYSTICK_SIGNAL.wait();

        match select(gatt_event_future, joystick_update_future).await {
            embassy_futures::select::Either::First(event) => match event {
                GattConnectionEvent::Disconnected { reason } => {
                    info!("[BLE] Disconnected: {:?}", reason);
                    break;
                }
                GattConnectionEvent::Gatt { event } => {
                    // Handle WRITE events
                    if let GattEvent::Write(write_event) = &event {
                        let handle = write_event.handle();
                        let data = write_event.data();

                        info!("[BLE] Write to handle {}", handle);

                        // Handle update_rate_ms write
                        if handle == update_rate_char.handle {
                            if data.len() == 2 {
                                let new_rate = u16::from_le_bytes([data[0], data[1]]);

                                // Validate: 50ms to 1000ms
                                if new_rate >= 50 && new_rate <= 1000 {
                                    info!("[BLE] Setting update rate to {}ms", new_rate);
                                    CONFIG.lock().await.update_rate_ms = new_rate;
                                    let _ = update_rate_char.set(server, &new_rate);
                                    let _ = update_rate_char.notify(conn, &new_rate).await;
                                } else {
                                    warn!("[BLE] Invalid update rate: {} (rejected)", new_rate);
                                    // Revert to current valid value
                                    let current_rate = CONFIG.lock().await.update_rate_ms;
                                    let _ = update_rate_char.set(server, &current_rate);
                                    let _ = update_rate_char.notify(conn, &current_rate).await;
                                }
                            }
                        }
                        // Handle led_enabled write
                        else if handle == led_enabled_char.handle {
                            if data.len() == 1 && data[0] <= 1 {
                                let enabled = data[0] == 1;
                                info!("[BLE] Setting LED enabled: {}", enabled);
                                CONFIG.lock().await.led_enabled = enabled;
                                let _ = led_enabled_char.set(server, &data[0]);
                                let _ = led_enabled_char.notify(conn, &data[0]).await;
                            } else {
                                warn!("[BLE] Invalid LED enabled value (rejected)");
                                // Revert to current valid value
                                let current_enabled = CONFIG.lock().await.led_enabled;
                                let value = if current_enabled { 1u8 } else { 0u8 };
                                let _ = led_enabled_char.set(server, &value);
                                let _ = led_enabled_char.notify(conn, &value).await;
                            }
                        }
                        // Handle device_name write
                        else if handle == device_name_char.handle {
                            if data.len() <= 20 {
                                // Convert to heapless::String
                                if let Ok(name_str) = core::str::from_utf8(data) {
                                    if let Ok(new_name) = heapless::String::<20>::try_from(name_str) {
                                        info!("[BLE] Setting device name: {}", name_str);
                                        CONFIG.lock().await.device_name = new_name;

                                        let mut name_bytes = [0u8; 20];
                                        let len = data.len().min(20);
                                        name_bytes[..len].copy_from_slice(&data[..len]);
                                        let _ = device_name_char.set(server, &name_bytes);
                                        let _ = device_name_char.notify(conn, &name_bytes).await;

                                        info!("[BLE] Device name will change on next connection");
                                    } else {
                                        warn!("[BLE] Name too long");
                                    }
                                } else {
                                    warn!("[BLE] Invalid UTF-8 in device name");
                                }
                            }
                        }
                    }

                    // Accept the event (send response to client)
                    match event.accept() {
                        Ok(reply) => reply.send().await,
                        Err(e) => warn!("[BLE] Error sending response: {:?}", e),
                    }
                }
                _ => {}
            },
            embassy_futures::select::Either::Second(data) => {
                // Update characteristic values and notify
                let _ = x_char.set(server, &data.x);
                let _ = y_char.set(server, &data.y);
                let _ = x_char.notify(conn, &data.x).await;
                let _ = y_char.notify(conn, &data.y).await;
                let _ = btn_a_char.set(server, &data.button_a);
                let _ = btn_b_char.set(server, &data.button_b);
                let _ = btn_a_char.notify(conn, &data.button_a).await;
                let _ = btn_b_char.notify(conn, &data.button_b).await;
                let _ = batt_char.set(server, &data.battery_level);
                let _ = batt_char.notify(conn, &data.battery_level).await;
            }
        }
    }

    info!("[BLE] Connection task finished");
}

// Main BLE application task
pub async fn ble_app_task<C: Controller>(mut peripheral: Peripheral<'_, C, DefaultPacketPool>) {
    info!("[BLE] Creating GATT server...");

    let server = JoystickServer::new_with_config(GapConfig::Peripheral(PeripheralConfig {
        name: "microbit-joy",
        appearance: &appearance::power_device::GENERIC_POWER_DEVICE,
    }))
    .expect("Failed to create GATT server");

    info!("[BLE] GATT server created");

    loop {
        match advertise(&mut peripheral, &server).await {
            Ok(conn) => {
                connection_task(&server, &conn).await;
            }
            Err(e) => {
                let e = Debug2Format(&e);
                warn!("[BLE] Advertising error: {:?}", e);
                Timer::after(Duration::from_secs(1)).await;
            }
        }
    }
}
