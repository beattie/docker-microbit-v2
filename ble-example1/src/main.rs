#![no_main]
#![no_std]

use panic_rtt_target as _;
use nrf52833_pac::{self as pac, Peripherals};
use rtt_target::{rprintln, rtt_init_print};
use cortex_m_rt::entry;

// BLE Advertising packet structure
struct BleAdvertiser {
    radio: pac::RADIO,
    timer: pac::TIMER0,
}

impl BleAdvertiser {
    fn new(radio: pac::RADIO, timer: pac::TIMER0) -> Self {
        Self { radio, timer }
    }

    fn init(&mut self) {
        // Configure RADIO for BLE 1Mbps
        unsafe {
            // Set mode to BLE 1Mbps
            self.radio.mode.write(|w| w.mode().ble_1mbit());
            
            // Set frequency to channel 37 (2402 MHz)
            self.radio.frequency.write(|w| w.frequency().bits(2));
            
            // Configure packet format
            self.radio.pcnf0.write(|w| {
                w.s0len().bit(true)  // 1 byte S0
                 .lflen().bits(8)     // 8-bit length field
                 .s1len().bits(0)     // No S1
            });
            
            self.radio.pcnf1.write(|w| {
                w.maxlen().bits(37)   // Max payload length
                 .statlen().bits(0)   // No static length
                 .balen().bits(3)     // Base address length
                 .endian().little()   // Little endian
                 .whiteen().enabled() // Enable whitening
            });
            
            // Set base address
            self.radio.base0.write(|w| w.bits(0x89BED600));
            
            // Set prefix
            self.radio.prefix0.write(|w| w.ap0().bits(0x8E));
            
            // Set TX address to use logical address 0
            self.radio.txaddress.write(|w| w.txaddress().bits(0));
            
            // Set CRC configuration
            self.radio.crccnf.write(|w| {
                w.len().three()       // 3 bytes
                 .skipaddr().skip()   // Skip address
            });
            
            // CRC polynomial
            self.radio.crcpoly.write(|w| w.crcpoly().bits(0x00065B));
            
            // CRC init value
            self.radio.crcinit.write(|w| w.crcinit().bits(0x555555));
            
            // Set TX power to 0 dBm
            self.radio.txpower.write(|w| w.txpower().bits(0));
        }
    }

    fn send_advertising_packet(&mut self, packet: &[u8]) {
        unsafe {
            // Set packet pointer
            self.radio.packetptr.write(|w| w.bits(packet.as_ptr() as u32));
            
            // Clear events
            self.radio.events_ready.write(|w| w.bits(0));
            self.radio.events_end.write(|w| w.bits(0));
            
            // Start transmission
            self.radio.tasks_txen.write(|w| w.bits(1));
            
            // Wait for READY event
            while self.radio.events_ready.read().bits() == 0 {}
            
            // Clear READY event
            self.radio.events_ready.write(|w| w.bits(0));
            
            // Start TX
            self.radio.tasks_start.write(|w| w.bits(1));
            
            // Wait for END event
            while self.radio.events_end.read().bits() == 0 {}
            
            // Disable radio
            self.radio.tasks_disable.write(|w| w.bits(1));
        }
    }

    fn delay_ms(&mut self, ms: u32) {
        unsafe {
            // Configure timer: 32-bit, 1MHz (prescaler = 4: 16MHz / 2^4 = 1MHz)
            self.timer.mode.write(|w| w.mode().timer());
            self.timer.bitmode.write(|w| w.bitmode()._32bit());
            self.timer.prescaler.write(|w| w.prescaler().bits(4));
            
            // Clear timer
            self.timer.tasks_clear.write(|w| w.bits(1));
            
            // Set compare value (1MHz = 1us per tick, so ms * 1000)
            self.timer.cc[0].write(|w| w.bits(ms * 1000));
            
            // Clear compare event
            self.timer.events_compare[0].write(|w| w.bits(0));
            
            // Start timer
            self.timer.tasks_start.write(|w| w.bits(1));
            
            // Wait for compare event
            while self.timer.events_compare[0].read().bits() == 0 {}
            
            // Stop timer
            self.timer.tasks_stop.write(|w| w.bits(1));
        }
    }
}

// Create BLE advertising packet
fn create_adv_packet(buffer: &mut [u8; 64], name: &[u8]) -> usize {
    let mut idx = 0;
    
    // PDU Header (2 bytes): ADV_NONCONN_IND
    buffer[idx] = 0x42; // PDU Type and RFU
    idx += 1;
    buffer[idx] = 0; // Length (will be updated)
    idx += 1;
    
    // Advertising Address (6 bytes) - random static address
    buffer[idx..idx+6].copy_from_slice(&[0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]);
    idx += 6;
    
    let payload_start = idx;
    
    // AD Structure: Flags
    buffer[idx] = 2; // Length
    idx += 1;
    buffer[idx] = 0x01; // Type: Flags
    idx += 1;
    buffer[idx] = 0x06; // LE General Discoverable, BR/EDR not supported
    idx += 1;
    
    // AD Structure: Complete Local Name
    buffer[idx] = (name.len() + 1) as u8; // Length
    idx += 1;
    buffer[idx] = 0x09; // Type: Complete Local Name
    idx += 1;
    buffer[idx..idx+name.len()].copy_from_slice(name);
    idx += name.len();
    
    // Update length field (payload only, not including header and address)
    buffer[1] = ((idx - payload_start) + 6) as u8;
    
    idx
}

#[entry]
fn main() -> ! {
    rtt_init_print!();
    rprintln!("micro:bit v2 BLE Example");
    
    // Get peripherals
    let p = Peripherals::take().unwrap();
    
    // Initialize BLE advertiser
    let mut ble = BleAdvertiser::new(p.RADIO, p.TIMER0);
    ble.init();
    
    rprintln!("BLE initialized");
    
    // Create advertising packet
    let mut adv_packet = [0u8; 64];
    let name = b"micro:bit";
    let packet_len = create_adv_packet(&mut adv_packet, name);
    
    rprintln!("Advertising as '{}'", core::str::from_utf8(name).unwrap());
    
    let mut counter = 0u32;
    loop {
        // Send advertising packet
        ble.send_advertising_packet(&adv_packet[..packet_len]);
        
        counter += 1;
        if counter % 100 == 0 {
            rprintln!("Sent {} advertising packets", counter);
        }
        
        // Advertise every 100ms on channel 37
        ble.delay_ms(100);
        
        // Optional: rotate through advertising channels 37, 38, 39
        // (This example just uses channel 37 for simplicity)
    }
}
