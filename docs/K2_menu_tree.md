# K2 / UD50 — Service-Menübaum (aus Firmware extrahiert)

Vollständig aus `27C1024.BIN` rekonstruiert über die **Menü-Deskriptor-Tabellen**
(nicht geraten). Jede Zeile zeigt die **Taste**, den **Menütext** und ggf. die
nötige **Passwortstufe**.

Legende: 🔑**L1** = Level-1-Passwort (Hash `0x2020`) · 🔒**L2** = Level-2-Passwort (Hash `0x4ABC`)

---

## Einstieg

```
Serielle Konsole: "K2 Serial I/O Is Alive .... [Press Any Key To Start]"
        │  (Taste drücken)
        ▼
Menu_0  - Select VDU type   (A VT52 · B VT100 · C ADM-3A · D Dumb VDU ·
        │                    E Half duplex · F Full duplex · Z = Auswahl ok)
        ▼
Menu_1  - K2 Main Menu
```

---

## Der Menübaum

```
Menu_1  K2 Main Menu
├─ A  Test / Debug ....................... Menu_2
├─ B  Production Configuration ........... Menu_5
└─ C  Error Message Log
         └─ zeigt Log; Frage "Do you wish to clear this log? [Y|N]"
              └─ Y  → 🔑 L1  → Log wird gelöscht

Menu_2  K2 Test/Debug Menu
├─ A  Dump memory ........................ Menu_3
├─ B  Set memory ......................... Menu_4
├─ C  Access 8086 i/o space .............. Menu_6
├─ D  DRAM error log ..................... Menu_11
├─ E  DRAM allocation/change maps ........ Menu_9
├─ F  BITS - Built In Test Software ...... Menu_7
├─ G  Miscellaneous options .............. Menu_10
└─ H  SMD/E Configuration ................ Menu_12
   ⚠ VERSTECKT: Es gibt einen 9. Handler-Stub (f1ec:00BA → Menu_8 SCSI Sniffer),
     aber KEINE Menütaste zeigt darauf → nicht erreichbar (s.u. "Versteckter SCSI Sniffer").

Menu_3  K2 Memory Dump Menu
   A Start address · B Dump DRAM · C Dump DRAM lba:offset · D Dump SRAM ·
   E Dump NVRAM · F Dump EPROM · G Dump 8086 seg:off · H Byte · I Word ·
   J Dword · K Aligned · L Unaligned · Z Commence dump          (keine PW)

Menu_4  K2 Memory Set Menu
   A Start address · B Set DRAM · C Set DRAM lba:offset · D Set SRAM ·
   E Set NVRAM · F Set 8086 seg:off · G Byte · H Word · I Dword ·
   └─ Z  Commence set  → 🔑 L1  (bedingt – beim Schreiben in geschützten Speicher)

Menu_5  K2 Production Configuration Menu
├─ A  Change Configuration ............... Menu_5a
└─ B  Change Revision Numbers ............ Menu_5f

Menu_5a K2 Production Configuration Change Menu     ← 🔒 L2 zum BETRETEN
   A Change SCSI config ..... Menu_5b
   B Change DRAM config ..... Menu_5c
   C Change MISC config ..... Menu_5d
   D Change SIO config ...... Menu_5e
   Z Write configuration to NVRAM        (kein Extra-PW, L2 bereits erbracht)

   Menu_5b SCSI config:  A..I  (Single/dual bit, backup, SE/diff ports, ESP clock, block size)
   Menu_5c DRAM config:  A..I  (DRAM size, mixed caps, ECC, control clocks, unit capacity)
   Menu_5d MISC config:  A Battery backup · B Change form factor !!! · C Backup media ·
                         D Syquest drive · E Boot program
   Menu_5e SIO config:   A Baud · B Sync/Async · C Data bits · D Parity · E Even/odd ·
                         F Stop bits · G SYNDET · H Sync character

Menu_5f K2 Hardware Revision / Serial Number Set     ← 🔒 L2 zum BETRETEN
   A Set Hardware Revision Number
   B Set Manufacturing Serial Number
   C Set Top Assembly Number
   D Set Current Job Number

Menu_6  K2 I/O Space Access Menu
├─ A  Access by Port Address ............. Menu_6a
├─ B  Access Named Registers ............. Menu_6b
├─ C  K2 Warm Start  → 🔒 L2
└─ D  K2 Cold Start  → 🔒 L2

Menu_6a K2 I/O Ports Access Menu
   A Port address · B 8/16 bit (toggle) · C Read format hex/bin · D Buzz mode (toggle) ·
   E Read port · F Write port
   └─ „Buzz write started." sperrt das Menü → ESC zum Verlassen = 🔑 L1
      (Spruch: "Only the knowledgeable or lucky can leave this menu")

Menu_6b K2 Named Registers Access Menu
   A..D Register-group A/B/C/D · E Read register-group · F Write register-group

Menu_7  K2 Built In Test Software (BITS) Menu
├─ A  Memory tests ....................... Menu_7a
├─ B  Device tests
├─ C  General tests
└─ D  DIP Switch Test

Menu_7a K2 Memory Tests Menu
   A SRAM · B NVRAM · C EPROM · D DRAM accelerated · E DRAM extended → Menu_7b
Menu_7b K2 DRAM Extended Test Menu
   A Set low DRAM address · B Set high DRAM address · Z Start test

Menu_8  K2 SCSI Sniffer Menu   (A Step mode · B Real time monitor)   [VERSTECKT - s.u.]

Menu_9  K2 DRAM Allocation/Change Maps Menu
   A  Display Map Descriptors
   B  Display DRAM Allocation Map
   C  Display DRAM Change Map
   D  Clear DRAM Allocation Map  → 🔑 L1
   E  Clear DRAM Change Map      → 🔑 L1
   F  Perform Backup            → 🔒 L2
   G  Perform Restore           → 🔒 L2
   H  Force Backup              → 🔒 L2

Menu_10 K2 Miscellaneous Options Menu
   A DRAM Scrubbing · B DRAM EDC Correction · C Display PDM Config ·
   D Set Power Fail Dump Time · E Set Fill Pattern ·
   F  Fill DRAM with Pattern    → 🔒 L2
   G Read DRAM to First Error · H Read All DRAM · I Limit DRAM Capacity ·
   J Primary Defect List · K Grown Defect List · L Allowed Defect Limit

Menu_11 K2 DRAM Error Log Menu
   A  Display single bit errors
   B  Display multi bit errors
   C  Clear error log           → 🔑 L1

Menu_12 K2 SMD/E Configuration Menu
├─ A  Emulation Program Transfer ......... Menu_12a
├─ B  Edit Emulation Program ............. Menu_12b
└─ C  Edit Global Geometry Parameters .... Menu_12c

Menu_12a K2 SMD/E Program Transfer Menu
   A  NVRAM to Edit Area
   B  Edit Area to NVRAM          → 🔒 L2
   C  NVRAM to Emulation Memory   → 🔒 L2
   D  ERAM to Edit Area
   E  Delete Program from NVRAM   → 🔒 L2
   F  SIO Fast Load to NVRAM      → 🔒 L2

Menu_12b K2 SMD/E Program Edit Menu
   A Edit Microcode → Menu_12d · B Edit Program Parameters → Menu_12e ·
   C Clear Edit Area · D Enter New Program

Menu_12c K2 SMD/E Global Geometry Menu
   A Set Seek Time · B Same Cyl. Seek · C Recalibrate Seek · D Carriage Offset ·
   E Released Pulse · F Reservation Time · G Extended Head Address ·
   └─ Z  Write to NVRAM           → 🔑 L1

Menu_12d K2 SMD/E Microcode Editor   (A Insert After · B Insert Before · D Delete · R Replace)
Menu_12e K2 SMD/E Program Parameters (A Name · B Cylinders · C Heads · D Sectors · E Bytes/Sector)
```

