# Fonts

To facilitate change tracking, fonts are source-controlled in BDF format.

(Ping is the designer of these fonts and will probably be the only one
editing them; the instructions below are mainly to document how they
are produced.)

## Editing

FontForge is a nice tool for editing these fonts.  To edit one of these
font files in FontForge:

  - In FontForge, click File > Open and open the BDF file.

  - Click File > Save As... and edit the filename to include the size
    (`kairon-10.sfd` or `kairon-16.sfd`).

Now you have a `.sfd` file such as `kairon-10.sfd` that you can safely open
and edit in FontForge.

When you are ready to commit your changes:

  - Click File > Generate Fonts...

  - The filename field should be prefilled with `kairon-*.bdf`.  You can
    navigate to other directories if you like, but leave the name unchanged.

  - Click Generate.

  - Click OK.

This produces a `.bdf` file such as `kairon-10.bdf` that you can commit
using Git in this directory.  When you commit a change to a BDF file,
please also run `compile_font` on it (see below) so that the corresponding
PCF file is up to date.

## Compiling

The fonts shipped with the Action Clock are in PCF format.  To compile a
BDF file into a PCF file, you will need the tool `bdftopcf`, which is
provided with X Windows (you'll get it if you install X11 or XQuartz).
Once you have this installed, simply run:

    tools/compile_font kairon-10.bdf

to produce the corresponding `kairon-10.pcf` file.  The `compile_font` tool
will perform some optimizations and error checks to produce a slimmer PCF
file and avoid erroneous rendering behaviour on the Action Clock; please use
`compile_font` instead of running `bdftopcf` directly.
