#!/bin/bash
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia xvfb-run python main.py --enable_gpu --output images/screenshot_gpu_xvfb.png