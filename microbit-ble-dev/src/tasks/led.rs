use defmt::info;
use embassy_time::Duration;
use microbit_bsp::display;

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
    loop {
        display.display(top_row, Duration::from_millis(500)).await;
        display.display(all_off, Duration::from_millis(500)).await;
    }
}
