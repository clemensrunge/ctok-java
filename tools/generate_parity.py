"""Generate expected results by executing Python ctok, never copying recorded counts.
Usage: ../ctok/.venv/bin/python tools/generate_parity.py ../ctok build/parity.bin
"""
import gzip, importlib.util, json, random, struct, sys
from pathlib import Path
upstream=Path(sys.argv[1]).resolve(); sys.path.insert(0,str(upstream))
from ctok import tokenize, normalize, marked_stream
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from export_helpers import write_string
samples=[]
def add(label,text): samples.append((label,text))
for path in sorted((upstream/'tests/fixtures').glob('*.jsonl.gz')):
    with gzip.open(path,'rt') as f:
        for i,line in enumerate(f): add(f'{path.stem}:{i}',json.loads(line)['text'])
spec=importlib.util.spec_from_file_location('api_tests',upstream/'tests/test_api.py'); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
for name in ('MARK_ROWS','APOSTROPHE_ROWS','SPACE_RUN_ROWS','CONTRACTION_ROWS','SYMBOL_ROWS','PIECE_ROWS'):
    for i,row in enumerate(getattr(module,name)):
        add(f'{name}:{i}',row[0] if name=='MARK_ROWS' else row[1])
for text in ['', 'hello, world', 'GaN WiFi QQ HELLO Hello', 'don’t “quote”', 'ทํางาน นํ้า น้ํา', '\ud800', '\udfff', '\ud800x\udfff', 'x\ue000y', '\ufdd0\ufdd1\ufdd2\ufdd3\ufdd4', '⟨bow⟩ ⟨0xFF⟩', 'ϴ Θϴ İ ẞ ΣΣΣΣ', '\u1c89abc \ua7cb'*4]: add('edge',text)
for n in range(150):
    for prefix in ('','hello', '123', '日本', "'First"):
        add(f'newline:{n}',prefix+'\n'*n)
for cp in range(65536):
    # Lone surrogates are encoded as U+FFFD for transport, which is their normalization.
    if 0xd800<=cp<=0xdfff: continue
    add(f'BMP:{cp:04X}',chr(cp))
rng=random.Random(1701)
pool=list('abcXYZ123 \t\n.,\'"')+[chr(i) for i in range(65536) if not 0xd800<=i<=0xdfff]+['😀','𐐀','𐐨','𠀀','\U000f0000','\U000e0100']
for i in range(3000): add(f'random:{i}',''.join(rng.choice(pool) for _ in range(rng.randrange(1,60))))
# Recorded witnesses cover the vocabulary pieces in their intended contexts.
for family in ('v3','v4_7'):
    doc=json.loads((upstream/f'ctok/data/pieces_{family}.json').read_text())
    for group,entries in doc['tokens'].items():
        for key,w in entries.items():
            if 'probe' in w: add(f'witness:{family}:{group}',w['probe'])
output=Path(sys.argv[2]); output.parent.mkdir(parents=True,exist_ok=True)
with output.open('wb') as f:
    f.write(struct.pack('>i',len(samples)*3))
    for i,(label,text) in enumerate(samples):
        for version in ('3.0','4.7','4.8'):
            tokens=tokenize(text,version)
            for s in (label,version,text,normalize(text,version),marked_stream(text,version)): write_string(f,s)
            f.write(struct.pack('>i',len(tokens)))
            for token in tokens: write_string(f,token)
        if i%10000==0: print(f'{i}/{len(samples)}',flush=True)
print(f'{len(samples)*3} reference cases -> {output}',flush=True)
