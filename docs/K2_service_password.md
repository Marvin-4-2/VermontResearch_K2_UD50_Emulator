# K2 / UD50 — Service-Passwort-Routine (Reverse Engineering)

Dokumentation der `Enter password:`-Abfrage aus dem Programm-EPROM `27C1024.BIN`
(NEC V30 / 8086-Realmode). Erstellt aus der statischen Analyse der Dumps in
`chip_dumps/`.

---

## 1. Speicher-Mapping (für die Disassemblierung)

| | |
|---|---|
| ROM-Größe | 128 KiB (`27C1024.BIN`) |
| Physische Basis | **0xE0000** → `phys_addr = file_offset + 0xE0000` |
| Reset-Vektor @ 0xFFFF0 | `EA 06 00 47 FE` = `JMP FE47:0006` |
| Segment↔Offset | `phys = seg*16 + off` |

Umrechnung Segment:Offset → Datei-Offset: `file = seg*16 + off − 0xE0000`.

---

## 2. Die Passwort-Abfrage

* Prompt-String `"Enter password: "` @ Datei **0xF658** (= `EF65:0008`).
* Vorher wird oft der Spott-Text ausgegeben:
  `"Only the knowledgeable or lucky can leave this menu"` @ **0xEB1A**.
* Prüf-Funktion: Einsprung **`EF65:001A`** (= `EF33:033A`, Datei **0xF66A**).
  Wird von **18 Stellen** aufgerufen.

### 2.1 Funktions-Signatur (C-Konvention, far)

```c
/* Rückgabe: 0xFF = korrekt, 0x00 = falsch */
unsigned char check_password(unsigned short target_hash,  /* [bp+8]        */
                             const char far *ref);        /* [bp+0Ah/0Ch]  */
```

Aufrufer-Muster (immer identisch):

```asm
    mov  ax, <ref_offset>   ; Zeiger auf Referenz-/Salt-String  ("NATO")
    push cs
    push ax
    mov  ax, <target_hash>  ; erwarteter 16-Bit-Hash  (0x2020 oder 0x4ABC)
    push ax
    lcall EF65:001A         ; -> AL = 0xFF wenn korrekt
    shr  ax, 1              ; CF = Ergebnis
    jb   <zugang_gewaehrt>
```

### 2.2 Verwendete Bibliotheks-Calls (beobachtet)

| Call | Bedeutung |
|---|---|
| `EF33:0042` | `puts(char far*)` — null-terminierten String ausgeben |
| `EF33:0136` | Zeilenvorschub / Ausgabe-Flush (am Anfang) |
| `EE95:0020` | `getchar()` → `AL` (blockierend) |
| `EE95:0152` | `putchar(AL)` |
| `EF33:001E` | pro akzeptiertem Zeichen aufgerufen (Cursor/Buffer) |
| `EF33:000A` | „Beep" bei ungültigem Zeichen |

---

## 3. Der Algorithmus

Es wird **kein Passwort im Klartext gespeichert**. Verglichen wird nur ein
**16-Bit-Hash**. Eingabe und ein Referenz-String werden *im Gleichschritt*
gefaltet. Der Referenz-String ist an allen 18 Stellen **`"NATO"`** (@ 0xEB4E).

Pro getipptem Zeichen (bis `CR`):

```
h = ((h*2 + eingabe[i]) * 2 + ref[i mod 4])  (mod 65536)
```

Zeichen-Filter: `CR (0x0D)` beendet die Eingabe; Zeichen `<= 0x1F` oder `>= 0x7F`
werden ignoriert (Beep); druckbare Zeichen werden als `.` echot (maskiert).
Am Ende: Zugang, wenn `h == target_hash`.

### 3.1 Referenz-Disassemblierung (gekürzt, `EF33:033A`)

