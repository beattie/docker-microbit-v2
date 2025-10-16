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
    //           1      2      3      4      5
    // Row 1  P0.21, P0.22, P0.15, P0.24, P0.19
    // Column P0.28, P0.11, P0.31, P1.05, P0.30
    let mut rowx = Output::new(p.P0_22, Level::High, OutputDrive::Standard);
    let mut colx = Output::new(p.P0_11, Level::Low, OutputDrive::Standard);

    info!("LED matrix initialized, starting blink loop");

    loop {
        info!("LED ON");
        rowx.set_low();   // Activate row
        colx.set_high();  // Activate column
        Timer::after_millis(1000).await;

        info!("LED OFF");
        rowx.set_high();  // Deactivate row
        colx.set_low();   // Deactivate column
        Timer::after_millis(1000).await;
    }
}
