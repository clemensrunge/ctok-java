"""Compile upstream data; run with ctok's locked Python environment."""
import sys, json, struct, unicodedata, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
from ctok import normalize as api_normalize
from ctok.normalize import classify, _stray_mark, _marks_like_punct, _digit_border, _is_upper, _is_lower, _lower, is_separator
root = Path(__file__).resolve().parents[1]
out = root / 'src/main/resources/dev/ctok'
def string(f, s):
    b = s.encode('utf-8'); f.write(struct.pack('>i', len(b))); f.write(b)
with (out/'unicode.bin').open('wb') as f:
    for cp in range(65536):
        c=chr(cp); cat=unicodedata.category(c)
        flags = int(_stray_mark(c)) | int(_marks_like_punct(c))<<1 | int(_digit_border(c))<<2 | int(_is_upper(c))<<3 | int(_is_lower(c))<<4 | int(cat[0] in 'LM' or cp in (0x1c89,0x1c8a,0xa7cb,0x264))<<5
        f.write(bytes([['wordy','hard','digit','punct','space'].index(classify(c)),flags, {'Nd':1,'No':2}.get(cat,0)]))
        string(f, _lower(c) if not 0xd800<=cp<=0xdfff else '\ufffd')
for family in ['v3','v4_7']:
    src=Path(sys.argv[1])/'ctok/data'/f'pieces_{family}.json'
    doc=json.loads(src.read_text()); meta=doc['meta']
    with (out/f'{family}.bin').open('wb') as f:
        f.write(struct.pack('>i?i',meta['message_overhead'],meta['fold_quotes'],meta['allcaps_min'] or 0))
        entries=[(g,k,w) for g,items in doc['tokens'].items() for k,w in items.items()]
        f.write(struct.pack('>i',len(entries)))
        for g,k,w in entries:
            string(f,g); string(f,k); string(f,w.get('probe','')); f.write(struct.pack('>i',w.get('raw',0))); string(f,w['kind'])
print('Exported vocabulary and Unicode',unicodedata.unidata_version)
