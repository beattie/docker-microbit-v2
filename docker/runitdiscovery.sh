#!/bin/sh

echo "run docker with ~/git/discovery-mb2 mounted"

docker run --rm -it --privileged \
	-v "$(dirname "$(realpath "$0")")"/..:/workspace \
	-v ~/git/discovery-mb2:/workspace/discovery-mb2 \
	microbit-v2-dev
