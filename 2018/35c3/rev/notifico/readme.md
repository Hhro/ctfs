## notifico



### Analyze

As you unzip `chall.tar.gz` as problem suggest, there are massive link-file and sub-directory.

After traverse some sub-directory, you can notice there are 1 regular file per directory, and link-file numbers are different from directory to directory. 

Before jump into binary `check`, let's read check.py first.

```python
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

```

First, it needs argv[1] as basedirectory. and pass it to binary `check`.

Second, it check return value of `check argv[1]` and if something goes wrong, it exit().

Third, if `check argv[1]` returns with 15, it make string through weird routine, which use regular file's perm and it called `magic`.

Last, with `magic`, it decrypt `enc_flag` and if it contain sub-string `35C3_` , It would print it.

It's unhelpful yet.. 

---

For more information, let's analyze `check`.

It does simple job. 

At function `sub_16AA`, it searches every sub-directory of `argv[1]` (basedir) to find regular files, and add it to inotify wating file list. this watcher checks events, `accessed` and `writable-file closed`.

> You can check https://mirrors.edge.kernel.org/pub/linux/kernel/people/rml/inotify/headers/inotify.h to find mask_value about inotify event.

One thing you have to read careful in this function is this line in subfunction `sub_14EA`.

`((v9 & 0x80) != 0) != ((v9 & 0x40) != 0) || v9 & 0x3F`

If regular file's permission is not 700 and not 400, it exit().
So every regular file has permission `rwx` or `r`

In function `sub_1815`, it opens and closes every regular file in sub-directory of basedir, and it's all.

There remains last, and most important function `sub_194D`.

It first, poll fds which is inotified, and read_events from `fds.fd` when it's ready to be read. 

After it reads event, it check if events is `accessed` or `writable file closed`. If it is latter, it increments `dword_40C4`(which is `main` function return value) and `execve ` every link file in the directory where event occuring file included, or if it is former, call `exit()`. 

---

Let's follow the binary step by step,

1. It make every regular file to be inotifed(event 1 & 8).
2. It opens every regular file and close. If file has perm 700, it would make event `writable file closed`, else nothing happen.
3. poll every inotified fds, read event and branch according to event.
4. Because every regular perm`700` file make event `writable file closed` , it read every this event and try to execute every link file in same directory. If any of this try succeed, it would make event `accessed` and will kill binary.

---

Sum up the information about `check.py` and `check`, and find a way which problem demands.

- Every regular file has to be have permission 700 or 400
- `check` must return 15.
-  `check` returns num of the regular file which has perm 700.
- `check` killed with -1 or 255, when more than two files(link and regfile) in same directory, is executable.

In conclusion, it demands to find out set of regular files which has perm 700,  and every link file in same directory links to non-executable file.

---

### Solution

First you should make graph structure, including information about which regular file dominate which regular file. (dominate means if it has perm 700, dominated must not have 700)

```python
graph={}

for root, dirs, x in os.walk('chall'):
    for dir in dirs:
        for _,_,files in os.walk('chall/'+dir):
            key=''
            link=[]
            for file in files:
                mode=os.lstat('/'.join([root,dir,file])).st_mode
                if S_ISREG(mode):
                    key='/'.join([dir,file])
                    graph.update({key:[]})
                else: 
                    link.append(os.readlink('/'.join([root,dir,file]))[3:]) 
                    graph[key]=link
```

After make graph, you have to find complete sub-graph which has 15 nodes.

If there is no other clue, it's NP-complete problem(clique problem).

However, thanks to hint, you can guess it's special case of clique problem, N-Queen, which has 15x15 chess board and 15 queens.

You can be more sure if you check number of edges per node.
Max value is 56, and it decrements 2 to min value, 42. It's definitely queen's movement.
(Center queen can move to 56 locations of board, and queen at edges can move to 42 locations of board)

Unfortunately, noticing it is just beginning of the problem.

I first thought every location of board is matched with directory name in sorted order. But, it's not the case. I can't find any clue about which directory represents which location of board except above graph.

So all you have to do is make chess-board complete with graph information, and solve 15-Queen problem. Thanks to google, there are many python N-queen solver. you could use it for your mental health.

In addition, 15-Queen problem has more than 2000000 solutions. So you should brute-forcing every solution case to solve it. If you find the case, you can make correct `magic` string and decrypt `enc_flag`. You sould be patient...

I think making board complete is hardest job in this problem. You can find the full solution at sol.py, which is almost undecodable and unorginized ;\ (sorry)
Maybe after taking some rest, I would clean it up.

Thanks to read my write-up, and feel free to ask about it. You can contact me through hhro9712@gmail.com.

 I would respond with full of grammar error :)