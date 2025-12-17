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

// Import from gatt module
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
    name: &'a str,
    peripheral: &mut Peripheral<'a, C, DefaultPacketPool>,
    server: &'b JoystickServer<'_>,
) -> Result<GattConnection<'a, 'b, DefaultPacketPool>, BleHostError<C::Error>> {
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

    info!("[BLE] Advertising as '{}'...", name);
    let conn = advertiser.accept().await?.with_attribute_server(server)?;
    info!("[BLE] Connection established!");
    Ok(conn)
}

// Handle GATT connection and send joystick notifications
async fn connection_task<P: PacketPool>(
    server: &JoystickServer<'_>,
    conn: &GattConnection<'_, '_, P>,
) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;
    let btn_b_char = server.joystick_service.button_b;
    let batt_char = server.battery_service.battery_level;

    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0u8);
    let _ = btn_b_char.set(server, &0u8);
    let _ = batt_char.set(server, &100u8);

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
                GattConnectionEvent::Gatt { event } => match event.accept() {
                    Ok(reply) => reply.send().await,
                    Err(e) => warn!("[BLE] Error sending response: {:?}", e),
                },
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
        match advertise("microbit-joy", &mut peripheral, &server).await {
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
