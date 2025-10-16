#![no_std]
#![no_main]

use defmt::*;
use embassy_executor::Spawner;
use embassy_nrf::gpio::{Level, Output, OutputDrive};
use embassy_time::Timer;
use {defmt_rtt as _, panic_probe as _};

// Required timestamp function for defmt
defmt::timestamp!("{=u64}", {
    0
});

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_nrf::init(Default::default());
    info!("Starting micro:bit LED flash example");

    // micro:bit v2 LED matrix - Row 1, Column 1 (top-left LED)
    // To light an LED: set the ROW low and the COLUMN high
    // Row 1 is P0.21
    // Column 1 is P0.28
    let mut row1 = Output::new(p.P0_21, Level::High, OutputDrive::Standard);
    let mut col1 = Output::new(p.P0_28, Level::Low, OutputDrive::Standard);

    info!("LED matrix initialized, starting blink loop");

    loop {
        info!("LED ON");
        row1.set_low();   // Activate row
        col1.set_high();  // Activate column
        Timer::after_millis(500).await;

        info!("LED OFF");
        row1.set_high();  // Deactivate row
        col1.set_low();   // Deactivate column
        Timer::after_millis(500).await;
    }
}
