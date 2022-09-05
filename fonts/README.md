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

The fonts shipped with the Action Clock are in the "Microfont" format,
a small and efficient font format that was designed for this application.
See `microfont.py` for details on this format.  To compile a BDF file into
a Microfont file, use `compile_microfont`.  For example:

    tools/compile_microfont kairon-10.bdf

will produce a corresponding `kairon-10.mcf` file.  It will also check the
input and warn you if any metrics or bounding boxes seem wrong.
