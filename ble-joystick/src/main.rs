#![no_std]
#![no_main]

use defmt::*;
use embassy_executor::Spawner;
use microbit_bsp::*;
use {defmt_rtt as _, panic_probe as _};

#[embassy_executor::task]
async fn led_blink_task(mut display: display::LedMatrix<embassy_nrf::gpio::Output<'static>, 5, 5>) {
    info!("✓ LED matrix initialized");
    info!("Starting LED startup sequence...");

    // Create patterns for blinking using Frame directly
    let all_off = display::Frame::empty();
    
    let mut top_row = display::Frame::empty();
    top_row.set(0, 0);
    top_row.set(0, 1);
    top_row.set(0, 2);
    top_row.set(0, 3);
    top_row.set(0, 4);

    // Startup LED flash sequence - 3 quick blinks
    for i in 1..=3 {
        info!("Startup blink {}/3", i);
        display.display(top_row, embassy_time::Duration::from_millis(150)).await;
        display.display(all_off, embassy_time::Duration::from_millis(150)).await;
    }

    info!("✓ Startup complete!");
    info!("LED entering main blink loop...");

    // Main LED blink loop
    loop {
        display.display(top_row, embassy_time::Duration::from_millis(500)).await;
        display.display(all_off, embassy_time::Duration::from_millis(500)).await;
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    info!("=================================");
    info!("micro:bit v2 Starting...");
    info!("=================================");
    
    let board = Microbit::default();

    match spawner.spawn(led_blink_task(board.display)) {
        Ok(_) => info!("LED task spawned"),
        Err(_) => error!("Failed to spawn LED task"),
    }

    info!("✓ All tasks spawned");
    
    // Main task just waits forever
    loop {
        embassy_time::Timer::after(embassy_time::Duration::from_secs(1)).await;
    }
}
