#![no_std]
#![no_main]

use defmt::{info, error, unwrap};
use embassy_executor::Spawner;
use embassy_nrf as _;
use embassy_time::Timer;
use defmt_rtt as _;

// Panic handler for Rust panics
use core::panic::PanicInfo;

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    error!("Panic: {:?}", defmt::Debug2Format(info));
    cortex_m::asm::udf()
}

// Defmt panic handler (for defmt::panic! and defmt::unwrap!)
#[defmt::panic_handler]
fn defmt_panic() -> ! {
    cortex_m::asm::udf()
}

use nrf_softdevice::ble::peripheral;
use nrf_softdevice::{raw, Softdevice};

#[embassy_executor::task]
async fn softdevice_task(sd: &'static Softdevice) -> ! {
    sd.run().await
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    info!("Starting micro:bit v2 BLE advertising");

    let config = nrf_softdevice::Config {
        clock: Some(raw::nrf_clock_lf_cfg_t {
            source: raw::NRF_CLOCK_LF_SRC_XTAL as u8,
            rc_ctiv: 0,
            rc_temp_ctiv: 0,
            accuracy: raw::NRF_CLOCK_LF_ACCURACY_20_PPM as u8,
        }),
        conn_gap: Some(raw::ble_gap_conn_cfg_t {
            conn_count: 1,
            event_length: 6,
        }),
        conn_gatt: Some(raw::ble_gatt_conn_cfg_t { att_mtu: 128 }),
        gatts_attr_tab_size: Some(raw::ble_gatts_cfg_attr_tab_size_t {
            attr_tab_size: 32768,
        }),
        gap_role_count: Some(raw::ble_gap_cfg_role_count_t {
            adv_set_count: 1,
            periph_role_count: 1,
            central_role_count: 0,
            central_sec_count: 0,
            _bitfield_1: raw::ble_gap_cfg_role_count_t::new_bitfield_1(0),
        }),
        gap_device_name: Some(raw::ble_gap_cfg_device_name_t {
            p_value: b"micro:bit" as *const u8 as _,
            current_len: 9,
            max_len: 9,
            write_perm: unsafe { core::mem::zeroed() },
            _bitfield_1: raw::ble_gap_cfg_device_name_t::new_bitfield_1(
                raw::BLE_GATTS_VLOC_STACK as u8,
            ),
        }),
        ..Default::default()
    };

    let sd = Softdevice::enable(&config);
    
    unwrap!(spawner.spawn(softdevice_task(sd)));

    info!("SoftDevice enabled, starting advertising loop");

    loop {
        let config = peripheral::Config::default();
        
        let adv = peripheral::ConnectableAdvertisement::ScannableUndirected {
            adv_data: &[
                // Flags: BR/EDR not supported, LE General Discoverable
                0x02, 0x01, 0x06,
                // Complete local name
                0x0a, 0x09, b'm', b'i', b'c', b'r', b'o', b':', b'b', b'i', b't',
            ],
            scan_data: &[],
        };

        info!("Starting advertisement");
        
        match peripheral::advertise_connectable(sd, adv, &config).await {
            Ok(conn) => {
                info!("Connected! Connection handle: {:?}", conn.handle());
                
                // Just hold the connection open
                // In a real app, you'd do GATT operations here
                // For now, just wait a bit then let it drop (disconnect)
                Timer::after_secs(10).await;
                
                info!("Disconnecting and restarting advertising");
            }
            Err(e) => {
                error!("Advertising error: {:?}", e);
                Timer::after_secs(1).await;
            }
        }
    }
}
