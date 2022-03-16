# cclock

CircuitPython implementation of the Climate Clock.

## Overview

The core concept is the abstract `Frame` interface, which represents
a frame buffer of pixel data in memory.  Implementations of `Frame`
are specialized for a particular display device, and may choose their
own pixel representation to optimize for the target device.

## Development setup

You'll need Python 3.7 or higher.  To get started, run:

    tools/setup

to set up your Python virtual environment and install dependencies.

## Frame implementations

`sdl_frame.py` is an implementation of `Frame` that will run on standard
Python, using the SDL2 graphics library for display.

`matrix_frame.py` is a partial implementation of `Frame` that runs on
CircuitPython.  It's written for the Adafruit MatrixPortal M4, and
assumes that there is an attached grid of 192 x 32 pixels (HUB75 panels).

## Running a module

You can write one module and run it in both contexts.  Your module must
expose a run() function that takes a Frame instance as its one argument.
An example of such a module is `quilt.py`, provided as a simple demo;
you can run it like this:

    tools/sdl_frame quilt

which will appear in a window on your computer, or like this:

    tools/matrix_frame quilt

which will copy all the Python files onto an attached MatrixPortal board
(via the `CIRCUITPY` drive that appears on your computer when you connect
a USB cable to the board).  This will cause the MatrixPortal to reboot
and run your module.

`clock.py` is a partial clock implementation that exercises the font
rendering methods in `Frame` by showing a countdown timer.  To run it,
you would run either `tools/sdl_frame clock` or `tools/matrix_frame clock`.