---

## Wo wird welches Passwort verlangt?

### 🔑 Level 1 (`0x2020`) — 6 Stellen

| # | Weg dorthin | Call-Site |
|---|---|---|
| 1 | **Main → C Error Message Log → Y** („clear this log?") | `0x11D17` |
| 2 | **Test/Debug → E DRAM allocation/change maps → D Clear DRAM Allocation Map** | `0x174A4` |
| 3 | **Test/Debug → E DRAM allocation/change maps → E Clear DRAM Change Map** | `0x17454` |
| 4 | **Test/Debug → D DRAM error log → C Clear error log** | `0x1B04C` |
| 5 | **Test/Debug → B Set memory → Z Commence set** (bedingt) | `0x13325` |
| 6 | **Test/Debug → H SMD/E → C Edit Global Geometry → Z Write to NVRAM** | `0x1D2DE` |
| + | **I/O Ports „Buzz write" → ESC** (Menü ist gesperrt) | `0xED87` |

> **Warum du es nicht gefunden hast:** Der häufigste L1-Punkt (Main → Error Message Log)
> fragt **nur dann** nach dem Passwort, wenn du mit **Y** das Löschen bestätigst – und
> bei „No Errors Logged" kommt die Y/N-Frage evtl. gar nicht. Der **zuverlässigste**
> L1-Test ist **Test/Debug → DRAM allocation/change maps → „Clear DRAM Change Map"**
> oder **DRAM error log → „Clear error log"**.

### 🔒 Level 2 (`0x4ABC`) — 11 Stellen

- **Production Configuration Change** (Menu_5a) — **beim Betreten** (`0x150E2`)
- **Hardware Revision / Serial Number Set** (Menu_5f) — **beim Betreten** (`0x150E2`)
- I/O Space → **K2 Warm Start** (`0x15F32`), **K2 Cold Start** (`0x15F60`)
- DRAM maps → **Perform Backup** (`0x175D8`), **Force Backup** (`0x1762E`), **Perform Restore** (`0x17696`)
- Misc → **Fill DRAM with Pattern** (`0x1A002`)
- SMD/E Program Transfer → **Edit Area to NVRAM** (`0x1C8C1`), **NVRAM to Emulation Memory** (`0x1C9EC`),
  **Delete Program from NVRAM** (`0x1CA3F`), **SIO Fast Load to NVRAM** (`0x1CB4C`)

**Muster:** L1 = *löschen/zurücksetzen* von Maps/Logs + geschütztes Schreiben; L2 = *konfigurieren,
Backup/Restore, DRAM überschreiben, Emulations-Programme ins NVRAM schreiben* (gefährlicher).

---

## Versteckter SCSI Sniffer (Menu_8)

Der SCSI Sniffer ist **voll implementiert, aber nicht erreichbar** — eine im
Werk deaktivierte Funktion, deren Code im ROM blieb:

- Das Test/Debug-Modul enthält **9** Handler-Stubs und eine **9-Einträge**-Zeiger­tabelle
  (`cs:[6,A,E,12,16,1A,1E,22,26]` → Menu_3,4,6,11,7,9,**8**,10,12).
- Die Options-Tabelle von Menu_2 hat aber nur **count = 8** und belegt die Tasten **A–H**
  mit 8 dieser Stubs. Der Stub **`f1ec:00BA`** (lädt `cs:[0x1E]` → Menu_8 SCSI Sniffer)
  bekommt **keine Taste**.
- Der Stub hat im gesamten ROM **keinen einzigen Aufrufer** (kein Far-Call, kein Zeiger) →
  klassisch „Feature aus dem Menü genommen, Code vergessen". Seine Lage (zwischen den
  Stubs für Option E und G) passt dazu: früher eine eigene Menüzeile, vor Release entfernt.
