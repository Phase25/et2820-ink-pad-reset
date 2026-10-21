"""Tintenauffangkissen-Zähler für Epson ET-2820 (und Baugleiche) auslesen und zurücksetzen.

Read and reset the waste ink pad counters of Epson ET-2820 (and identical models).

Nutzt epson_print_conf (vendor/epson_print_conf) und epson-usb.
"""
import argparse
import datetime
import json
import logging
import os
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER / "vendor" / "epson_print_conf"))
import epson_print_conf as epc  # noqa: E402

# ET-2820 hat dieselben Keys/Adressen wie ET-2812 (reinkpy führt ET-2810..2826,
# L3250..L3261 in einem gemeinsamen Eintrag: rkey 0x364A, wkey "Maribaya").
BASIS_MODELL = "ET-2812"
ERLAUBTE_FAMILIEN = ("ET-281", "ET-282", "L325", "L326")
BACKUP_ORDNER = HIER / "backups"
BACKUP_BEREICH = range(0x000, 0x200)  # enthält alle Zähler + Flag 0x100

TEXTE = {
    "de": {
        "titel": "=== Epson ET-2820 Tintenkissen-Tool ===",
        "verbindung": "\nVerbindung:",
        "usb": "  1) USB-Kabel (empfohlen)",
        "wlan": "  2) WLAN (IP-Adresse eingeben)",
        "auswahl_1": "Auswahl [1]: ",
        "ip": "IP-Adresse des Druckers: ",
        "main_waste": "Hauptkissen",
        "borderless_waste": "Randlos-Kissen",
        "third_waste": "Drittes Kissen",
        "unbekannt": "unbekannt",
        "nicht_lesbar": "  Füllstand nicht lesbar (EEPROM-Zugriff gesperrt?).",
        "modell": "  Modell:        {}",
        "firmware": "  Firmware:      {}",
        "serie": "  Seriennummer:  {}",
        "warn_modell": "  WARNUNG: Modell gehört nicht zur ET-281x/282x-Familie. Schreiben gesperrt.",
        "lese_eeprom": "\n  Lese EEPROM 0x{:03X}-0x{:03X} ...",
        "backup_fehler": "  Backup fehlgeschlagen: EEPROM nicht lesbar.",
        "gespeichert": "  Gespeichert: {}",
        "fehlend": "  Hinweis: {} Adressen nicht lesbar.",
        "drucker_zeile": "\n  Drucker: {}  |  Seriennummer: {}  |  Firmware: {}",
        "abbruch_modell": "  Abbruch: Modell nicht freigegeben.",
        "abbruch_lesen": "  Abbruch: Zähler nicht lesbar, also auch nicht schreibbar.",
        "tipp": "  Tipp: USB-Kabel nutzen oder Menüpunkt 'Temporärer Reset'.",
        "abbruch_backup": "  Abbruch: ohne Backup kein Reset.",
        "frage_reset": "\n  Zähler jetzt auf 0 setzen? '{}' eintippen: ",
        "abgebrochen": "  Abgebrochen.",
        "reset_ok": "\n  Reset geschrieben und nachgeprüft. Neuer Stand:",
        "neustart": "  Drucker jetzt aus- und wieder einschalten.",
        "reset_fehler": "\n  Reset FEHLGESCHLAGEN (Drucker hat Schreiben abgelehnt oder Wert verworfen).",
        "reset_fehler2": "  Siehe Meldungen oben. Backup liegt im Ordner 'backups'.",
        "frage_temp": "\n  Temporären Reset senden (hält bis zum Ausschalten)? '{}': ",
        "temp_ok": "  OK, Drucker sollte bis zum nächsten Ausschalten drucken.",
        "temp_fehler": "  Drucker hat den temporären Reset nicht bestätigt.",
        "keine_backups": "\n  Keine Backups vorhanden.",
        "nummer": "  Nummer: ",
        "abbruch_serie": "  Abbruch: Backup ist von Seriennummer {}, Drucker hat {}.",
        "abbruch_unvollst": "  Abbruch: Backup enthält nicht alle Zähler-Adressen.",
        "schreibt_zurueck": "  Schreibt nur die Zähler-Adressen zurück: {}",
        "fortfahren": "  Fortfahren? '{}': ",
        "fehler_adr": "  Fehler bei 0x{:03X}, Abbruch.",
        "wiederhergestellt": "  Wiederhergestellt.",
        "m_status": "Status (Modell, Firmware, Füllstand)",
        "m_backup": "Backup EEPROM",
        "m_reset": "Reset Zähler (mit Backup)",
        "m_temp": "Temporärer Reset (bis Ausschalten)",
        "m_restore": "Backup zurückspielen (nur Zähler)",
        "m_ende": "  0) Beenden",
        "auswahl": "Auswahl: ",
        "keine_verbindung": "  Keine Verbindung zum Drucker: {}",
        "ja": "JA",
    },
    "en": {
        "titel": "=== Epson ET-2820 Waste Ink Pad Tool ===",
        "verbindung": "\nConnection:",
        "usb": "  1) USB cable (recommended)",
        "wlan": "  2) Wi-Fi (enter IP address)",
        "auswahl_1": "Choice [1]: ",
        "ip": "Printer IP address: ",
        "main_waste": "Main pad",
        "borderless_waste": "Borderless pad",
        "third_waste": "Third pad",
        "unbekannt": "unknown",
        "nicht_lesbar": "  Levels not readable (EEPROM access locked?).",
        "modell": "  Model:         {}",
        "firmware": "  Firmware:      {}",
        "serie": "  Serial number: {}",
        "warn_modell": "  WARNING: model is not part of the ET-281x/282x family. Writing disabled.",
        "lese_eeprom": "\n  Reading EEPROM 0x{:03X}-0x{:03X} ...",
        "backup_fehler": "  Backup failed: EEPROM not readable.",
        "gespeichert": "  Saved: {}",
        "fehlend": "  Note: {} addresses not readable.",
        "drucker_zeile": "\n  Printer: {}  |  Serial number: {}  |  Firmware: {}",
        "abbruch_modell": "  Aborted: model not supported.",
        "abbruch_lesen": "  Aborted: counters not readable, so not writable either.",
        "tipp": "  Tip: use a USB cable or the 'Temporary reset' menu entry.",
        "abbruch_backup": "  Aborted: no reset without a backup.",
        "frage_reset": "\n  Reset counters to 0 now? Type '{}': ",
        "abgebrochen": "  Cancelled.",
        "reset_ok": "\n  Reset written and verified. New levels:",
        "neustart": "  Now switch the printer off and on again.",
        "reset_fehler": "\n  Reset FAILED (printer refused the write or discarded the value).",
        "reset_fehler2": "  See messages above. The backup is in the 'backups' folder.",
        "frage_temp": "\n  Send temporary reset (lasts until power off)? '{}': ",
        "temp_ok": "  OK, the printer should print until it is switched off.",
        "temp_fehler": "  Printer did not confirm the temporary reset.",
        "keine_backups": "\n  No backups found.",
        "nummer": "  Number: ",
        "abbruch_serie": "  Aborted: backup is from serial number {}, printer has {}.",
        "abbruch_unvollst": "  Aborted: backup does not contain all counter addresses.",
        "schreibt_zurueck": "  Writes back the counter addresses only: {}",
        "fortfahren": "  Continue? '{}': ",
        "fehler_adr": "  Error at 0x{:03X}, aborted.",
        "wiederhergestellt": "  Restored.",
        "m_status": "Status (model, firmware, levels)",
        "m_backup": "Backup EEPROM",
        "m_reset": "Reset counters (with backup)",
        "m_temp": "Temporary reset (until power off)",
        "m_restore": "Restore backup (counters only)",
        "m_ende": "  0) Quit",
        "auswahl": "Choice: ",
        "keine_verbindung": "  No connection to the printer: {}",
        "ja": "YES",
    },
}
T = TEXTE["de"]


