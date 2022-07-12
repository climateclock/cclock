# cclock

CircuitPython implementation of the Climate Clock.

This codebase is known as "Action Clock v4."

## Overview

The production hardware target is the MatrixPortal M4:

    https://learn.adafruit.com/adafruit-matrixportal-m4

The core concept is the abstract `Frame` interface, which represents
a frame buffer of pixel data in memory.  Implementations of `Frame`
are specialized for a particular display device, and may choose their
own pixel representation to optimize for the target device.

## Firmware setup

This code is written to run on a custom build of the MatrixPortal
firmware that has several of the Adafruit libraries built-in,
to conserve RAM.  To install the firmware:

  - Connect your MatrixPortal to your computer with a USB cable.
  - Reset the board to bootloader mode by double-pressing the reset button.
  - A `MATRIXBOOT` volume should appear.
  - Copy the `firmware.uf2` file to the `MATRIXBOOT` volume.
  - After a moment, the board will reboot and a `CIRCUITPY` volume will appear.

## Running the clock

Once you have a `CIRCUITPY` volume visible, run:

    tools/matrix_run clock

This will copy all the Python source files to the MatrixPortal, which
should automatically restart and run the clock.  If necessary, you can
press the reset button once to restart the board.

## Building firmware

If you want to build the firmware image yourself:

    git clone https://github.com/zestyping/circuitpython
    cd circuitpython/ports/atmel-samd
    make -j8 V=1 BOARD=matrixportal_m4_cclock

This will produce the aforementioned `firmware.uf2` file.

## Development setup

You'll need Python 3.7 or higher.  To get started, run:

    tools/setup

to set up your Python virtual environment and install dependencies.

Once you have installed the clock program on the board, the startup
sequence will set the filesystem to be writable from CircuitPython,
which makes it non-writable over the USB cable.

To enable writing over USB, press the reset button once and then hold
down either of the other two buttons until the status light turns white.
The white light indicates that the board is now writable, so you can
run `tools/matrix_run clock` again to copy any of your local edits over
to the board.  The status light can be white or purple; the mnemonic is:

  - WhITE means you can WrITE files to the board over USB
  - PuRple means the board is in PRoduction mode, non-writable over USB

## Frame implementation notes

`sdl_frame.py` is an implementation of `Frame` that will run on standard
Python, using the SDL2 graphics library for display.

`matrix_frame.py` is a partial implementation of `Frame` that runs on
CircuitPython.  It's written for the Adafruit MatrixPortal M4, and
assumes that there is an attached grid of 192 x 32 pixels (HUB75 panels).

You can write one module and run it in both contexts.  Your module must
expose a run() function that takes a Frame instance as its one argument.
An example of such a module is `quilt.py`, provided as a simple demo;
you can run it like this:

    tools/sdl_run quilt

which will appear in a window on your computer, or like this:

    tools/matrix_run quilt

which will copy all the Python files onto an attached MatrixPortal board
(via the `CIRCUITPY` drive that appears on your computer when you connect
a USB cable to the board).  This will cause the MatrixPortal to reboot
and run your module.

`clock.py` is the Action Clock implementation.  You can run it in a window
on your computer with:

    tools/sdl_run clock

or run it on an attached MatrixPortal with:

    tools/matrix_run clock
