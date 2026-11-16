#!/usr/bin/env python3
"""
k2_passtool.py - Hash-/Entsperr-Tool fuer die K2 / UD50 Service-Passwortabfrage.

Bildet die Pruefroutine aus dem Programm-EPROM (27C1024.BIN, NEC V30) exakt nach:
pro akzeptiertem Zeichen i gilt
        h = ((h*2 + eingabe[i]) * 2 + salt[idx mod len(salt)])  (mod 65536)
mit salt = "NATO". Zeichen <= 0x1F oder >= 0x7F werden ignoriert, CR beendet.
Zugang wird gewaehrt, wenn h == ziel_hash.

Bekannte Stufen:
    Stufe 1  ->  0x2020   (Anzeige / verstecktes Menue verlassen)
    Stufe 2  ->  0x4ABC   (schreibende / zerstoererische Aktionen, NVRAM-Write)

Es ist KEIN Klartext-Passwort gespeichert; verglichen wird nur dieser 16-Bit-Hash.
Da der Hash viele Kollisionen hat, ist das Original-Passwort nicht eindeutig -
dieses Tool erzeugt stattdessen beliebige GUELTIGE, tippbare Passwoerter.

Beispiele:
    python k2_passtool.py hash 4796878
    python k2_passtool.py check GEHEIM --level 2
    python k2_passtool.py find 0x2020
    python k2_passtool.py find --level 2 --charset upper --count 5
    python k2_passtool.py find 0x4abc --prefix OPENK2
    python k2_passtool.py list
    python k2_passtool.py selftest
"""
from __future__ import annotations
import argparse
import sys
from collections import deque

DEFAULT_SALT = "NATO"

LEVELS = {
    0x2020: "Stufe 1  (Anzeige / Menue verlassen)",
    0x4ABC: "Stufe 2  (schreibend / zerstoererisch)",
}

CHARSETS = {
    "digits": [chr(c) for c in range(0x30, 0x3A)],                         # 0-9
    "upper":  [chr(c) for c in range(0x41, 0x5B)],                         # A-Z
    "lower":  [chr(c) for c in range(0x61, 0x7B)],                         # a-z
    "alnum":  [chr(c) for c in range(0x30, 0x3A)]
              + [chr(c) for c in range(0x41, 0x5B)]
              + [chr(c) for c in range(0x61, 0x7B)],
    "ascii":  [chr(c) for c in range(0x20, 0x7F)],                         # alle druckbaren
}


# --------------------------------------------------------------------------- #
#  Kern: exakte Nachbildung der ROM-Routine
# --------------------------------------------------------------------------- #
def fold_step(h: int, idx: int, ch: int, salt: bytes) -> tuple[int, int]:
    """Ein akzeptiertes Zeichen falten. Gibt (neuer_hash, neuer_idx) zurueck."""
    h = ((h << 1) + ch) & 0xFFFF
    if idx >= len(salt) or salt[idx] == 0:
        idx = 0
    h = ((h << 1) + salt[idx]) & 0xFFFF
    return h, idx + 1


def k2_fold(text: str, salt: str = DEFAULT_SALT) -> int:
    """16-Bit-Hash einer Eingabe berechnen (wie die ROM-Routine)."""
    sb = salt.encode("latin1")
    h, idx = 0, 0
    for c in text:
        o = ord(c)
        if o == 0x0D:            # Enter -> fertig
            break
        if o <= 0x1F or o >= 0x7F:   # ignoriert (Beep)
            continue
        h, idx = fold_step(h, idx, o, sb)
    return h


def matched_levels(h: int) -> list[int]:
    return [t for t in LEVELS if t == h]


