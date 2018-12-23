## Analyze

문제자체는 쉬운편이니, 문제풀이 보다는 주어진 netbsd모듈인 `chall1.kmod`를 분석하는 것에 집중하겠습니다. 

chall1.kmod에는 총 8개의 함수가 있습니다. 

- chall1_close
- chall1_open
- chall1_write
- chall1_modcmd
- md5hash
- sha1hash
- get_flag_ready
- chall1_read

하나하나 분석하기 전에, 대충 봤을 때 문제풀이에 중요해보이는 함수는 `get_flag_ready`임을 바로 알 수 있습니다(실제로, 저것만 읽어보면 문제가 풀립니다). 하지만 그게 중요한게 아니니, 모듈 동작의 핵심으로 보이는 chall1_modcmd를 먼저 분석하겠습니다.

---

### chall1_modcmd

> ref1 : http://netbsd.gw.com/cgi-bin/man-cgi?module+9+NetBSD-current
>
> ref2 : http://netbsd.gw.com/cgi-bin/man-cgi?devsw_attach+9+NetBSD-current

```c
int chall1_modcmd(modcmd_t cmd)
{
  int cmajor; // [esp+14h] [ebp-8h]
  int bmajor; // [esp+18h] [ebp-4h]

  cmajor = 210;
  bmajor = -1;
    
  switch(cmd):
    case MODULE_CMD_INIT:
      if ( devsw_attach("chall1", 0, &bmajor, &chall1_cdevsw, &cmajor))
        return 6;
      else 
        return 0;
    case MODULE_CMD_FINI:
      if ( sc <= 0 ){
        devsw_detach(0, &chall1_cdevsw);
        return 0;
      }
      else
        return 16;
    default:
      return 25;
}
```

netbsd에서 module을 load할 때, modcmd(MODULE_CMD_INIT)을 호출합니다. 이 모듈 에서는 MODULE_CMD_INIT의 경우, `devsw_attach("chall1", 0, &bmajor, &chall1_cdevsw, &cmajor)`을 호출합니다. 이 함수는 드라이버와 필수적인 구조체를 링크해주는 역할을 합니다.

핵심이 되는 구조체는 chall1_cdevsw입니다. 이 구조체의 원형은 다음과 같습니다.

```c
const struct cdevsw foo_cdevsw {
             int (*d_open)(dev_t, int, int, struct lwp *);
             int (*d_close)(dev_t, int, int, struct lwp *);
             int (*d_read)(dev_t, struct uio *, int);
             int (*d_write)(dev_t, struct uio *, int);
             int (*d_ioctl)(dev_t, u_long, void *, int, struct lwp *);
             void (*d_stop)(struct tty *, int);
             struct tty *(*d_tty)(dev_t);
             int (*d_poll)(dev_t, int, struct lwp *);
             paddr_t (*d_mmap)(dev_t, off_t, int);
             int (*d_kqfilter)(dev_t, struct knote *);
             int d_flag;
     };
```

생긴걸 보아하니 디바이스를 대상으로하는 I/O에 대한 핸들러 구조체인것 같습니다. 
그리고 위 함수의 chall1_cdevsw는 다음과 같습니다.

```c
.data:08000660 chall1_cdevsw   dd offset chall1_open   ; DATA XREF: chall1_modcmd+3F↑o
.data:08000660                                         ; chall1_modcmd:loc_8000157↑o
.data:08000664                 dd offset chall1_close
.data:08000668                 dd offset chall1_read
.data:0800066C                 dd offset chall1_write
.data:08000670                 dd offset enodev
.data:08000674                 dd offset enodev
.data:08000678                 dd 0
.data:0800067C                 dd offset seltrue
.data:08000680                 dd offset nommap
.data:08000684                 dd offset seltrue_kqfilter
.data:08000688                 dd offset enodev
```

이 둘을 대응해보면, 이 디바이스를 대상으로 `open, close, read, write`함수는 정의된 함수를 따르고, 나머지는 구현하지 않고 있음을 알 수 있습니다.

또한, 모듈을 unload할 때, modcmd(MODULE_CMD_FINI)를 먼저 호출하는데, 이 모듈에서는 devsw_detach를 호출하고, 이는 드라이버와 구조체를 분리하는 역할을 합니다.

---

#### chall1_open

> ref1 : http://netbsd.gw.com/cgi-bin/man-cgi?kmem_alloc+9+NetBSD-current

```c
signed int chall1_open()
{
  if ( sc > 0 )
    return 16;
  dword_80006A4 = 0;
  ++sc;
  cur_s_len = 100;
  s = (char *)kmem_alloc(100, KM_NOSLEEP);
  uvm_struct = (char *)uvm_km_alloc(kernel_map, 100, 0, UVM_KMF_WIRED|UVM_KMF_ZERO);
  return 0;
}
```

sc(s counter?)을 1증가시킴(device가 open됐다는 flag인듯)

- kmem_alloc(100, KM_NOSLEEP) : 크기 100의 커널 메모리를 할당하고 그 주소를 반환
- uvm_km_alloc(kernel_map, 100, 0, UVM_KMF_WIRED|UVM_KMF_ZERO) : 0으로 초기화된 크기 100의 커널 메모리를 `kernel_map`안에 연속되게 할당하고 그 주소를 반환

---

### chall1_write

> ref1 : http://netbsd.gw.com/cgi-bin/man-cgi?uiomove+9+NetBSD-6.0
>
> ref2 : https://saurvs.github.io/post/writing-netbsd-kern-mod/

