#![no_std]
#![no_main]

use defmt::*;
use embassy_executor::Spawner;
use embassy_nrf::gpio::{Level, OutputDrive};
use nrf_softdevice::ble::peripheral;
use nrf_softdevice::Softdevice;
use {defmt_rtt as _, panic_probe as _};

// Required timestamp function for defmt
defmt::timestamp!("{=u64}", {
    0
});

// Simple blocking delay function (approximately 1ms at 64MHz)
fn delay_ms(ms: u32) {
    for _ in 0..ms {
        for _ in 0..8000 {
            cortex_m::asm::nop();
        }
    }
}

// Yielding delay that allows other tasks to run
async fn delay_ms_yielding(ms: u32) {
    const CHUNK_MS: u32 = 10;
    let chunks = ms / CHUNK_MS;
    let remainder = ms % CHUNK_MS;
    
    for _ in 0..chunks {
        delay_ms(CHUNK_MS);
        // Yield to other tasks by awaiting a future that returns Pending once
        struct Yield {
            yielded: bool,
        }
        
        impl core::future::Future for Yield {
            type Output = ();
            
            fn poll(mut self: core::pin::Pin<&mut Self>, cx: &mut core::task::Context<'_>) -> core::task::Poll<()> {
                if self.yielded {
                    core::task::Poll::Ready(())
                } else {
                    self.yielded = true;
                    cx.waker().wake_by_ref();
                    core::task::Poll::Pending
                }
            }
        }
        
        Yield { yielded: false }.await;
    }
    
    if remainder > 0 {
        delay_ms(remainder);
    }
}

// Advertising data must be in RAM for SoftDevice to access
#[link_section = ".data"]
static mut ADV_DATA: [u8; 13] = [
    0x02, 0x01, 0x06, // Flags: General Discoverable, BR/EDR not supported
    0x09, 0x09, b'm', b'i', b'c', b'r', b'o', b'b', b'i', b't', // Complete local name
];

#[link_section = ".data"]
static mut SCAN_DATA: [u8; 0] = [];

#[embassy_executor::task]
async fn led_blink_task() {
    // SAFETY: We're only accessing these pins once and SoftDevice doesn't use them
    use embassy_nrf::gpio::{AnyPin, Output as GpioOutput};
    
    let row1_pin = unsafe { AnyPin::steal(21) };
    let col1_pin = unsafe { AnyPin::steal(28) };
    
    let mut row1 = GpioOutput::new(row1_pin, Level::High, OutputDrive::Standard);
    let mut col1 = GpioOutput::new(col1_pin, Level::Low, OutputDrive::Standard);

    info!("✓ LED matrix initialized");
    info!("Starting LED startup sequence...");

    // Startup LED flash sequence - 3 quick blinks
    for i in 1..=3 {
        info!("Startup blink {}/3", i);
        row1.set_low();
        col1.set_high();
        delay_ms_yielding(150).await;
        
        row1.set_high();
        col1.set_low();
        delay_ms_yielding(150).await;
    }

    info!("✓ Startup complete!");
    info!("LED entering main blink loop...");

    // Main LED blink loop
    loop {
        row1.set_low();
        col1.set_high();
        delay_ms_yielding(1000).await;
        
        row1.set_high();
        col1.set_low();
        delay_ms_yielding(1000).await;
    }
}

#[embassy_executor::task]
async fn softdevice_task(sd: &'static Softdevice) -> ! {
    sd.run().await
}

#[embassy_executor::task]
async fn ble_task(sd: &'static Softdevice) {
    info!("BLE task entered!");
    
    // Give SoftDevice a moment to fully initialize
    for _ in 0..1_000_000 {
        cortex_m::asm::nop();
    }
    
    info!("Starting BLE advertising task");
    
    loop {
        let config = peripheral::Config::default();
        let adv = peripheral::ConnectableAdvertisement::ScannableUndirected {
            adv_data: unsafe { &*core::ptr::addr_of!(ADV_DATA) },
            scan_data: unsafe { &*core::ptr::addr_of!(SCAN_DATA) },
        };
        
        info!("BLE Advertising started - Device name: microbit");
        
        match peripheral::advertise_connectable(sd, adv, &config).await {
            Ok(_conn) => {
                info!("BLE Connected!");
                
                // Just wait - connection will stay alive until remote disconnects
                core::future::pending::<()>().await;
            }
            Err(e) => {
                error!("BLE Advertising error: {:?}", e);
            }
        }
        
        info!("Restarting advertising...");
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    info!("=================================");
    info!("micro:bit v2 Starting...");
    info!("=================================");
    
    let config = nrf_softdevice::Config {
        clock: Some(nrf_softdevice::raw::nrf_clock_lf_cfg_t {
            source: nrf_softdevice::raw::NRF_CLOCK_LF_SRC_RC as u8,
            rc_ctiv: 16,
            rc_temp_ctiv: 2,
            accuracy: nrf_softdevice::raw::NRF_CLOCK_LF_ACCURACY_500_PPM as u8,
        }),
        conn_gap: Some(nrf_softdevice::raw::ble_gap_conn_cfg_t {
            conn_count: 1,
            event_length: 24,
        }),
        conn_gatt: Some(nrf_softdevice::raw::ble_gatt_conn_cfg_t {
            att_mtu: 256,
        }),
        gatts_attr_tab_size: Some(nrf_softdevice::raw::ble_gatts_cfg_attr_tab_size_t {
            attr_tab_size: 32768,
        }),
        gap_role_count: Some(nrf_softdevice::raw::ble_gap_cfg_role_count_t {
            adv_set_count: 1,
            periph_role_count: 1,
            central_role_count: 0,
            central_sec_count: 0,
            _bitfield_1: nrf_softdevice::raw::ble_gap_cfg_role_count_t::new_bitfield_1(0),
        }),
        gap_device_name: Some(nrf_softdevice::raw::ble_gap_cfg_device_name_t {
            p_value: b"microbit" as *const u8 as _,
            current_len: 8,
            max_len: 8,
            write_perm: unsafe { core::mem::zeroed() },
            _bitfield_1: nrf_softdevice::raw::ble_gap_cfg_device_name_t::new_bitfield_1(
                nrf_softdevice::raw::BLE_GATTS_VLOC_STACK as u8,
            ),
        }),
        ..Default::default()
    };

    let sd = Softdevice::enable(&config);
    
    info!("✓ SoftDevice S140 initialized");
    
    match spawner.spawn(softdevice_task(sd)) {
        Ok(_) => info!("SoftDevice task spawned"),
        Err(_) => error!("Failed to spawn softdevice task"),
    }
    
    match spawner.spawn(ble_task(sd)) {
        Ok(_) => info!("BLE task spawned"),
        Err(_) => error!("Failed to spawn BLE task"),
    }
    
    match spawner.spawn(led_blink_task()) {
        Ok(_) => info!("LED task spawned"),
        Err(_) => error!("Failed to spawn LED task"),
    }

    info!("✓ All tasks spawned");
    info!("✓ BLE advertising will start shortly");
    
    // Main task just waits forever
    loop {
        core::future::pending::<()>().await;
    }
}
