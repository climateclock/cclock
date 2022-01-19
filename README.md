# cclock

CircuitPython implementation of the Climate Clock.

## Overview

The core concept is the abstract `Frame` interface, which represents
a frame buffer of pixel data in memory.  Implementations of `Frame`
are specialized for a particular display device, and may choose their
own pixel data type to optimize for the target device.

## Development

You'll need Python 3.7 or higher.  To get started, run:

    tools/setup

to set up your Python virtual environment and install dependencies.

At the moment, we just have one test script, quilt.py.  You can run it
with

    python3 quilt.py mpv

or

    python3 quilt.py sdl

to show the animated pixel matrix using mpv or SDL, respectively.