# --------------------------------------------------------------------------- #
#  Passwort-Generierung: kuerzestes gueltiges Suffix per BFS ueber (hash, idx%4)
# --------------------------------------------------------------------------- #
def generate(target: int,
             charset: list[str],
             salt: str = DEFAULT_SALT,
             prefix: str = "",
             want: int = 10,
             max_len: int = 12) -> list[str]:
    """
    Liefert bis zu `want` gueltige Passwoerter, die (nach optionalem festem
    `prefix`) mit einem moeglichst kurzen Suffix aus `charset` den Ziel-Hash
    erreichen. Der Salt-Phasenzustand des Prefix wird korrekt beruecksichtigt.
    """
    sb = salt.encode("latin1")
    period = len(sb)

    # Startzustand nach dem festen Prefix berechnen
    h0, idx0 = 0, 0
    for c in prefix:
        o = ord(c)
        if o == 0x0D or o <= 0x1F or o >= 0x7F:
            continue
        h0, idx0 = fold_step(h0, idx0, o, sb)
    start = (h0, idx0 % period)

    if h0 == target and (not charset or prefix):
        # Prefix trifft bereits (nur sinnvoll, wenn ueberhaupt ein Prefix da ist)
        if prefix:
            return [prefix]

    ords = [ord(c) for c in charset]
    # BFS: Zustand = (hash, idx%4). Pro Zustand einen Vorgaenger merken,
    # danach mehrere Loesungen durch begrenztes Nachverfolgen erzeugen.
    results: list[str] = []
    # frontier: Liste (state, suffix_string)
    frontier = [(start, "")]
    seen = {start}
    for _ in range(max_len):
        nxt = []
        for (h, phase), suf in frontier:
            # echter idx fuer Salt = aktuelle Laenge-Phase; salt-index == phase
            for o in ords:
                nh = ((h << 1) + o) & 0xFFFF
                nh = ((nh << 1) + sb[phase % period]) & 0xFFFF
                nphase = (phase + 1) % period
                nstate = (nh, nphase)
                nsuf = suf + chr(o)
                if nh == target:
                    results.append(prefix + nsuf)
                    if len(results) >= want:
                        return _verify(results, target, salt)
                if nstate not in seen:
                    seen.add(nstate)
                    nxt.append((nstate, nsuf))
        if results:          # kuerzeste Laenge gefunden -> genug
            return _verify(results, target, salt)
        frontier = nxt
        if not frontier:
            break
    return _verify(results, target, salt)


def _verify(cands: list[str], target: int, salt: str) -> list[str]:
    out, seen = [], set()
    for c in cands:
        if c in seen:
            continue
        seen.add(c)
        if k2_fold(c, salt) == target:
            out.append(c)
    out.sort(key=lambda s: (len(s), s))
    return out


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def resolve_target(args) -> int | None:
    if getattr(args, "level", None):
        return 0x2020 if args.level == "1" else 0x4ABC
    if getattr(args, "hash", None) is not None:
        return int(args.hash, 0) & 0xFFFF
    return None


def cmd_hash(args):
    h = k2_fold(args.text, args.salt)
    print(f'Eingabe : {args.text!r}')
    print(f'Salt    : {args.salt!r}')
    print(f'Hash    : 0x{h:04X}  ({h})')
    m = matched_levels(h)
    if m:
        for t in m:
            print(f'ZUGANG  : {LEVELS[t]}  (Hash 0x{t:04X})  -> korrekt!')
    else:
        print('ZUGANG  : keine bekannte Stufe (kein Treffer)')
    if args.level:
        tgt = 0x2020 if args.level == "1" else 0x4ABC
        ok = (h == tgt)
        print(f'Pruefung Stufe {args.level}: {"OK - akzeptiert" if ok else "ABGELEHNT"}')
        return 0 if ok else 1
    return 0


def cmd_find(args):
    target = resolve_target(args)
    if target is None:
        print("Fehler: Ziel fehlt. Gib einen Hash (z.B. 0x2020) oder --level 1|2 an.",
              file=sys.stderr)
        return 2
    cs = CHARSETS[args.charset]
    sols = generate(target, cs, salt=args.salt, prefix=args.prefix,
                    want=args.count, max_len=args.max_len)
    label = LEVELS.get(target, "(unbekannte Stufe)")
    print(f'Ziel-Hash : 0x{target:04X}   {label}')
    print(f'Salt      : {args.salt!r}   Zeichensatz: {args.charset}'
          + (f'   Prefix: {args.prefix!r}' if args.prefix else ''))
    if not sols:
        print('Keine Loesung im Laengenlimit gefunden - erhoehe --max-len '
              'oder waehle einen groesseren Zeichensatz.')
        return 1
    print(f'Gueltige Passwoerter ({len(sols)}):')
    for s in sols:
        print(f'  {s}   (len {len(s)}, verifiziert 0x{k2_fold(s, args.salt):04X})')
    return 0