def system_sprache():
    if sys.platform == "win32":
        import ctypes
        return "de" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x07 else "en"
    return "de" if os.environ.get("LANG", "").startswith("de") else "en"


def verbinden():
    print(T["verbindung"])
    print(T["usb"])
    print(T["wlan"])
    wahl = input(T["auswahl_1"]).strip() or "1"
    if wahl == "2":
        ip = input(T["ip"]).strip()
        if not ip:
            return None
        return epc.EpsonPrinter(model=BASIS_MODELL, hostname=ip)
    for zeile in epc.usb_interface_lines():
        print("  " + zeile)
    klasse = epc.enable_usb_transport()
    return klasse(model=BASIS_MODELL)


def identitaet(drucker):
    ident = drucker.get_device_identification() or {}
    modell = " ".join(ident.get("Model", [])) or "?"
    firmware = drucker.get_firmware_version() or "?"
    serie = drucker.get_serial_number()
    if not serie or not serie.isalnum():
        serie = (drucker.get_printer_status() or {}).get("serial_number_info") or "?"
    if not serie.isalnum():
        serie = T["unbekannt"]
    return modell, firmware, serie


def modell_ok(modell):
    return any(f in modell for f in ERLAUBTE_FAMILIEN)


def fuellstand_zeigen(drucker):
    stand = drucker.get_waste_ink_levels()
    if stand is None:
        print(T["nicht_lesbar"])
        return False
    for key, prozent in stand.items():
        print(f"  {T.get(key, key):<16} {prozent:6.2f} %")
    return True


