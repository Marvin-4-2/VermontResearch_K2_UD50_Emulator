#!/usr/bin/env python3
"""Patch 27C1024.BIN: make the hidden SCSI Sniffer (Menu_8) reachable via key 'I'
in the Test/Debug menu. Non-destructive relocation of the Menu_2 option array."""
import sys, os

SRC = sys.argv[1] if len(sys.argv) > 1 else '27C1024.BIN'
OUT = sys.argv[2] if len(sys.argv) > 2 else '27C1024_SCSI.BIN'
FIX_CKSUM = (len(sys.argv) > 3 and sys.argv[3] == 'ck')
ROM = 0xE0000

data = bytearray(open(SRC, 'rb').read())
assert len(data) == 0x20000, f"unexpected size {len(data):#x}"

# --- geometry ------------------------------------------------------------
DESC      = 0x11DF0          # Menu_2 (Test/Debug) descriptor
OLD_ARR   = 0x11DA8          # original 8-record option array (stays, unused)
STUB      = (0xF1EC, 0x00BA) # handler that opens Menu_8  -> f1ec:00BA
NEW_STR   = 0x1F000          # free 0xFF space: label string lives here (phys 0xFF000)
NEW_ARR   = 0x1F010          # free 0xFF space: relocated 9-record array (phys 0xFF010)
LABEL     = b"SCSI Sniffer\x00"
NEWKEY    = ord('I')         # 0x49, sorts right after 'H'

def far(phys):               # phys -> (off,seg) bytes LE, paragraph aligned (data only)
    seg = (phys >> 4) & 0xFFFF
    off = phys & 0xF
    return far_so(seg, off)

def far_so(seg, off):        # explicit seg:off -> 4 bytes LE (needed when seg==CS matters)
    return bytes([off & 0xFF, (off >> 8) & 0xFF, seg & 0xFF, (seg >> 8) & 0xFF])

# --- sanity: target free region must be erased (0xFF) ---------------------
need_end = NEW_ARR + 9*9
for a in range(NEW_STR, NEW_STR+len(LABEL)):
    assert data[a] == 0xFF, f"string area not free @ {a:#x}"
for a in range(NEW_ARR, need_end):
    assert data[a] == 0xFF, f"array area not free @ {a:#x}"
assert need_end < 0x1FFF0, "would collide with reset vector"

orig = bytes(data)
changes = []   # (offset, old_bytes, new_bytes, note)

# 1) write label string in free space
new = LABEL
changes.append((NEW_STR, orig[NEW_STR:NEW_STR+len(new)], new, 'Label-String "SCSI Sniffer"'))

# 2) build relocated array: 8 original records verbatim + new 9th record
arr = bytearray(orig[OLD_ARR:OLD_ARR+8*9])          # copy A..H
# label = any seg:off to the string (data read); handler MUST keep seg=0xF1EC
# because the stub uses CS-relative addressing (les bx, cs:[0x1e]).
rec = bytes([NEWKEY]) + far(NEW_STR+ROM) + far_so(STUB[0], STUB[1])  # key,label,handler
arr += rec
changes.append((NEW_ARR, orig[NEW_ARR:NEW_ARR+len(arr)], bytes(arr),
                "9-Record-Array (A..H kopiert + 'I' SCSI Sniffer)"))

# 3) descriptor: count 8 -> 9
changes.append((DESC+4, orig[DESC+4:DESC+6], bytes([9,0]), 'count 8 -> 9'))

# 4) descriptor: optarray far-ptr -> new array
changes.append((DESC+8, orig[DESC+8:DESC+12], far(NEW_ARR+ROM), 'optarray -> neues Array'))

# apply functional changes
for off, old, nw, note in changes:
    data[off:off+len(nw)] = nw

# --- checksum neutralisation --------------------------------------------
# EPROM self-test = 16-bit sum of all bytes != 0xFF over file 0x00000..0x1FFFD,
# expected value stored LE at 0x1FFFE/0x1FFFF (excluded from the sum itself).
def rom_cksum(buf):
    s = 0
    for b in buf[0:0x1FFFE]:
        if b != 0xFF:
            s = (s + b) & 0xFFFF
    return s

if FIX_CKSUM:
    new_ck = rom_cksum(data)
    old_ck_bytes = bytes(orig[0x1FFFE:0x20000])
    new_ck_bytes = bytes([new_ck & 0xFF, (new_ck >> 8) & 0xFF])
    data[0x1FFFE:0x20000] = new_ck_bytes
    changes.append((0x1FFFE, old_ck_bytes, new_ck_bytes,
                    f'EPROM-Pruefsumme -> 0x{new_ck:04X} (Selbsttest passed)'))

open(OUT, 'wb').write(data)

# --- report --------------------------------------------------------------
print(f"Quelle : {SRC}  ({len(orig)} bytes)")
print(f"Ziel   : {OUT}  ({len(data)} bytes)\n")
print("Geänderte/geschriebene Bytes:")
for off, old, nw, note in changes:
    o = old.hex(' ')
    n = nw.hex(' ')
    if len(o) > 60: o = o[:57]+'...'
    if len(n) > 60: n = n[:57]+'...'
    print(f"  @0x{off:05X}  {note}")
    print(f"       alt: {o}")
    print(f"       neu: {n}")

dsum = (sum(data) - sum(orig))
print(f"\nByte-Summen-Delta (für optionalen BITS-EPROM-Selbsttest): {dsum:+d}")
PY_END = None
