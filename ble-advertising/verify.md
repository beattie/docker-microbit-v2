# Verify the installation

**NB this work was performed on a linux host**

## Verifying cargo-embed

First, connect the micro:bit to your Computer using a USB cable.

At least an orange LED right next to the USB port of the micro:bit should light up.  Furthermore, if you have never flashed another program on to your micro:bit, the default program the micro:bit ships with should start blinking the red LEDs on its back: you can ignore them, or you can play with the
demo app.

Now let's see if probe-rs, and by extensions cargo-embed can see your micro:bit. You can do this by
running the following command:

``` console
$ probe-rs list
The following debug probes were found:
[0]: BBC micro:bit CMSIS-DAP -- 0d28:0204:990636020005282030f57fa14252d446000000006e052820 (CMSIS-DAP)
```

Or if you want more information about the micro:bits debug capabilities then you can run:

``` console
$ probe-rs info
Probing target via JTAG

Error identifying target using protocol JTAG: The probe does not support the JTAG protocol.

Probing target via SWD

Arm Chip with debug port Default:
Debug Port: DPv1, DP Designer: Arm Ltd
├── 0 MemoryAP
│   └── ROM Table (Class 1), Designer: Nordic VLSI ASA
│       ├── Cortex-M4 SCS   (Generic IP component)
│       │   └── CPUID
│       │       ├── IMPLEMENTER: Arm Ltd
│       │       ├── VARIANT: 0
│       │       ├── PARTNO: Cortex-M4
│       │       └── REVISION: 1
│       ├── Cortex-M3 DWT   (Generic IP component)
│       ├── Cortex-M3 FBP   (Generic IP component)
│       ├── Cortex-M3 ITM   (Generic IP component)
│       ├── Cortex-M4 TPIU  (Coresight Component)
│       └── Cortex-M4 ETM   (Coresight Component)
└── 1 Unknown AP (Designer: Nordic VLSI ASA, Class: Undefined, Type: 0x0, Variant: 0x0, Revision: 0x0)


```

## Verifying BLE Advertising

### Build and Run
```bash
# Clean previous builds
cargo clean

# Build and flash
cargo run

### 3. Expected Output

You should see something like:

  Programming ✔ 100% [####################]  84.00 KiB @  12.63 KiB/s
      Finished in 10.07s
0.000000 [INFO] Starting micro:bit v2 BLE advertising
0.123456 [INFO] SoftDevice enabled, starting advertising loop
0.234567 [INFO] Starting advertisement
```

With the code running on the micro:bit a number of tools can be used to test the functioning of BLE. Here ```bluetoothctl``` is used.

```bash
bluetoothctl
scan on
```
This should result in something like:
```text
Agent registered
[bluetooth]# scan on
Discovery started
[CHG] Controller 40:23:43:88:25:E4 Discovering: yes
[NEW] Device EC:CA:C3:F4:5F:4C microbit
[NEW] Device 29:E0:0F:25:70:9E 29-E0-0F-25-70-9E

```
The line ending in "microbit" includes the MAC. Next we test connecting to the BLE device.
```bash
bluetoothctl
scan on
connect EC:CA:C3:F4:5F:4C
```
Pairing can also be tested.
```bash
bluetoothctl
scan on
pair EC:CA:C3:F4:5F:4C
```
