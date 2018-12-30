#!/usr/bin/env python3
from sys import argv
import os, subprocess, re
from stat import S_ISREG
from hashlib import sha256
from Crypto.Cipher import AES

# Remember, only chmod, no touch! Also, make sure to keep symlinks while extracting.

VAL = 15
flag_fmt = r"35C3_[\w]*"

# enc_flag = AES.new(sha256(my_magic).digest()).encrypt(b'35C3_my_example_flag_AAAAAAAAAAA')
enc_flag = b'\x99|8\x80oh\xf57\xd4\x81\xa5\x12\x92\xde\xf5y\xbc\xc0y\rG\xa8#l\xb6\xa1/\xfeE\xc5\x7f\x85\x9a\x82\x0b\x02Y{\xd9/\x92X>p\\\xb7H\xb1{\xcf\x8b/r=\x87-#\xae\x95\xb6\xd1\r\x03\x13'

if len(argv) != 2:
    print("Usage: {} <base_dir>".format(argv[0]))
    exit(-1)

basedir = argv[1]

res = subprocess.call(["./check", basedir])

if res == 255 or res != VAL:
    print("This looks no good...")
    exit(-1)
else:
    print("A worthy try, let's see if it yields something readable...")

fs = {}

magic = ""
for root, dirs, files in os.walk(basedir):
    for file in files:
        path = os.path.join(root, file)
        mode = os.lstat(path).st_mode
        if S_ISREG(mode):
            fs[path] = "{:o}".format(mode & 0o777)

for path in sorted(fs.keys()):
    magic += fs[path]

print("magic: ", magic)

try:
    flag = AES.new(sha256(magic.encode()).digest(), AES.MODE_ECB).decrypt(enc_flag)
    if re.fullmatch(flag_fmt, flag.decode()) is not None:
        print("Looks good, here is your output: {}".format(flag))
        exit(0)
except Exception:
    pass

print("Sorry, I only see gibberish. Do you have more where that came from?")

