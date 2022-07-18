# cclock

CircuitPython implementation of the Climate Clock.

This codebase is known as "Action Clock 4."

## Overview

To get yourself a running clock, obtain the necessary hardware and follow
the instructions below to install the firmware and software.

(For testing and development, you can also run the clock software just on
your laptop, without any extra hardware.  See the Development section below.)

### Hardware

The production board is the MatrixPortal M4, sold by Adafruit for $25:

    https://learn.adafruit.com/adafruit-matrixportal-m4

The production display is a grid of 192 by 32 pixels, made of three
HUB75 boards, each board with 64 by 32 pixels, chained together.

For input controls, you'll need:

  - An analog potentiometer, for brightness control (connect the
    left tap to ground, center tap to pin A1, and right tap to VCC).

  - A rotary encoder with a push switch, for making menu selections
    (connect the quadrature signals A and B to pins A2 and A3 respectively,
    connect C (common) to ground, and connect the momentary-close push
    switch between pin A4 and ground).

### Firmware

The clock requires a custom build of the MatrixPortal firmware that has several
of the Adafruit libraries built-in, to conserve RAM.  To install the firmware:

  - Connect the MatrixPortal to your computer with a USB cable.
  - Double-press the Reset button on the MatrixPortal to go to bootloader mode.
  - A `MATRIXBOOT` volume should appear.
  - Copy the `firmware.uf2` file to the `MATRIXBOOT` volume, and wait a bit.
  - `MATRIXBOOT` will disappear and eventually a `CIRCUITPY` volume will appear.

### Software

Once you have a `CIRCUITPY` volume visible, run:

    tools/matrix_run app

to copy all the software files to the MatrixPortal.

The clock should then automatically restart and run the installed software.
If necessary, you can press the reset button once to restart.

### Networking

To use the clock's network functionality, you'll need to get it connected
to the Internet.

The easiest way to get the clock online is to set up your phone as a Wi-Fi
hotspot with the network name `climateclock` and the password `climateclock`.
By default, the clock will use this name and password for its Wi-Fi connection.

Alternatively, see below for details on how to customize the network name
and password to join an existing Wi-Fi network.

## Development

### Setup

First, ensure that you have Python 3.7 or higher.  Then, run:

    tools/setup

to set up your Python virtual environment and install dependencies.

### Running locally

To run the clock in a window on your computer:

    tools/sdl_run app

This will substitute your computer's filesystem, network, and display, but
otherwise run the same code that runs in production, so you can test and
develop the clock display and user interaction.

### Writing over USB

After you run `tools/matrix_run` for the first time and restart the board,
`tools/matrix_run` will not work any more.  That's because the startup
sequence sets the filesystem to be writable from CircuitPython, which
makes it non-writable over the USB cable.

To enable writing over USB, press the reset button once and then hold
down either of the other two buttons until the status light turns red.
The red light indicates that the board is now writable, so you can
run `tools/matrix_run app` again to copy any of your local edits over
to the board.  The status light can be red or purple; the mnemonic is:

  - Red means you can wRite (or think of a red recording light)
  - PuRple means it's in PRoduction (non-writable over USB)

### Communicating with the MatrixPortal

The MatrixPortal has a serial console that is accessible over USB.
The "Mu Editor" app can bring up this console for you, or you can use
the GNU `screen` program.  To use `screen`, run it like
`screen /dev/tty... 115200`, replacing `/dev/tty...` with the serial
device that newly appears when you plug in the USB cable.  For example:

    screen /dev/tty.usbmodem1101 115200

If you are on MacOS, the utility `tools/con` will do this for you.

`print` statements will print to this serial console.  You can also
press Ctrl-C in the console to stop the running program, which will
put you in an interactive Python interpreter.

### Connecting to an existing Wi-Fi network

If you prefer to use an existing Wi-Fi network instead of creating a hotspot,
you can edit `prefs.json` to customize the network name and password.

First, put the board into writable mode by pressing the reset button and
holding down one of the other buttons until the status light turns red
(see the preceding section).  Then open `/Volumes/CIRCUITPY/prefs.json`
in a text editor, edit the network's SSID and password, and save the file.
Eject the `/Volumes/CIRCUITPY` drive from your computer, then press the
reset button to restart the board.

### Software update (under development)

The functionality to download software update packages over Wi-Fi is
currently under development.  A software update package is a single file
(with extension `.pk`) in a custom "pack" format, which is created using
`tools/pack`.

If you'd like to make your own software update package for the clock to
download, run `tools/pack` with a directory path as the first argument
and a package name (a "v" followed by a version number, such as "v17")
as the second argument; for example:

    tools/pack /tmp/folder/ v17 > v17.pk

Then make the resulting `cclock.pk` file available for download at
a HTTPS URL, put the hostname in the `connect_step()` call, and
put the hostname and path of the URL in the `PackFetcher()` call.

### Building firmware

The MatrixPortal firmware is already included in this repo as
`firmware.uf2`, so you shouldn't need to build the firmware yourself.
For the record, though, here's how you build the firmware:

    git clone https://github.com/zestyping/circuitpython
    cd circuitpython/ports/atmel-samd
    make -j8 V=1 BOARD=matrixportal_m4_cclock

### Implementation notes

The filesystem, display, and network subsystems are abstracted as
interfaces called FileSystem, Frame, and Network respectively.  Each one
is implemented both for the MatrixPortal and for a Unix environment,
and the appropriate implementation is passed in when the program starts.
See `tools/sdl_run` and `tools/matrix_run` for details on how these
implementations are instantiated and passed in.

The display is provided through the abstract `Frame` interface, which
represents a frame buffer of pixel data in memory.  Implementations of
`Frame` are specialized for a particular display device, and may choose
their own pixel representation to optimize for the target device.

`sdl_frame.py` is an implementation of `Frame` that will run on standard
Python, using the SDL2 graphics library for display.

`matrix_frame.py` is a partial implementation of `Frame` that runs on
CircuitPython.  It's written for the Adafruit MatrixPortal M4, and
assumes that there is an attached grid of 192 x 32 pixels (HUB75 panels).

You can write one main module and run it in both contexts.  Your module
must expose a run() function that takes a Frame instance as its one argument.
An example of such a module is `quilt.py`, provided as a simple demo;
you can run it like this:

    tools/sdl_run quilt

which will appear in a window on your computer, or like this:

    tools/matrix_run quilt

which will run the same module on an attached MatrixPortal board.

`app.py` is the Action Clock implementation.  You can run it in a window
on your computer with:

    tools/sdl_run app

or run it on an attached MatrixPortal with:

    tools/matrix_run app

