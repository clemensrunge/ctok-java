import struct

def write_string(f,s):
    # UTF-8 has no lone-surrogate representation; transport their equivalent replacement.
    s=''.join('\ufffd' if 0xd800<=ord(c)<=0xdfff else c for c in s)
    b=s.encode('utf-8'); f.write(struct.pack('>i',len(b))); f.write(b)
