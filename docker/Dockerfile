# Use a recent Ubuntu LTS
FROM ubuntu:24.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential build tools and system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pkg-config \
    libssl-dev \
    libudev-dev \
    libusb-1.0-0-dev \
    cmake \
    unzip \
	libclang-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust using rustup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Add embedded target for ARM Cortex-M (for micro:bit v2)
RUN rustup target add thumbv7em-none-eabihf

# Install useful cargo tools for embedded development
RUN cargo install cargo-binutils && rustup component add llvm-tools-preview

# Install probe-rs CLI for flashing and debugging microcontrollers
RUN cargo install probe-rs-tools --locked

# Set up a workspace directory
WORKDIR /workspace

# Default entrypoint
CMD ["/bin/bash"]