```asm
033A  push ds
      mov  cx,0x00FF        ; DS = 0x00FF  (Scratch-RAM)
      mov  ds,cx
      push bp / mov bp,sp
      lcall EF33:0136       ; CRLF
      mov  ax,8 / push cs / push ax
      lcall EF33:0042       ; puts("Enter password: ")  (EF65:0008)
      mov  word [0C],0      ; h      = 0   (Akkumulator)
      mov  word [0E],0      ; idx    = 0   (Index in ref)
.loop:
      lcall EE95:0020       ; AL = getchar()
      mov  [10],al
      cmp  al,0x0D / je .done
      cmp  al,0x7F / jae .beep
      cmp  al,0x1F / jbe .beep
      lcall EF33:001E
      mov  al,'.' / push ax / lcall EE95:0152   ; echo '.'
      mov  ax,[0C] / shl ax,1 / add ax,<eingabe> / mov [0C],ax   ; h = h*2 + in
      les  bx,[bp+0Ah]      ; ref
      mov  si,[0E]
      mov  al,es:[bx+si]    ; ref[idx]
      or   al,al / jne +    ; bei 0x00: idx=0, ref[0]  (Wrap)
        mov word [0E],0 / mov al,es:[bx]
   +: inc  word [0E]
      mov  ax,[0C] / shl ax,1 / add ax,<refchar> / mov [0C],ax   ; h = h*2 + ref
      jmp  .loop
.beep:
      lcall EF33:000A / jmp .loop
.done:
      mov  ax,[bp+8]        ; target_hash
      cmp  ax,[0C]          ; == h ?
      mov  al,0xFF / je +   ; gleich -> 0xFF
      inc  ax               ; sonst  -> 0x00
   +: mov  ah,0 / pop bp / pop ds / retf 6
```

---

## 4. C-Reimplementierung (fürs Emulator-Projekt)

```c
#include <stdint.h>
#include <string.h>

/* 1:1-Nachbau der ROM-Routine EF33:033A. */
static uint16_t k2_pw_fold(const char *input, const char *ref)
{
    uint16_t h = 0;
    size_t   reflen = strlen(ref);
    size_t   idx    = 0;

    for (size_t i = 0; input[i]; ++i) {
        uint8_t c = (uint8_t)input[i];
        if (c == 0x0D) break;              /* Enter beendet          */
        if (c <= 0x1F || c >= 0x7F) continue; /* ignoriert (Beep)    */

        h = (uint16_t)((h << 1) + c);      /* h = h*2 + eingabe      */

        if (idx >= reflen || ref[idx] == 0) idx = 0;   /* Wrap        */
        h = (uint16_t)((h << 1) + (uint8_t)ref[idx]);  /* h = h*2+ref */
        ++idx;
    }
    return h;
}

/* true = Zugang gewährt */
static int k2_check_password(const char *input, uint16_t target_hash)
{
    return k2_pw_fold(input, "NATO") == target_hash;
}
```

Konstanten:

```c
#define K2_PW_SALT        "NATO"
#define K2_PW_LEVEL1_HASH 0x2020u   /* „view/leave"-Menüs          */
#define K2_PW_LEVEL2_HASH 0x4ABCu   /* destruktive/Schreib-Menüs   */
```

---

## 5. Funktionierende Passwörter

Der 16-Bit-Hash hat viele Kollisionen → das *ursprünglich gemeinte* Entwickler-
Passwort ist nicht eindeutig rekonstruierbar (kein Treffer gegen Wortlisten:
NATO-Alphabet, Serien-/Teilenummer, gängige Default-Passwörter). Es lassen sich
aber beliebige **gültige** Passwörter berechnen. Nur Ziffern, verifiziert:

| Stufe | Hash | Passwort (Beispiel) | weitere gültige |
|---|---|---|---|
| **1** | `0x2020` | **`4796878`** | `AUYYW`, `BQYYW`, `4796884`, … |
| **2** | `0x4ABC` | **`5967976`** | `UZZXY`, `VVZXY`, `5967982`, … |

> Hinweis: Der Salt „NATO" ist positions-gebunden (`i mod 4`), d. h. ein gültiges
> Suffix lässt sich **nicht** einfach mit beliebigem Text verlängern.

