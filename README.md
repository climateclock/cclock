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

## Running on Python (on your computer)

`mpv_frame.py` and `sdl_frame.py` are two implementations of `Frame` that
will run on standard Python.  You can exercise them with a test script,
quilt.py, by running:

    python3 quilt.py mpv

or

    python3 quilt.py sdl

to show an animated quilt pattern using mpv or SDL, respectively.

## Running on CircuitPython (on a MatrixPortal board)

`matrix_frame.py` is a partial implementation of `Frame` that runs on
CircuitPython.  It's written for the Adafruit MatrixPortal M4, and
assumes that there is an attached grid of 192 x 32 pixels (HUB75 panels).

To try it out, put the following in `code.py`, which runs exactly the same
code in `quilt.py` but on top of the `matrix_frame` implementation:

    import matrix_frame
    frame = matrix_frame.new_display_frame(192, 32, 64)
    import quilt
    quilt.run(frame)

and then copy all the `*.py` files to the `CIRCUITPY` drive that appears
when you connect your computer to the MatrixPortal board with a USB cable.

`clock.py` exercises the font rendering capabilities in `Frame` with
a few test strings and a countdown timer.  To run it, you would put the
following in `code.py`:

    import matrix_frame
    frame = matrix_frame.new_display_frame(192, 32, 64)
    import clock
    clock.run(frame)
