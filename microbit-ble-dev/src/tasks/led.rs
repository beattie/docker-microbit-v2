use defmt::info;
use embassy_time::{Duration, Timer};
use microbit_bsp::display;

use crate::config::CONFIG;

#[embassy_executor::task]
pub async fn led_blink_task(
    mut display: display::LedMatrix<embassy_nrf::gpio::Output<'static>, 5, 5>,
) {
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
        display.display(top_row, Duration::from_millis(150)).await;
        display.display(all_off, Duration::from_millis(150)).await;
    }

    info!("✓ Startup complete!");
    info!("LED entering main blink loop...");

    // Main LED blink loop - slower to indicate system running
    // Can be disabled via BLE configuration
    loop {
        // Check if LED is enabled
        let enabled = {
            let config = CONFIG.lock().await;
            config.led_enabled
        };

        if enabled {
            // LED enabled - normal blinking
            display.display(top_row, Duration::from_millis(500)).await;
            display.display(all_off, Duration::from_millis(500)).await;
        } else {
            // LED disabled - keep it off and just wait
            display.display(all_off, Duration::from_millis(1)).await;
            Timer::after(Duration::from_millis(500)).await;
        }
    }
}
