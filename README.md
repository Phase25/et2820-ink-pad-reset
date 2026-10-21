# ET-28xx Waste Ink Pad Reset

A small console tool to **read and reset the waste ink pad counters** of the Epson EcoTank
ET-2820 and identical models, after the ink pad has been **physically replaced**.

English and German user interface (picked from the Windows display language, override with `--lang en` / `--lang de`).

> [!WARNING]
> **Use at your own risk.** Only reset the counters after replacing or cleaning the waste
> ink pad (or fitting an external waste ink bottle). Resetting the counter alone does not
> empty the pad: ink can overflow and damage the printer or your desk. Writing to the
> printer's EEPROM may void your warranty (see [Warranty](#warranty)). This project is not
> affiliated with or endorsed by Seiko Epson Corporation.

## Warranty

Replacing the waste ink pad yourself and writing to the printer's EEPROM **may void Epson's
manufacturer warranty**. Epson's warranty terms typically exclude damage caused by modification
by or on behalf of the end user, and treat waste ink pads as consumables that are not covered once
they reach the end of their service life (see for example
[Epson Australia's CoverPlus terms](https://www.epson.com.au/coverplus/terms/inkjetandmultifunctionstermsrtb.asp)).
Terms differ by country, so check the warranty conditions that apply to your printer before using
this tool, especially if it is still under warranty or registered for Epson's extended warranty.

In the EU, your statutory rights against the seller are not removed by this, but defects caused by
the modification will generally not be covered.

## Supported printers

Tested on hardware: **ET-2820** (reports itself as `ET-2820 Series`), firmware XE13Q2, over USB on Windows 11.

The model check allows the families `ET-281x`, `ET-282x`, `L325x`, `L326x`, which share the same
EEPROM layout and keys according to [reinkpy](https://codeberg.org/atufi/reinkpy). Only the
ET-2820 has been tested.

## Features

| Menu | What it does |
|---|---|
| 1) Status | Model, firmware, serial number, pad levels in % |
| 2) Backup | Saves EEPROM 0x000–0x1FF to `backups/` as JSON |
| 3) Reset | Checks the model, makes a backup, asks for confirmation, writes the counters to 0 and **reads them back** to verify |
| 4) Temporary reset | No key needed, lasts until the printer is switched off |
| 5) Restore | Writes the counter addresses back from a backup (only if the serial number matches) |

## Setup (Windows)

Requires Python 3.10+ and Git.

```
git clone --recursive https://github.com/Phase25/et2820-ink-pad-reset
cd et2820-ink-pad-reset
setup.bat
```

Then connect the printer **by USB cable** and run `start.bat`.

### Important: install the Epson printer driver

On Windows 11 a USB printer is often set up with the *Microsoft IPP Class Driver*. The printer's
USB interface then speaks IPP-over-USB (HTTP), and the Epson maintenance protocol (IEEE 1284.4 / D4)
gets **no answer at all** (`D4 Init failed`). Fix:

1. Install the official Epson printer driver for your model from Epson's website.
2. Remove the USB printer queue that uses the Microsoft IPP Class Driver.
3. Unplug and replug the USB cable.

### Why USB and not Wi-Fi?

Newer firmware blocks EEPROM access over the network (SNMP). Over USB it still worked on firmware XE13Q2.
Wi-Fi is still offered in the menu, but only works with older firmware.

## How it works

The tool is a thin wrapper around [epson_print_conf](https://github.com/Ircama/epson_print_conf)
(included as a git submodule) and [epson-usb](https://pypi.org/project/epson-usb/), using the
model parameters of the ET-2812 (read key `0x364A`, write key, counter addresses `0x1C`, `0x2F–0x37`,
`0xFC–0xFF`, completion flag `0x100`).

## Credits

- [epson_print_conf](https://github.com/Ircama/epson_print_conf) by Ircama (EUPL-1.2)
- [epson-usb](https://pypi.org/project/epson-usb/) by Onur Kesim and Ircama (MIT)
- [reinkpy](https://codeberg.org/atufi/reinkpy) for the model database

This project was created with the help of [Claude](https://claude.com/claude-code) (Anthropic), an AI assistant.

## License

[EUPL-1.2](LICENSE)