```c
int chall1_write(dev_t self, struct uio * uio, int flags)
{
  if ( s )
    kmem_free(s, s_len);
  cur_s_len = uio->uio_iov->iov_len;
  s = (char *)kmem_alloc(cur_s_len, KM_NOSLEEP);
  uiomove(s, cur_s_len, uio);
  return 0;
}
```

먼저 할당된 s를 free합니다. 

그 뒤, 인자로 주어진 uio에서 iov_len을 구하여 그 만큼 새로 s를 할당하고,  uio에서 s로 데이터를 옮깁니다.

uio의 원형은 다음과 같습니다.

```c
struct uio {
                   struct  iovec *uio_iov;
                   int     uio_iovcnt;
                   off_t   uio_offset;
                   size_t  uio_resid;
                   enum    uio_rw uio_rw;
                   struct  vmspace *uio_vmspace;
           };
```

uiomove함수의 원형은 다음과 같습니다.

```c
int uiomove(void *buf, size_t n, struct uio *uio);
```

uiomove함수는 uio구조체의 uio_rw를 참조하여 데이터를 uio에서 read할지 또는 uio에서 buf로 write할지를 결정합니다.이 때, n과 uio_resid중에 작은 값만큼 쓰거나, 읽습니다. 이 함수는 커널스페이스와 유저스페이스 간에 값을 교환할 때 사용할 수 있습니다.

---

### chall1_read

> ref1 : https://saurvs.github.io/post/writing-netbsd-kern-mod/

```c
int __cdecl chall1_read(dev_t self, struct uio *uio, int flags)
{
  char res; // [esp+10h] [ebp-58h]

  if ( !strcmp(s,'give_this_to_get_flag'))
  {
    snprintf(&res, 0x19u, "%s", "Why don't you try again?");
    return uiomove(&res, 24, uio);
  }
  else
  {
    get_flag_ready();
    len_uvm = strlen(uvm_struct);
    snprintf(&s, len_uvm + 1, "%s", uvm_struct);
    return uiomove(&res, len_uvm + 1, uio);
  }
}
```

이 함수도 구조는 위의 write와 같습니다. 다만 아마도 이 함수를 호출할 때, uio의 uio_rw는 0으로 세팅되어 read로 설정되어야 겠죠. 

---

## Solve

### Intended Solution

> ref1 : https://docs.oracle.com/cd/E19120-01/open.solaris/819-3196/character-21002/index.html

아마 출제자의 의도는 chall1_write함수를 이용하여 전역변수 s가 가리키는 커널메모리에 "give_this_to_get_flag"를 입력하고, read함수의 분기문을 제대로 통과하여 flag를 받아내는 것일 겁니다. 

```c
#include <sys/cdefs.h>

#include <err.h> 
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#define _PATH_DEV_MAPPER "/dev/chall1"

int main(int argc, char **argv)
{
        int devfd;
        char *buf;

        buf = malloc(50);

        if ((devfd = open(_PATH_DEV_MAPPER, O_RDWR)) == -1)
                err(EXIT_FAILURE, "Cannot open %s", _PATH_DEV_MAPPER);

        strcpy(buf,"give_this_to_get_flag");
        write(devfd,buf,100);

        read(devfd, buf, 100);
        printf("%s", buf);
        if (close(devfd) == -1)
                err(EXIT_FAILURE, "Cannot close %s", _PATH_DEV_MAPPER);

        return EXIT_SUCCESS;
}
```

여기서 왜 write함수에 uio struct * buf가 아니라, char * buf를 전달하는지 의아할 수 있습니다.  관련된 레퍼런스를 찾아보면 Oracle에 이런 예제와 설명이 있습니다.

---

When a user thread issues a [write(2)](https://docs.oracle.com/docs/cd/E19963-01/821-1463/write-2/index.html) system call, the thread passes the address of a buffer in user space:

```c
char buffer[] = "python";
count = write(fd, buffer, strlen(buffer) + 1);
```

The system builds a [uio(9S)](https://docs.oracle.com/docs/cd/E19963-01/821-1478/uio-9s/index.html) structure to describe this transfer by allocating an [iovec(9S)](https://docs.oracle.com/docs/cd/E19963-01/821-1478/iovec-9s/index.html) structure and setting the `iov_base` field to the address passed to [write(2)](https://docs.oracle.com/docs/cd/E19963-01/821-1463/write-2/index.html), in this case, `buffer`. The [uio(9S)](https://docs.oracle.com/docs/cd/E19963-01/821-1478/uio-9s/index.html) structure is passed to the driver [write(9E)](https://docs.oracle.com/docs/cd/E19963-01/821-1476/write-9e/index.html) routine. See [Vectored I/O](https://docs.oracle.com/cd/E19120-01/open.solaris/819-3196/character-15613/index.html) for more information about the [uio(9S)](https://docs.oracle.com/docs/cd/E19963-01/821-1478/uio-9s/index.html) structure.

---

즉, 유저가 버퍼 주소만 전달하면 이를 커널 측에서 uio structure로 가공하여 driver_write루틴으로 전달한다는 것이죠. 

따라서 위의 소스를 작성하고 컴파일한뒤, 실행하면 플래그가 출력됩니다.

```bash
localhost# gcc -o test test.c
localhost# ./test
flag{netB5D_i5_4ws0m3_y0u_sh0uld_7ry_i7}
```

---

### Quick_Solution

get_flag_ready()만 리버싱하시면 플래그를 구할 수 있습니다. 어렵지 않은 루틴이니 해보세요 :)

---

## Review

strip 되어 있지 않은 작은 크기의 netbsd모듈을 제공해 줘서 리버싱하기 편하고 공부하기 좋았다.