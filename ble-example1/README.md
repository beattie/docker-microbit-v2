# Micro:bit V2 BLE example

This project is derived from `03-setup` to demonstrate how to build an example using the basic BLE(Bluetooth Low Energy) features of the Micro:bit v2 and it's Nordic nRF52833. 

## 🧩 1. Build and flash to your micro:bit v2

From your Rust embedded environment (inside Docker or directly on your host):

```bash
cargo run
```

That will flash your program and start running it on the board.
RTT output (“micro:bit v2 BLE Example”) will appear in your RTT terminal if you’re using probe-rs or cargo-embed.

---

## 🧠 2. Verify RTT debug output (optional)

If you have from inside Docker `cargo run`:

You should see:

```text
micro:bit v2 BLE Example
BLE initialized
Advertising as 'micro:bit'
Sent 100 advertising packets
...
```
That confirms the firmware is running and transmitting.

---

## 🛰️ 3. Use Linux tools to detect the BLE advertisements

On your Linux laptop, ensure Bluetooth is enabled and you have the BlueZ utilities installed:

```sudo apt install bluez bluez-hcidump```

Then scan for nearby BLE advertisers:
### Option A: Simple ```bluetoothctl``` scan

```bash
bluetoothctl
[bluetooth]# power on
[bluetooth]# scan on
```

Look for entries like:

```text
Device AA:BB:CC:DD:EE:FF (random)
Name: micro:bit
RSSI: -60
```

If you see ```"micro:bit"``` — success! 🎉 That’s your advertisement being broadcast by the micro:bit.
### Option B: Low-level scan using ```hcitool``` or ```hcitop```

To view raw advertising packets:

```bash
sudo hcitool lescan
```

or to dump the actual data fields:

sudo hcitool lescan --duplicates &
sudo hcidump -X

You’ll see hex dumps like:

```test
> 04 3E 2A 02 01 03 01 FF EE DD CC BB AA 1A 02 01 06 0A 09 6D 69 63 72 6F 3A 62 69 74
```

where:

*    ```AA BB CC DD EE FF``` → your advertising address
*    ```09 6D 69 63 72 6F 3A 62 69 74``` → “micro:bit” UTF-8 bytes

### Option C: Graphical scan with ```bluetoothctl``` or ```blueman```

If you prefer GUI:

```bash
sudo apt install blueman
blueman-manager
```

You’ll see ```micro:bit``` appear in nearby devices (though pairing won’t work — this is just advertising).
### ⚙️ 4. Optional: Analyze the advertisement payload

You can decode the bytes with btmon:

```bash
sudo btmon
```

Then power on scanning in another terminal:

```bash
bluetoothctl scan on
```

```btmon``` will print decoded BLE packets:

```text
> ADV_IND: AA:BB:CC:DD:EE:FF (Random)
    Flags: 0x06
    Complete Local Name: micro:bit
```

This confirms your advertisement matches the payload you built.