def status(drucker):
    modell, firmware, serie = identitaet(drucker)
    print()
    print(T["modell"].format(modell))
    print(T["firmware"].format(firmware))
    print(T["serie"].format(serie))
    if not modell_ok(modell):
        print(T["warn_modell"])
    fuellstand_zeigen(drucker)


def backup(drucker):
    modell, firmware, serie = identitaet(drucker)
    print(T["lese_eeprom"].format(BACKUP_BEREICH.start, BACKUP_BEREICH.stop - 1))
    dump = drucker.dump_eeprom(BACKUP_BEREICH.start, BACKUP_BEREICH.stop - 1)
    fehlend = [a for a, v in dump.items() if v is None]
    if len(fehlend) == len(dump):
        print(T["backup_fehler"])
        return None
    BACKUP_ORDNER.mkdir(exist_ok=True)
    zeit = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    datei = BACKUP_ORDNER / f"eeprom_{serie}_{zeit}.json"
    datei.write_text(json.dumps({
        "modell": modell,
        "firmware": firmware,
        "seriennummer": serie,
        "zeit": zeit,
        "eeprom": {f"0x{a:04X}": v for a, v in dump.items()},
    }, indent=1), encoding="utf-8")
    print(T["gespeichert"].format(datei))
    if fehlend:
        print(T["fehlend"].format(len(fehlend)))
    return datei


def reset(drucker):
    modell, firmware, serie = identitaet(drucker)
    print(T["drucker_zeile"].format(modell, serie, firmware))
    if not modell_ok(modell):
        print(T["abbruch_modell"])
        return
    if not fuellstand_zeigen(drucker):
        print(T["abbruch_lesen"])
        print(T["tipp"])
        return
    if backup(drucker) is None:
        print(T["abbruch_backup"])
        return
    if input(T["frage_reset"].format(T["ja"])).strip() != T["ja"]:
        print(T["abgebrochen"])
        return
    bericht = []
    ok = drucker.reset_waste_ink_levels(report=bericht)
    for adr, vorher, neu, _ in bericht:
        print(f"    0x{adr:03X}: {vorher if vorher is not None else '?'} -> {neu}")
    if ok:
        print(T["reset_ok"])
        fuellstand_zeigen(drucker)
        print(T["neustart"])
    else:
        print(T["reset_fehler"])
        print(T["reset_fehler2"])


def temp_reset(drucker):
    if input(T["frage_temp"].format(T["ja"])).strip() != T["ja"]:
        return
    if drucker.temporary_reset_waste():
        print(T["temp_ok"])
    else:
        print(T["temp_fehler"])


def wiederherstellen(drucker):
    dateien = sorted(BACKUP_ORDNER.glob("eeprom_*.json"))
    if not dateien:
        print(T["keine_backups"])
        return
    for i, d in enumerate(dateien, 1):
        print(f"  {i}) {d.name}")
    try:
        datei = dateien[int(input(T["nummer"])) - 1]
    except (ValueError, IndexError):
        return
    daten = json.loads(datei.read_text(encoding="utf-8"))
    modell, _, serie = identitaet(drucker)
    if daten["seriennummer"] != serie:
        print(T["abbruch_serie"].format(daten["seriennummer"], serie))
        return
    adressen = list(drucker.parm["raw_waste_reset"]) + list(drucker.parm.get("waste_reset_commit", {}))
    werte = {a: daten["eeprom"].get(f"0x{a:04X}") for a in adressen}
    if None in werte.values():
        print(T["abbruch_unvollst"])
        return
    print(T["schreibt_zurueck"].format(", ".join(f"0x{a:03X}" for a in adressen)))
    if input(T["fortfahren"].format(T["ja"])).strip() != T["ja"]:
        return
    for adr, wert in werte.items():
        if not drucker.write_eeprom(adr, wert, label="restore"):
            print(T["fehler_adr"].format(adr))
            return
    print(T["wiederhergestellt"])
    fuellstand_zeigen(drucker)


MENU = {
    "1": ("m_status", status),
    "2": ("m_backup", backup),
    "3": ("m_reset", reset),
    "4": ("m_temp", temp_reset),
    "5": ("m_restore", wiederherstellen),
}


def main():
    global T
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=sorted(TEXTE), default=system_sprache())
    T = TEXTE[parser.parse_args().lang]
    logging.basicConfig(level=logging.WARNING, format="  [%(levelname)s] %(message)s")
    print(T["titel"])
    drucker = verbinden()
    if drucker is None:
        return
    while True:
        print()
        for k, (text, _) in MENU.items():
            print(f"  {k}) {T[text]}")
        print(T["m_ende"])
        wahl = input(T["auswahl"]).strip()
        if wahl == "0":
            break
        if wahl in MENU:
            try:
                MENU[wahl][1](drucker)
            except TimeoutError as e:
                print(T["keine_verbindung"].format(e))
    if hasattr(drucker, "close"):
        drucker.close()


if __name__ == "__main__":
    main()
