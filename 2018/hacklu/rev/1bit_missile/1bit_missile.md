> reference : https://xz.aliyun.com/t/2928

---

## Analyze

### Server-Side

지정된 nc를 실행하여 무슨 동작을 하는지 살펴보면

```bash
Enter target byte [0 - 262143]: 194401
]> 10111111 <[
Enter target bit: [0 - 7]: 7
}X> ---------------------------------------{0}
]> 00111111 <[
```

목표 바이트를 정하면, 그 바이트의 값을 비트로 보여줍니다. 그 다음 그 비트들중 목표 비트의 인덱스를 입력하면, 그 비트를 0으로 만들고, 수정된 rom바이너리를 qemu를 통해 실행시켜 줍니다.

이 때, 적절한 목표 바이트와 비트를 설정하면 flag를 보여준다고 합니다.

---

### Binary

우선 지정된 rom을 디버깅하기 위해 qemu를 사용합니다. 
명령어는 `qemu-system-i386 -s -S -no-graphics -bios ./rom`입니다.
그 뒤, gdb로 attach합니다. (<u>peda보다는 pwndbg사용을 권장</u>)서버의 출력로그를 읽어보면, ROM의 코드를 적절히 매핑한뒤 EP를 0x100000으로 잡고 실행함을 알 수 있으므로, gdb에서 0x100000에 브레이크포인트를 걸고 `c`합니다.

그러면 0x100000에서부터 코드가 정상적으로 매핑됨을 확인할 수 있습니다.

![0x100000](/images/rom.png)

이 상태에서 메모리를 덤프합니다.
명령어는 `dump binary memory dump.bin 0x100000 0xffffff`
그 뒤 dump.bin을 ida32로 디컴파일 한뒤 flag관련 스트링을 xref하면 흥미로운 함수를 발견할 수 있습니다.

```c
void __cdecl __noreturn sub_10009E(char a1)
{
  _BYTE *v1; // [esp+4h] [ebp-14h]

  sub_103CA3("FLAG if hit confirmed:");
  if ( (unsigned int)dword_FB1000 < 0xC8000 )
  {
    sub_103CA3("address out of scope!");
    sub_100160();
  }
  v1 = (_BYTE *)sub_102DF7(64);
  sub_103E95(v1, 0xC8000, 63);
  if ( *v1 )
    sub_103CA3(v1);
  else
    sub_103CA3("MISSED!");
  sub_100160();
}
```

이 함수에서 13번째 줄부터 있는 분기문을 보면, *v1이 0이 아닌 값으로 초기화되지 않으면, MISSED를 출력하는 것을 알 수 있습니다.

위 함수의 서브루틴들은 분석해보면 각각 다음과 같은 역할을 합니다.

- `sub_103CA3` : print
- `sub_100160` : exit
- `sub_103E95` : strncpy

여기서 12번째 줄의 `sub_103E95`(이하 strncpy)를 주목해보면, 두번째 인자의 값으로 `flag`문자열의 주소가 들어가면, 14번째 줄의 `sub_103CA3`(print)에 의해 flag을 출력시킬 수 있다는 것을 알 수 있습니다.

strncpy의 두번째 인자가 어떻게 계산되나 살펴보면 

```assembly
mov     edx, ds:dword_106BB0
mov     eax, ds:dword_106BC4
xor     eax, edx
mov     [ebp+var_10], eax
```

0x106BB0의 주소에 있는 값과, 0x106BC4의 주소에 있는 값을 xor하여 사용합니다.

따라서, 두번째 인자를 flag의 주소로 변경하기 위해서는 0x106BB0에 있는 값 혹은 0x106BC4에 있는 값을 변경해야 합니다.

flag의 위치는 gdb를 이용하여 찾아보면 0xc0000입니다.

`0x106BC4`: `0xEF5A3F92`
`0x106BB0`: `0xEF56BF92` 

`0xEF5A3F92^0xc0000 = 0xEF563F92`
`0x106BB1`:`0xBF`=`(0b10111111)`
`0x3F` = `0b00111111`

=>`0x106BB1`의 7번째 비트를 0으로 만들면 된다.

주의해야할 것이, 0x106BB1은 메모리에 올려진 뒤의 주소이므로, 실제 rom파일에서의 주소와는 다릅니다. 
`hexdump` 나 `ida`같은 디컴파일러를 이용해서 0xEF56Bf92를 find하면 rom파일 상에서의 이 주소를 알 수 있습니다.

```bash
0002f760  92 bf 56 ef de 62 c5 85  a5 c2 9f 9c 00 de ad c3  |..V..b..........|
0002f770  6a c7 00 00 92 3f 5a ef  fb 98 4f c5 83 a3 d0 5e  |j....?Z...O....^|
0002f780  b1 ad e1 6e db 36 ba bf  64 4c a1 fc 61 b4 f9 4b  |...n.6..dL..a..K|
0002f790  65 82 00 00 00 10 00 00  00 10 fb 00 00 00 00 00  |e...............|
0002f7a0  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
0002f7b0  c8 00 00 00 00 00 00 00  f8 03 00 00 00 00 00 00  |................|
0002f7c0  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
```

=> mem : 0x106BB1 == rom : 0x2f761 (d194401)

---

## Solve

```bash
$hhro nc arcade.fluxfingers.net 1816

Enter target byte [0 - 262143]: 194401
]> 10111111 <[
Enter target bit: [0 - 7]: 7
}X> ---------------------------------------{0}
]> 00111111 <[
...
//qemu log
...
flag{only_cb_can_run_this_simple_elf}
```

---

## Review

- Bios ROM은 qemu-system-"arch" -no-graphics -bios [rom]으로 실행할수 있다.

- Bios ROM은 qemu-system-"arch" -no-graphics -bios [rom] -s -S 으로 디버깅할 수 있다.

- Bios ROM은 실행 중 매핑과정을 거쳐 엔트리포인트를 찾아가므로, gdb로 동적 디버깅중, 메모리 덤프를 뜨면 ida로 분석하기 좋다. ROM파일은 이렇게 하지 않으면, ida의 xref가 제대로 작동하지 않는다.