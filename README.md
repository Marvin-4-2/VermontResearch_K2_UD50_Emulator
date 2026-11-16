# Vermont Research K2 / UD50 — Firmware Reverse Engineering

Reverse engineering, documentation and tooling for the firmware of a **Vermont
Research "K2" solid-state drive** (a RAM-based, battery-backed storage unit that emulates a
classic **UD50 / SMD-E disk drive**, with a SCSI drive for backup).

Everything here was derived by **static analysis** of two on-board memory chips:

| Chip | Size | Role |
|---|---|---|
| `27C1024` | 128 KiB | Program EPROM (NEC **V30** / 8086-class code) |
| `28C64` | 8 KiB | Non-volatile configuration EEPROM |

## Highlights

- **🔑 Service-password scheme fully decoded.** The engineering/service menus are
  gated by an `Enter password:` prompt. There is **no plaintext password** — the
  routine folds the typed input together with the salt string **`"NATO"`** into a
  weak 16-bit hash and compares it against a stored target. Two levels exist, and
  working passwords were recovered by preimage search:
  - **Level 1** (hash `0x2020`) → e.g. **`4796878`**
  - **Level 2** (hash `0x4ABC`) → e.g. **`5967976`**
- **🗺️ Complete menu tree extracted** from the firmware's menu-descriptor tables
  (`Menu_0 … Menu_12e`), with every key, label, handler address and password gate.
- **🕵️ A hidden "SCSI Sniffer" menu** (`Menu_8`, Step mode / Real-time monitor) is
  fully implemented but **unwired** from the menu — a factory-disabled feature. A
  patch re-enables it as a new Test/Debug menu entry, with the ROM checksum fixed up
  so the built-in EPROM self-test still passes.
- **🔧 Hardware note:** how to replace the 16-bit `27C1024` with **two 8-bit
  W27C512** flash chips (split images + pin-by-pin wiring).

## Repository layout

```
docs/      K2_service_password.md     – the password routine (asm + C reimplementation)
           K2_menu_tree.md            – full service menu tree, password gates, hidden SCSI sniffer
           K2_SCSI_sniffer_patch.md   – the ROM patch (what/where/how, checksum-neutral build)
           K2_27C1024_adapter_wiring.md – 27C1024 → 2× W27C512 pin mapping
tools/     k2_passtool.py             – compute/verify passwords, generate valid ones (no deps)
           make_patch.py              – apply the SCSI-sniffer patch to a 27C1024 dump
firmware/  original/                  – as-dumped 27C1024.BIN, 28C64.BIN
           patched/                   – SCSI-sniffer builds + low/high byte split images
hardware/  adapter_27C1024_to_2x_W27C512.svg – wiring sketch for the 2-chip EPROM replacement
```

## Quick start

**Passwords** (Python 3, no dependencies):

```bash
python tools/k2_passtool.py list                 # known levels + example passwords
python tools/k2_passtool.py hash 4796878         # hash a candidate / check a level
python tools/k2_passtool.py find --level 2       # generate valid passwords for a level
```

**Re-create the SCSI-sniffer ROM** from your own dump:

```bash
python tools/make_patch.py firmware/original/27C1024.BIN 27C1024_SCSI_CKSUM.BIN ck
```

Burn the result (or, for a 2-chip build, `firmware/patched/K2_SCSI_LOW_D0-D7.bin` and
`…_HIGH_D8-D15.bin`), then: **Main Menu → A Test/Debug → I SCSI Sniffer**.

## Technical notes

- ROM maps at physical **`0xE0000`** (`file_offset + 0xE0000 = phys`); reset vector
  `JMP FE47:0006` at `0xFFFF0`.
- Password check routine: `EF65:001A`, salt `"NATO"`, fold
  `h = ((h*2 + in[i])*2 + salt[i mod 4]) mod 2^16`.
- EPROM self-test = 16-bit sum of all bytes `!= 0xFF` over `0xE0000…0xFFFFD`,
  expected value stored LE at `0x1FFFE/0x1FFFF`.

See the files in [`docs/`](docs/) for the full analysis.

## License & firmware ownership

Documentation and tools (`docs/`, `tools/`, `hardware/`, this README) are released
under the **MIT License** — see [`LICENSE`](LICENSE).

The firmware images under `firmware/` are **not** covered by that license; they
remain the property of their respective rights holder and are included for
preservation, interoperability, repair and research of obsolete hardware. See
[`NOTICE.md`](NOTICE.md).