---

## 6. Die 18 Call-Sites und ihre Stufe

`file` = Datei-Offset des `lcall` im Programm-ROM.

### Stufe 1 — Hash `0x2020` (7×)

| file | CS | Geschützt (laut Kontext-Strings) |
|---|---|---|
| `0xED87` | `EEB0` | **Verstecktes Menü / Trap**: „Only the knowledgeable or lucky can leave this menu" |
| `0x11D17` | `F163` | Test/Debug (Menu_2): EDC-/„C Error"-Funktion |
| `0x13325` | `F2E5` | DRAM-Fehler: Syndrome / „Current value / Replacement value" |
| `0x17454` | `F712` | DRAM Allocation/Change Maps (Menu_9) |
| `0x174A4` | `F712` | DRAM-Map-Anzeige („End of Map") (Menu_9) |
| `0x1B04C` | `FAC9` | SMD/E Configuration (Menu_12) |
| `0x1D2DE` | `FB61` | SMD/E-Bereich |

### Stufe 2 — Hash `0x4ABC` (11×)

| file | CS | Geschützt (laut Kontext-Strings) |
|---|---|---|
| `0x150E2` | `F418` | I/O-/Konfig-Zugriff |
| `0x15F32` | `F5BE` | I/O Space Access (Menu_6): Port-Zugriff |
| `0x15F60` | `F5BE` | I/O Space Access (Menu_6): Named Registers |
| `0x175D8` | `F712` | DRAM-Map ändern — „1 …" (Menu_9) |
| `0x1762E` | `F712` | DRAM-Map ändern — „2 …" (Menu_9) |
| `0x17696` | `F712` | DRAM-Map ändern — „3 …" (Menu_9) |
| `0x1A002` | `F78B` | **„WARNING: This action will destroy backup map information"** (Menu_11) |
| `0x1C8C1` | `FB61` | SMD/E Program Edit (temp. Name) |
| `0x1C9EC` | `FB61` | SMD/E Program Edit |
| `0x1CA3F` | `FB61` | SMD/E Program löschen („can't delete active program") |
| `0x1CB4C` | `FB61` | **„SIO fast load to NVRAM"** — Schreiben ins Konfig-EEPROM (28C64) |

**Muster:** Stufe 1 = Einstieg/Anzeige (lesen, Trap-Menü verlassen); Stufe 2 =
schreibende/zerstörende Aktionen (Port-Writes, Map-Zerstörung, SMD/E-Programm-
Editor, NVRAM-Schreiben).

---

## 7. Menübaum (Kontext)

`Menu_0` VDU-Typ · `Menu_1` Main · `Menu_2` Test/Debug · `Menu_3` Memory Dump ·
`Menu_4` Memory Set · `Menu_5[a–f]` Production/SCSI/DRAM/Misc/SerialIO/HW-Rev+Serial ·
`Menu_6[a/b]` I/O-Space/Ports/Named-Registers · `Menu_7[a/b]` BITS/Memory/DRAM-Tests ·
`Menu_8` SCSI Sniffer · `Menu_9` DRAM Allocation/Change Maps · `Menu_10` Misc ·
`Menu_11` DRAM Error Log · `Menu_12[a–e]` SMD/E Config/Transfer/Edit/Geometry/Microcode/Params.

---

## 8. `28C64.BIN` (Konfig-EEPROM) — kein Passwort

Enthält nur Konfiguration, **kein** Passwort:

* Board-Nr. `L02-A-0157-000`, Seriennummer `SR1518K5080403`
* Emulations-Profile: `DEFAULT EMU`, `SCARSB`, `UD50`, `UD502`,
  `SCARS_TRUE12S`, `UD50_TEST384`, `*** EMPTY ***`
* Test-Signatur @ `0x1FF0`: `00 5A A5 FF 1F F1 2E E2 11 22 33 44 55 66 77 88`
