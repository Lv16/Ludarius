#!/usr/bin/env python3
"""
Dedupe .po by msgid, keeping the first occurrence of each msgid.
Usage: python dedupe_po.py <input.po> <output.po>
"""
import sys
import re

if len(sys.argv) != 3:
    print("Usage: dedupe_po.py <input.po> <output.po>")
    sys.exit(2)

inpath = sys.argv[1]
outpath = sys.argv[2]

with open(inpath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

blocks = []
cur = []
for line in lines:
    if line.strip() == "" and cur:
        blocks.append(cur)
        cur = []
    else:
        cur.append(line)
if cur:
    blocks.append(cur)

seen = set()
output_blocks = []

# Helper to extract msgid string from a block
msgid_re = re.compile(r'^msgid\s+"(.*)"')
cont_re = re.compile(r'^"(.*)"')

for block in blocks:
    # find msgid line index
    msgid_idx = None
    for i, l in enumerate(block):
        if l.lstrip().startswith('msgid'):
            msgid_idx = i
            break
    if msgid_idx is None:
        # no msgid (shouldn't happen) - keep block
        output_blocks.append(block)
        continue
    # collect msgid content including continued lines until a line that starts with msgstr
    msgid_parts = []
    i = msgid_idx
    m = msgid_re.match(block[i].lstrip())
    if m:
        msgid_parts.append(m.group(1))
    i += 1
    while i < len(block) and not block[i].lstrip().startswith('msgstr'):
        cm = cont_re.match(block[i].lstrip())
        if cm:
            msgid_parts.append(cm.group(1))
        i += 1
    full_msgid = '\\n'.join(msgid_parts)
    if full_msgid in seen:
        # skip duplicate
        continue
    seen.add(full_msgid)
    output_blocks.append(block)

with open(outpath, 'w', encoding='utf-8') as f:
    for b in output_blocks:
        for l in b:
            f.write(l)
        f.write('\n')

print(f'Written deduplicated .po to {outpath} (keeps {len(output_blocks)} blocks)')
