# 🦀 Rust Embedded Development for BBC micro:bit v2

The goal of this repository is to develop BLE examples for the [micro:bit v2](https://microbit.org) and the [joystick:bit](https://wiki.elecfreaks.com/en/microbit/expansion-board/joystick-bit-v2/).

A self-contained **Docker-based development environment** for building and running **Rust programs** on the **BBC micro:bit v2** (powered by the Nordic nRF52833).  These examples are based on examples from the [_Rust Embedded Discovery Book_](https://rust-embedded.github.io/discovery/microbit/index.html), including `03-setup` and `06-hello-world`.
`ble-example1` is extended from `03-setup` with input from `claude.ai` .

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
