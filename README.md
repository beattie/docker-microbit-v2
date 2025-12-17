# 🦀 Rust Embedded Development for BBC micro:bit v2

The goal of this repository is to develop BLE examples for the [micro:bit v2](https://microbit.org) and the [joystick:bit](https://wiki.elecfreaks.com/en/microbit/expansion-board/joystick-bit-v2/).

A self-contained **Docker-based development environment** for building and running **Rust programs** on the **BBC micro:bit v2** (powered by the Nordic nRF52833).  These examples are based on examples from the [_Rust Embedded Discovery Book_](https://rust-embedded.github.io/discovery/microbit/index.html), including `03-setup` and `06-hello-world`
`ble-example1` is extended from `03-setup` with input from `claude.ai` .
The `ble-advertising` project is a stepping stone to understanding BLE, while `ble-joystick` is a complete application demonstrating production BLE patterns with real sensor data.

The branch `HID_buttons` includes reading some _buttons_ and reporting them via **BLE**.

The project **microbit-ble-dev** includes the branches _micro-ble-dev-Phase1_, _micro-ble-dev-Phase2_, _micro-ble-dev-Phase3_ and _micro-ble-dev-Phase4_ which include changes exclusively in this project. This project covers the process of developing a _HID Jotstick_ using a **micro:bit + joystick:bit** and is intended as an educational project with an exploration of _generative AI_.

## 🐳 Quick Start
🖥️ Ubuntu Host Requirements
```bash
sudo apt update
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    build-essential \
    git \
    python3 \
    python3-pip \
    cmake \
    pkg-config \
    libusb-1.0-0-dev \
    udev \
    usbutils
```
### 1️⃣ Clone this repository
```bash
git clone https://github.com/beattie/docker-microbit-v2.git
cd docker-microbit-v2/docker
./builddocker.sh
```
### 2️⃣ Start container
```bash
cd docker-microbit-v2/docker
./runit.sh
```
