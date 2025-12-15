#![no_std]
#![no_main]

mod gatt;
mod tasks;

use defmt::{error, info};
use embassy_executor::Spawner;
use embassy_futures::select::select;
use microbit_bsp::{Config, Microbit};
use trouble_host::prelude::*;
use {defmt_rtt as _, panic_probe as _};

// Import GATT definitions from gatt module
use gatt::{CONNECTIONS_MAX, L2CAP_CHANNELS_MAX};

// Import task functions from tasks module
use tasks::{led_blink_task, joystick_read_task, button_read_task, mpsl_task, ble_runner_task, ble_app_task};

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    info!("=================================");
    info!("micro:bit v2 BLE Joystick");
    info!("=================================");

    let board = Microbit::new(Config::default());

    info!("Initializing peripherals...");

    // Spawn LED blink task
    match spawner.spawn(led_blink_task(board.display)) {
        Ok(_) => info!("✓ LED task spawned"),
        Err(_) => error!("✗ Failed to spawn LED task"),
    }

    // Spawn joystick reading task with ADC peripheral and pins
    info!("Spawning joystick task...");
    match spawner.spawn(joystick_read_task(board.saadc, board.p1, board.p2)) {
        Ok(_) => info!("✓ Joystick task spawned"),
        Err(_) => error!("✗ Failed to spawn joystick task"),
    }

    // Spawn button reading task
    info!("Spawning button task...");
    match spawner.spawn(button_read_task(board.btn_a, board.btn_b)) {
        Ok(_) => info!("✓ Button task spawned"),
        Err(_) => error!("✗ Failed to spawn button task"),
    }

    // Initialize BLE stack
    info!("Initializing BLE stack...");
    let (sdc, mpsl) = board
        .ble
        .init(board.timer0, board.rng)
        .expect("BLE Stack failed to initialize");

    // Spawn MPSL task
    spawner.must_spawn(mpsl_task(mpsl));
    info!("✓ MPSL task spawned");

    // Set up BLE host stack
    let address = Address::random([0x41, 0x5A, 0xE3, 0x1E, 0x10, 0xC9]);
    info!("BLE Address: {:?}", address);

    let mut resources: HostResources<DefaultPacketPool, CONNECTIONS_MAX, L2CAP_CHANNELS_MAX> =
        HostResources::new();
    let stack = trouble_host::new(sdc, &mut resources).set_random_address(address);

    let Host {
        peripheral, runner, ..
    } = stack.build();

    info!("✓ BLE Host stack created");
    info!("=================================");
    info!("✓ All tasks running!");
    info!("=================================");

    // Run BLE runner and application tasks concurrently
    select(ble_runner_task(runner), ble_app_task(peripheral)).await;
}