- Menu_8 selbst ist real: **A Step mode** → `f0e3:0086("Sniff step")`,
  **B Real time monitor** → `f0e3:0086("Sniff monitor")` (Live-SCSI-Bus-Mitschnitt).

**Wieder aktivieren**
- *Im Emulator:* direkt den Handler `f1ec:00BA` (phys `0xF1F7A`) aufrufen – oder den
  Menu_8-Deskriptor (`f6f4:001A`, phys `0xF6F5A`) an die Engine `EEB0:0058` übergeben.
- *Als ROM-Patch:* in einem Options-Record von Menu_2 (Array @ file `0x11DA8`, 8×9 Bytes)
  den Handler-Zeiger (Record-Offset +5) auf `f1ec:00BA` umbiegen → die betreffende Taste
  öffnet dann den Sniffer. Eine echte **9.** Zeile hinzuzufügen erfordert, das Options-Array
  umzulegen (es grenzt direkt an den Deskriptor @ `0x11DF0`) und `count` (@ `0x11DF4`) auf 9
  zu erhöhen.

---

## Anhang — Menü-Deskriptor-Format (für den Emulator)

Jedes Menü ist eine Struktur; die Options-Tabelle ist nach Taste sortiert, die
Engine (`EEB0:0058`) macht eine **Binärsuche** und ruft den Handler als Far-Call.

```
Deskriptor:
  +0x00  far*  Titel-String ("Menu_X - ...")
  +0x04  u16   Anzahl Optionen
  +0x06  u16   Typ (0 = Buchstaben A..Z,  2 = nummerierte/Toggle-Liste)
  +0x08  far*  Options-Array  (Stride 9 Bytes, s.u.)
  +0x0C  far*  Enter-Callback (0 = keiner; kann das Menü "sperren" -> [0x17]=1)
  +0x18  u8    Flags (Bit0 = Layout)

Options-Record (9 Bytes):
  +0x00  u8    Taste (ASCII)
  +0x01  far*  Label-String
  +0x05  far*  Handler-Funktion
```

**Sperr-/ESC-Logik:** Beim Verlassen prüft die Engine
`(ESC_oder_^C) & lock_flag`. `lock_flag` kommt aus `[0x17]`, gesetzt vom
Enter-Callback bzw. vom „Buzz write"-Start. Ist es gesetzt, wird beim ESC der
Spruch *„Only the knowledgeable or lucky can leave this menu"* gezeigt und das
**L1-Passwort** verlangt; falsch ⇒ Quit-Flag wird gelöscht ⇒ du bleibst drin.

**Passwort-Prüfung:** `EF65:001A`, Salt `"NATO"`, 16-Bit-Fold — Details und das
Tool siehe `K2_service_password.md` / `k2_passtool.py`.
