# 27C1024-Ersatz aus 2× W27C512 — Adapter-Verdrahtung

Ziel: einen 16-bit-breiten 27C1024 (64K×16, 40-pin) durch **zwei 8-bit-Chips
W27C512** (64K×8, 28-pin, elektrisch löschbar, 5 V) nachbilden. Ein Chip liefert
das Low-Byte, einer das High-Byte; beide teilen sich Adresse + Steuerleitungen.

## Was auf welchen Chip kommt

| Image (aus `27C1024_SCSI_CKSUM.BIN`) | Chip | treibt |
|---|---|---|
| **`K2_SCSI_LOW_D0-D7.bin`** (64 KB) | **LOW-Chip** | Datenbits **Q0–Q7** |
| **`K2_SCSI_HIGH_D8-D15.bin`** (64 KB) | **HIGH-Chip** | Datenbits **Q8–Q15** |

Beide Chips sind immer gleichzeitig aktiv und treiben jeweils ihre eigenen 8
Datenleitungen → **kein Buskonflikt**.

## Referenz-Pinouts

**27C1024 (40-pin DIP)** — Pin: Signal
```
 1 VPP      11 VSS      21 A0       31 A9
 2 /E (CE)  12 Q7       22 A1       32 A10
 3 Q15      13 Q6       23 A2       33 A11
 4 Q14      14 Q5       24 A3       34 A12
 5 Q13      15 Q4       25 A4       35 A13
 6 Q12      16 Q3       26 A5       36 A14
 7 Q11      17 Q2       27 A6       37 A15
 8 Q10      18 Q1       28 A7       38 NC
 9 Q9       19 Q0       29 A8       39 /P (PGM)
10 Q8       20 /G (OE)  30 VSS      40 VCC
```

**W27C512 / 27C512 (28-pin DIP)** — Pin: Signal
```
 1 A15   8 A2    15 Q3    22 /OE
 2 A12   9 A1    16 Q4    23 A11
 3 A7   10 A0    17 Q5    24 A9
 4 A6   11 Q0    18 Q6    25 A8
 5 A5   12 Q1    19 Q7    26 A13
 6 A4   13 Q2    20 /CE   27 A14
 7 A3   14 VSS   21 A10   28 VCC
```

## Verdrahtung

### 1) Adressleitungen — 27C1024 → *beide* W27C512 parallel

| Signal | 27C1024 Pin | W27C512 Pin |
|---|---|---|
| A0 | 21 | 10 |
| A1 | 22 | 9 |
| A2 | 23 | 8 |
| A3 | 24 | 7 |
| A4 | 25 | 6 |
| A5 | 26 | 5 |
| A6 | 27 | 4 |
| A7 | 28 | 3 |
| A8 | 29 | 25 |
| A9 | 31 | 24 |
| A10 | 32 | 21 |
| A11 | 33 | 23 |
| A12 | 34 | 2 |
| A13 | 35 | 26 |
| A14 | 36 | 27 |
| A15 | 37 | 1 |

### 2) Steuerung + Versorgung — 27C1024 → *beide* W27C512 parallel

| Signal | 27C1024 Pin | W27C512 Pin |
|---|---|---|
| /CE (Chip Enable) | 2 (/E) | 20 |
| /OE (Output Enable) | 20 (/G) | 22 |
| Vcc (+5 V) | 40 | 28 |
| GND | **11 und 30** | 14 |

### 3) Datenbus — GETRENNT (je Chip eigene 8 Bit)

| 27C1024 | Pin | → Chip | Chip-Pin |
|---|---|---|---|
| Q0 | 19 | LOW  Q0 | 11 |
| Q1 | 18 | LOW  Q1 | 12 |
| Q2 | 17 | LOW  Q2 | 13 |
| Q3 | 16 | LOW  Q3 | 15 |
| Q4 | 15 | LOW  Q4 | 16 |
| Q5 | 14 | LOW  Q5 | 17 |
| Q6 | 13 | LOW  Q6 | 18 |
| Q7 | 12 | LOW  Q7 | 19 |
| Q8 | 10 | HIGH Q0 | 11 |
| Q9 | 9  | HIGH Q1 | 12 |
| Q10 | 8 | HIGH Q2 | 13 |
| Q11 | 7 | HIGH Q3 | 15 |
| Q12 | 6 | HIGH Q4 | 16 |
| Q13 | 5 | HIGH Q5 | 17 |
| Q14 | 4 | HIGH Q6 | 18 |
| Q15 | 3 | HIGH Q7 | 19 |

### 4) 27C1024-Pins, die offen bleiben (nicht an die W27C512)

- **Pin 1 (VPP)** — nur beim Brennen des 27C1024 relevant; der W27C512 wird
  separat im TL866 gebrannt. Offen lassen.
- **Pin 38 (NC)** — nicht belegt.
- **Pin 39 (/P, PGM)** — nur beim Brennen des 27C1024 relevant. Offen lassen.

## Bau-Hinweise

- **Je 100 nF Keramik-Kerko** direkt zwischen Pin 28 (Vcc) und Pin 14 (GND) jedes
  W27C512.
- **Beide GND-Pins** des 27C1024 (11 **und** 30) mit GND verbinden.
- Adress-/Datenstichleitungen kurz halten (gestapelte Platine / kurze Fädeldrähte),
  der Bus läuft mit Original-EPROM-Timing, das ist unkritisch.
- **W27C512 Pin 22** ist im Lesebetrieb /OE; dass dieser Pin beim Programmieren als
  Vpp dient, spielt im Sockel keine Rolle.
- **Reihenfolge:** erst beide W27C512 im TL866 brennen
  (LOW = `K2_SCSI_LOW_D0-D7.bin`, HIGH = `K2_SCSI_HIGH_D8-D15.bin`), dann in den
  Adapter, dann in den K2.

## ⚠️ Vor dem Einschalten prüfen

Die 27C1024-Pinbelegung ist gegen Vpp=1 / Vcc=40 / zwei GND (11, 30) aus den
offiziellen Datenblättern (ST/AMD/Atmel) gegengecheckt, die vollständige Zuordnung
stammt aus einer Sekundärquelle. **Vor dem ersten Einschalten** die kritischen Pins
(Vcc 40, GND 11/30, /E 2, /G 20) am konkreten Chip-Datenblatt und per Durchgangs-
prüfung gegen Kurzschlüsse verifizieren — besonders Vcc↔GND.

Quellen: [circuits-diy 27C1024](https://www.circuits-diy.com/27c1024-64kx16-120ns-cmos-eprom-datasheet/) ·
[ST M27C1024 (cieri.net)](https://www.cieri.net/Documenti/Data%20Sheets/Memories/M27C1024%20(ST).pdf) ·
[AMD Am27C1024](https://manualmachine.com/amd/am27c1024/3991198-datasheet)