def cmd_list(args):
    print("Bekannte Passwort-Stufen der K2/UD50-Firmware (Salt 'NATO'):\n")
    for t, desc in LEVELS.items():
        pw = generate(t, CHARSETS["digits"], want=1)
        example = pw[0] if pw else "(?)"
        print(f'  Hash 0x{t:04X}  {desc}')
        print(f'             Beispiel-Passwort: {example}\n')
    return 0


def cmd_selftest(args):
    ok = True
    cases = [("4796878", 0x2020), ("5967976", 0x4ABC),
             ("AUYYW", 0x2020), ("UZZXY", 0x4ABC)]
    print("Selbsttest (bekannte Passwort/Hash-Paare):")
    for pw, exp in cases:
        h = k2_fold(pw)
        good = (h == exp)
        ok &= good
        print(f'  {pw:<10} -> 0x{h:04X}  erwartet 0x{exp:04X}  {"OK" if good else "FAIL"}')
    # Generator-Rundlauf
    for t in LEVELS:
        for name in ("digits", "upper", "alnum"):
            sols = generate(t, CHARSETS[name], want=3)
            bad = [s for s in sols if k2_fold(s) != t]
            status = "OK" if (sols and not bad) else "FAIL"
            ok &= bool(sols) and not bad
            print(f'  gen 0x{t:04X} [{name:<6}] -> {sols[:3]}  {status}')
    # Prefix-Funktion
    sols = generate(0x2020, CHARSETS["digits"], prefix="OPENK2", want=2)
    good = bool(sols) and all(k2_fold(s) == 0x2020 and s.startswith("OPENK2") for s in sols)
    ok &= good
    print(f'  prefix "OPENK2" -> {sols[:2]}  {"OK" if good else "FAIL"}')
    print("\nErgebnis:", "ALLE TESTS OK" if ok else "FEHLER!")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="k2_passtool",
        description="Hash-/Entsperr-Tool fuer die K2/UD50 Service-Passwortabfrage "
                    "(Salt 'NATO', 16-Bit-Fold-Hash).")
    p.add_argument("--salt", default=DEFAULT_SALT,
                   help="Referenz-/Salt-String (Standard: NATO)")
    sub = p.add_subparsers(dest="cmd")

    h = sub.add_parser("hash", aliases=["check"],
                       help="Hash einer Eingabe berechnen / gegen Stufe pruefen")
    h.add_argument("text", help="Passwort-/Eingabetext")
    h.add_argument("--level", choices=["1", "2"],
                   help="zusaetzlich gegen diese Stufe pruefen")
    h.set_defaults(func=cmd_hash)

    f = sub.add_parser("find", aliases=["gen"],
                       help="gueltige Passwoerter zu einem Hash erzeugen")
    f.add_argument("hash", nargs="?",
                   help="Ziel-Hash, z.B. 0x2020 (oder --level verwenden)")
    f.add_argument("--level", choices=["1", "2"], help="bekannte Stufe als Ziel")
    f.add_argument("--charset", choices=list(CHARSETS), default="digits",
                   help="Zeichensatz fuer die Erzeugung (Standard: digits)")
    f.add_argument("--prefix", default="",
                   help="fester Anfang; das Tool ergaenzt ein passendes Suffix")
    f.add_argument("--count", type=int, default=10, help="Anzahl Ergebnisse")
    f.add_argument("--max-len", type=int, default=12, help="max. Suffix-Laenge")
    f.set_defaults(func=cmd_find)

    sub.add_parser("list", help="bekannte Stufen + Beispiel-Passwoerter zeigen"
                   ).set_defaults(func=cmd_list)
    sub.add_parser("selftest", help="Selbsttest ausfuehren"
                   ).set_defaults(func=cmd_selftest)
    return p


def main(argv=None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    if not getattr(args, "cmd", None):
        p.print_help()
        print()
        cmd_list(args)
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
