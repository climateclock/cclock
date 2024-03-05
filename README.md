# cclock

CircuitPython implementation of the Climate Clock.

## Overview

To get yourself a running clock, obtain the necessary hardware and follow
the instructions below to install the firmware and software.

For testing and development, you can run the clock software just on your
laptop, without any extra hardware; see "Running the simulator" below.

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

First, ensure that you have Python 3.7 or higher.  Then, run:

    tools/setup

to set up your Python virtual environment and install dependencies.

Plug in your board.  Once you have a `CIRCUITPY` volume visible, run:

    tools/deploy -f

to wipe the MatrixPortal and perform a clean installation.  The current
code will be deployed as version v999 and preferences will be wiped (the
equivalent of a "factory reset").

### Networking

To use the clock's network functionality, you'll need to get it connected
to the Internet.

The easiest way to get the clock online is to set up your phone as a Wi-Fi
hotspot with the network name `climateclock` and the password `climateclock`.
By default, the clock will use this name and password for its Wi-Fi connection.

Alternatively, you can use the settings menu on the clock to enter a network
name and password.  Press the rotary encoder to open the settings menu, then
press to select "Wi-Fi setup", then select "Network" and type in the name of
your Wi-Fi network, then select "Password" and type in your Wi-Fi password.

### Factory reset

To perform a factory reset on your clock, press the tiny RESET button on the
board and then hold down either of the other two buttons.  Keep holding and
wait for the status light to pulse red 5 times (once per second, for 5 seconds)
and turn fuchsia ([F]uchsia indicates a [F]actory reset), and then release the
buttons.  The light will briefly turn yellow while the factory reset is in
progress, and then green to indicate success.  Your clock is now restored to
its state immediately after initial deployment.

If the board is installed inside an actual Action Clock case, you can also do
this using just the external knobs, without opening the case.  Turn the power
knob all the way down to power the clock off and back on, then press and hold
the menu knob until the status light pulses red 5 times and turns fuchsia.

## Development

To get started, be sure you have run `tools/setup` as described above.

### Running the simulator

This codebase includes a simulation environment that lets you run the clock
just on your computer, so you can do development even if you don't have any
of the clock hardware.  Even if you do have clock hardware, using the
simulator is usually the fastest way to try out your changes and iterate.

The simulation environment substitutes your computer's filesystem, network,
and display, but otherwise runs the same code that runs in production.  The
`/tmp/cclock` directory is used as the filesystem, and you will first need
to deploy the code to that location before you can run the simulator.

To deploy the code to the simulator, run `deploy` with the `-s` option:

    tools/deploy -s -f

To run the simulator:

    tools/sim

When you make changes to the code during development, you will need to
deploy again with `tools/deploy -s -f` in order to see your changes in
the simulator.

The simulated clock will save the clock definition and user settings to
files in `/tmp/cclock`, just as the real clock saves these files on its
flash disk.  Also, the simulated clock can download and install updates
to its own software, and writes these to directories in `/tmp/cclock`,
again just as the real clock installs updates to its flash disk.  When
you run `tools/sim`, the simulated clock will launch the latest available
installed version of the software, just as the real clock does.

### Connecting to an existing Wi-Fi network

If you prefer to use an existing Wi-Fi network instead of creating a hotspot,
you can specify a network name and password when you deploy:

    tools/deploy -f -w NetworkName:SecretPassword

This will factory-reset the board in every respect except that prefs.json
will be initialized to contain the given Wi-Fi network name and password.

### Writing changes to the board over USB

After you run `tools/deploy` for the first time and restart the board, it
won't work a second time.  That's because the startup sequence sets the
filesystem to be writable from CircuitPython, which makes it non-writable
over the USB cable.

To enable writing over USB, press the tiny RESET button on the board and then
hold down either of the other two buttons until the status light turns red.
If the board is inside an Action Clock, you can also do this using just the
external knobs: turn the power knob all the way down to power the clock off
and back on, then press and hold the menu knob until the light turns red.

The red light indicates that the board is now writable, so you can
run `tools/deploy` again to copy any of your local edits over to the
board.  The status light can be red or blue; the mnemonic is:

  - Red means you can wRite (or think of a red recording light)
  - Blue means it's in Broduction (non-writable over USB)

When the light is red, `tools/deploy` will work.

### Communicating with the MatrixPortal

The MatrixPortal has a serial console that is accessible over USB.
The "Mu Editor" app can bring up this console for you, or you can use
the GNU `screen` program.  To use `screen`, run it like
`screen /dev/tty... 115200`, replacing `/dev/tty...` with the serial
device that newly appears when you plug in the USB cable.  For example:

    screen /dev/tty.usbmodem1101 115200

If you are on MacOS or Linux, the utility `tools/serial` will do this
for you.  The session will be continuously logged to `screenlog.0`.

