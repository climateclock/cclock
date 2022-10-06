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

    tools/deploy

to wipe the MatrixPortal and perform a clean installation.  The current
code will be deployed as version 0 and preferences will be wiped (the
equivalent of a "factory reset").

Or you can deploy the current code without wiping the MatrixPortal:

    tools/deploy -q

This is a quicker way to write small code changes during development.
The clock should then automatically restart and run the updated code.
If necessary, you can press the reset button once to restart.

During development, the fastest way to try out your changes is to
simulate the clock in a window on your computer with:

    tools/sim

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

    tools/sim

This will substitute your computer's filesystem, network, and display, but
otherwise run the same code that runs in production, so you can test and
develop the clock display and user interaction.

### Writing over USB

After you run `tools/deploy` for the first time and restart the board, it
won't work a second time.  That's because the startup sequence sets the
filesystem to be writable from CircuitPython, which makes it non-writable
over the USB cable.

To enable writing over USB, press the reset button once and then hold
down either of the other two buttons until the status light turns red.
The red light indicates that the board is now writable, so you can
run `tools/deploy` again to copy any of your local edits over to the
board.  The status light can be red or purple; the mnemonic is:

  - Red means you can wRite (or think of a red recording light)
  - PuRple means it's in PRoduction (non-writable over USB)

When the light is red, `tools/deploy` will work.

### Communicating with the MatrixPortal

The MatrixPortal has a serial console that is accessible over USB.
The "Mu Editor" app can bring up this console for you, or you can use
the GNU `screen` program.  To use `screen`, run it like
`screen /dev/tty... 115200`, replacing `/dev/tty...` with the serial
device that newly appears when you plug in the USB cable.  For example:

    screen /dev/tty.usbmodem1101 115200

If you are on MacOS, the utility `tools/serial` will do this for you.
The session will be continuously logged to `screenlog.0`.

`print` statements will print to this serial console.  You can also
press Ctrl-C in the console to stop the running program, which will
put you in an interactive Python interpreter.

### Taking a screenshot of the display

You can get a screenshot of the display by double-clicking the UP button
on the MatrixPortal while the serial console is running.  This will dump
the screenshot as a long string of hex digits; running `tools/last_frame`
will then extract the last screenshot from `screenlog.0` and display it
on your computer screen.  This lets you see what would be on the display
even when you don't have any LED matrix boards attached.

### Connecting to an existing Wi-Fi network

If you prefer to use an existing Wi-Fi network instead of creating a hotspot,
you can edit `data/prefs.json` to customize the network name and password.

First, put the board into writable mode by pressing the reset button and
holding down one of the other buttons until the status light turns red
(see the preceding section).  Then open `/Volumes/CIRCUITPY/data/prefs.json`
in a text editor, edit the `wifi_ssid` and `wifi_password` values, and save
the file.  Eject the `/Volumes/CIRCUITPY` drive from your computer, then
press the reset button to restart the board.

### Software update

An Action Clock will periodically try to connect to Wi-Fi and check for
newer versions of its software.  First, it will fetch an "index file",
which is a JSON file listing the available software versions.

The index file is conventionally named `packs.json` and looks like this:

    {
      "name": "Action Clock by climateclock.world",
      "updated": "2022-07-17T18:51:03Z",
      "packs": {
        "v1": {
          "url": "https://zestyping.github.io/cclock/v1.f4a09eb4651480f7a20a2849544f80e2.pk",
          "hash": "f4a09eb4651480f7a20a2849544f80e2",
          "published": "2022-07-17T18:49:20Z",
          "enabled": true
        },
        "v2": {
          "url": "https://zestyping.github.io/cclock/v2.e5be85c68ae680dd2b8fe001e4d82798.pk",
          "hash": "e5be85c68ae680dd2b8fe001e4d82798",
          "published": "2022-07-18T07:29:37Z",
          "enabled": true
        },
        "v3": {
          "url": "https://zestyping.github.io/cclock/v3.eacbbf89c33d9be378a8c655a160194d.pk",
          "hash": "eacbbf89c33d9be378a8c655a160194d",
          "published": "2022-07-18T17:50:55Z",
          "enabled": true
        }
      }
    }

Each entry is identified by a version name (always a "v" followed by an
integer) and refers to a software update file (with extension `.pk`)
in a custom "pack" format, which is created using `tools/pack`.  Each
entry also has an `enabled` flag; the Action Clock will always try to
run the latest enabled version.  Thus, when the `enabled` flag is flipped
to `false`, it has the effect of retracting a published version and
causing Action Clocks in the field to downgrade to a previous version.

When we talk about v0, we are referring to the contents of the root
directory of the flash drive on a factory-installed Action Clock.
Each pack file is an overlay over v0, NOT over the preceding version.
Specifically, each Python module (`*.py`) and each font file (`*.mcf`)
overrides the file of the same name in the root directory of the flash
drive.  Therefore, once the first Action Clock is released, v0 must be
set in stone; the root directory must never be changed henceforth, in
order to ensure that every subsequent version has a consistent meaning on
every deployed Action Clock.  (Of course, a future version might improve
the software update mechanism to allow for a different policy.  For now,
the use of v0 as a base layer, upon which all other versions are overlaid,
is merely a simple space-saving measure.)

The steps for publishing a new software update are as follows:

  - Run `tools/pack` with a directory path as the first argument and
    a version name (a "v" followed by a version number, such as "v17")
    as the second argument; for example:

        tools/pack /tmp/folder v17

    A file with a name like `v17.d41d8cd98f00b204e9800998ecf8427e.pk'
    will be created, containing all the files in the specified folder.
    The string of 32 hex digits is the MD5 hash of the folder contents.

  - Publish the new `.pk` file at an HTTPS URL.

  - Add an entry to the index file under the `"packs"` key, whose key
    is the version name, and whose value is an object containing the
    keys: `"url"` (the URL to your pack file), `"hash" (the 32-digit
    hash in the file name), and `"enabled"` (set to `true`).

  - Publish the new index file at the HTTPS URL (the official update URL).

The "official update URL" has not been designated yet; it is configured
in `data/prefs.json` as the `update_url` entry.  For development, it defaults
to `https://zestyping.github.io/cclock/packs.json`.  If you are working
on this feature, you can set `update_url` to point to your own server by
editing `data/prefs.json` on the Action Clock's flash drive.

### Building firmware

The MatrixPortal firmware is already included in this repo as
`firmware.uf2`, so you shouldn't need to build the firmware yourself.
For the record, though, here's how you build the firmware:

    git clone https://github.com/zestyping/circuitpython
    cd circuitpython
    git checkout cclock_v8
    make fetch-submodules
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install -r requirements-dev.txt
    cd ports/atmel-samd
    make -j8 V=1 BOARD=matrixportal_m4_cclock

### Implementation notes

The filesystem, display, and network subsystems are abstracted in modules
named fs, display, and network respectively.  Memory is tight on the
MatrixPortal, so each module is implemented for the MatrixPortal by default,
with hooks allowing it to be configured or monkey-patched to run in a Unix
environment.   Memory conservation is also the reason that these are written
as modules with global variables, rather than classes with instance variables.

On the MatrixPortal, `start.py` initializes the app.  Its counterpart,
`tools/sim`, applies patches and starts the app in a Unix environment.

The display is backed by a displayio.Bitmap object, held by the App object.
All the user interface routines paint into the app's bitmap and then call
`display.send()` to show the contents of the bitmap on the display.
