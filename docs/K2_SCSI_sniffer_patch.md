# ROM-Patch: versteckten SCSI Sniffer sichtbar machen

**Eingabe:** `27C1024.BIN` (Original). Größe immer unverändert (131072 Bytes).
Es gibt zwei Ausgaben:

| Datei | MD5 | EPROM-Selbsttest |
|---|---|---|
| `27C1024.BIN` (Original) | `c447067e31a997c80eb0fbb44cfe1a0a` | passed (0x847F) |
| `27C1024_SCSI.BIN` | `8d0f7b7ec446a96296c558dff54a19cd` | **failed** (kosmetisch) |
| **`27C1024_SCSI_CKSUM.BIN`** ⭐ | `7dd5eeddaa945dbcddea78284b1279fd` | **passed** (0xB25F) |

⭐ **Empfohlen:** `27C1024_SCSI_CKSUM.BIN` — identisch zum einfachen Patch, aber mit
korrigierter ROM-Prüfsumme, sodass auch `BITS → Memory tests → EPROM` „passed" meldet.

## Was der Patch tut

Im **Test/Debug-Menü (Menu_2)** erscheint eine neue Zeile:

```
I  SCSI Sniffer
```

Taste **`I`** öffnet das vorhandene, aber bisher unerreichbare **Menu_8 – K2 SCSI
Sniffer Menu** (A Step mode · B Real time monitor). Keine bestehende Option geht
verloren (A–H bleiben unverändert).

## Funktionsweise

Das Options-Array von Menu_2 (8 Einträge) grenzt direkt an den Deskriptor, es war
also kein Platz für einen 9. Eintrag „inline". Der Patch legt das Array daher in
freien EPROM-Bereich (lauter `0xFF`, ab `0x1F000`) um und hängt den 9. Eintrag an:

- Taste `I` → Label **"SCSI Sniffer"** → Handler **`f1ec:00BA`** (der vorhandene,
  verwaiste Stub, der Menu_8 öffnet).
- Der Handler-Zeiger behält bewusst Segment **`F1EC`** (phys `0xF1F7A`), weil der
  Stub CS-relativ arbeitet (`les bx, cs:[0x1E]`) und so die Menu_8-Zeigertabelle
  bei `f1ec:001E` findet.

## Geänderte Bytes

| Offset (Datei) | alt | neu | Bedeutung |
|---|---|---|---|
| `0x11DF4` | `08` | `09` | Deskriptor `count` 8 → 9 |
| `0x11DF8` | `08 00 DA F1` | `00 00 01 FF` | `optarray`-Zeiger → neues Array (`FF01:0000`) |
| `0x1F000` | `FF…` | `"SCSI Sniffer\0"` (13 B) | neuer Label-String |
| `0x1F010` | `FF…` | 9×9-Byte-Array (81 B) | A–H kopiert + neuer `I`-Record |

Neuer Record (`I`): `49  00 00 00 FF  BA 00 EC F1`
= Taste `I`, Label-Ptr `FF00:0000`, Handler-Ptr `F1EC:00BA`.

## Benutzen

- **EPROM brennen:** `27C1024_SCSI.BIN` 1:1 in den 27C1024 brennen (word-organisiert,
  wie das Original-Dump).
- **Emulator:** statt `27C1024.BIN` laden.

Weg im Gerät: **Hauptmenü → A Test / Debug → I SCSI Sniffer**.

## Verifikation (statisch, bereits geprüft)

- Menu_2 `count` = 9, Record 8 = `I` → Label `"SCSI Sniffer"`, Handler `f1ec:00ba`.
- Binärsuche der Menü-Engine nach `I` (0x49) landet auf Record 8.
- Handler-Stub liest `cs:[0x1E]` → `f6f4:001A` (= phys `0xF6F5A`) = Deskriptor von
  **Menu_8 SCSI Sniffer** ✓.
- Reset-Vektor (`0x1FFF0`) und der gesamte Boot-/Menücode unangetastet.

## ROM-Prüfsumme (EPROM-Selbsttest)

`BITS → Memory tests → EPROM` berechnet die **16-Bit-Summe aller Bytes ≠ 0xFF** über
`0xE0000…0xFFFFD` und vergleicht sie mit dem **gespeicherten Wert in den letzten 2 Bytes**
(`0x1FFFE/0x1FFFF`, little-endian). Original: `0x847F`.

Die Variante **`27C1024_SCSI_CKSUM.BIN`** berechnet diese Summe nach dem Patch neu
(`0xB25F`) und legt sie an `0x1FFFE/0x1FFFF` ab → der Selbsttest meldet wieder „passed".
Diese 2 Bytes zählen selbst nicht in die Summe (werden ausgeschlossen) und gehören nicht
zum Reset-Vektor (`0x1FFF0`), es gibt also keinen Zirkelbezug. Zusätzliche Änderung
gegenüber dem einfachen Patch:

| Offset | alt | neu | Bedeutung |
|---|---|---|---|
| `0x1FFFE` | `7F 84` | `5F B2` | ROM-Prüfsumme `0x847F` → `0xB25F` |

Verifiziert durch 1:1-Nachbildung der ROM-Routine `e40a:650`: Original `passed` (0x847F),
`27C1024_SCSI_CKSUM.BIN` `passed` (0xB25F), einfacher Patch `failed`.

## Hinweise

- **Boot:** Der Boot-Code prüft **keine** ROM-Prüfsumme (nur RAM-Warmstart-Marker) –
  beide Varianten booten normal.
- **Welche nehmen?** Für reale Nutzung / sauberen Selbsttest: `27C1024_SCSI_CKSUM.BIN`.
  Der einfache `27C1024_SCSI.BIN` funktioniert genauso, nur der optionale EPROM-Selbsttest
  würde „failed" zeigen (ohne Einfluss auf Betrieb/Boot).
- **Zurücksetzen:** einfach wieder das Original-`27C1024.BIN` verwenden.