`print` statements in the code will print to this serial console.
You can also press Ctrl-C in the console to stop the running program,
which will put you in an interactive Python interpreter.

### Taking a screenshot of the display

You can get a screenshot of the display by double-clicking the UP button
on the MatrixPortal while the serial console is running.  This will dump
the screenshot as a long string of hex digits; running `tools/last_frame`
will then extract the last screenshot from `screenlog.0` and display it
on your computer screen.  This lets you see what would be on the display
even when you don't have any LED matrix boards attached.

### Software update

The clock will periodically try to connect to Wi-Fi, synchronize its RTC
using NTP, download the API file from `api.climateclock.world`, and check for
newer versions of its software.

To check for new versions, it fetches an "index file", which is a JSON
file listing the available software versions.

The index file is conventionally named `packs.json` and looks like this:

    {
      "name": "Action Clock by climateclock.world",
      "updated": "2022-10-18T05:41:09Z",
      "packs": {
        "v1": {
          "url": "https://zestyping.github.io/cclock/v1.f4a09eb4651480f7a20a2849544f80e2.pk",
          "hash": "f4a09eb4651480f7a20a2849544f80e2",
          "published": "2022-07-17T18:49:20Z",
          "enabled": true
        },
        "v2-v0": {
          "url": "https://zestyping.github.io/cclock/v2-v0.4e20c155e2ad7225a89acc3dca90418e.pk",
          "hash": "4e20c155e2ad7225a89acc3dca90418e",
          "published": "2022-10-07T06:49:29Z",
          "enabled": true
        },
        "v3-v0": {
          "url": "https://zestyping.github.io/cclock/v3-v0.c1b6a4b69bf2dcb61d49c1b1236e9b2b.pk",
          "hash": "c1b6a4b69bf2dcb61d49c1b1236e9b2b",
          "published": "2022-10-07T07:34:38Z",
          "enabled": true
        }
      }
    }

Each version is identified by a name (always a "v" followed by an
integer) and refers to a software update file (with extension `.pk`)
in a custom "pack" format, which is created using `tools/pack`.  Each
entry also has an `enabled` flag; the Action Clock will always try to
run the latest enabled version.  Thus, when the `enabled` flag is flipped
to `false`, it has the effect of retracting a published version and
causing Action Clocks in the field to downgrade to a previous version.

The entries in the index file can refer to "complete" packs or "patch"
packs.  In the example above, the "v1" pack is a complete distribution
of version "v1", containing all the files.  The "v2-v0" pack is a patch
distribution from "v0" to "v2", containing just the files that are new
or different in "v2" as compared to "v0".

Software versions are installed to version directories on the flash disk;
each directory has a name of the form `v<number>.<hash>`, which includes
an MD5 hash of the contents of the directory.  In the above example, "v1"
would be installed at `/v1.f4a09eb4651480f7a20a2849544f80e2`.

A factory-installed Action Clock always has a "v7" directory; performing
a factory reset deletes all the other version directories as well as the
`data` directory containing the user settings and any other downloaded
data files.  When each version is released, its hash and thus its contents
will be set in stone.  This makes it possible to release patch packs that
are overlays on top of fixed known previous versions of the software.

To publish a new software update, use `tools/release`.  To produce a
complete pack, run it with a version name and a Git tag or commit hash:

    tools/release v9 HEAD

This creates a file with a name like `v9.d41d8cd98f00b204e9800998ecf8427e.pk`.

To produce a patch pack, also provide a second, previous version name
and an older commit hash:

    tools/release v9 HEAD v7 6d92602

The result will have a name like `v9-v7.d41d8cd98f00b204e9800998ecf8427e.pk`.

If you use the `-u` option to specify the root URL where you plan to publish
the pack file, a JSON entry will also be printed out.  You can paste this
JSON entry into the index file, publish your new `.pk` file, and then
publish your new index file at the official update URL.

The "official update URL" is configured in `data/prefs.json` as the
`update_url` entry.  If you are working on software update functionality,
you can set `update_url` to point to your own server by editing
`data/prefs.json` on the Action Clock's flash drive.

### Building the firmware

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
named `fs.py`, `display.py`, and `network.py` respectively.  Memory is tight
on the MatrixPortal, so each module is implemented for the MatrixPortal by
default, with hooks allowing it to be configured or monkey-patched to run in
a Unix environment.   Memory conservation is also the reason these are written
as modules with global variables, rather than classes with instance variables.

The display is backed by a displayio.Bitmap object, held by the App object.
All the user interface routines paint into the app's bitmap and then call
`display.send()` to show the contents of the bitmap on the display.

On the board, the first file to run is `main.py`, which examines the available
software versions and launches the latest usable version.  It will catch
uncaught exceptions and disable the current version if it crashes, thus
automatically reverting to the previous version.  `tools/sim` sets up the
simulation environment and then runs `main.py`.
