

# ​EasyPT	

## 0. BackGround

### IntelPT(Intel Processor-Trace) : 

> Intel® Processor Trace (Intel PT) is an extension of Intel® Architecture that captures information about software execution using dedicated hardware facilities that cause only minimal performance perturbation to the software being traced. This information is collected in data packets. The initial implementations of Intel PT offer control flow tracing, which generates a variety of packets to be processed by a software decoder. The packets include timing, program flow information (e.g. branch targets, branch taken/not taken indications) and program-induced mode related information (e.g. Intel TSX state transitions, CR3 changes). These packets may be buffered internally before being sent to the memory subsystem or other output mechanism available in the platform. Debug software can process the trace data and reconstruct the program flow. Later generations include additional trace sources, including software trace instrumentation using PTWRITE, and Power Event tracing.

인텔의 Processor Trace기술로, 프로세서가 수행한 연산들을 수집하고, Packet으로 저장하는 기술이다. 이 중 주목해야 할 것은 Branch(JMP, JNE 등)에 관한 로그를 수집한다는 것이다.

Intel의 공식 Document을 읽어보면, 수집하는 로그에 대한 자세한 정보를 찾아볼 수 있다.
https://software.intel.com/sites/default/files/managed/39/c5/325462-sdm-vol-1-2abcd-3abcd.pdf

INSN중에서 TNT8(Taken-NotTaken-Taken)은 JNE,JE,JZ 처럼 조건이 있는 분기문에서 JMP를 Taken했는지, Not Taken했는지를 표기한 로그이다. 

예를 들어, `TNT8 TTTTTT` 은 6번의 분기문에서 모두 JMP했다는 의미이다.

TNT를 기억해두자.



## 1. ELF Analyze

### a.PT

![1550123995289](img\1550123995289.png)

flag의 각 character에 대해 모든 아스키 문자와 비교하여 같은지 비교, 탈출을 반복함.
만약 각 character에 대한 반복문 반복횟수를 알 수 있다면, flag의 각 자리를 복구할 수 있을 것임.



### b.capture

![1550124201966](img\1550124201966.png)

기본적인 fork프로세스의 골격을 가짐

- pid = fork() > 0 : 부모 프로세스

- pid = fork() == 0 : 자식 프로세스

  > read) https://www.geeksforgeeks.org/fork-system-call/



pipe함수를 통해, 부모 자식프로세스간에 통신을 함

> read) https://www.geeksforgeeks.org/pipe-system-call/

![1550124412284](img\1550124412284.png)

parent는 processor-trace의 준비를 마치고, `write(pipedes[1],&v8,4)`을 통해 child 에 시그널을 보냄.
시그널을 받은 child는 `execve`함수를 호출하여, `argv[1]`에 해당하는 파일을 실행함.

`waitpid(pid,&stat_loc,0)`을 호출하여 child가 종료될것을 기다림.

child가 종료되면, `sub_400df8()`, `sub_40129c()`,`sub_40101c()`,`sub_4100b5()`를 호출하여, 
processor-trace를 멈추고, 수집한 정보를 기록함.

저장하는 파일명은 각각 `perf.header`,`perf.packet`,`perf.sideband` 인데, 이 문제에서 주목해야할 파일은 `perf.packet`이다.



## 2. Packet Analyze

Packet파일은 RAW TEXT파일이 아니다. 저장하는 format이 따로있고, 이를 decode해야 우리가 해석하기 쉬운 형태가 된다.

직접 decoder를 짜는 것은 번거로우므로, git을 뒤져보면, SimplePT(https://github.com/andikleen/simple-pt)라는 오픈소스 유틸을 찾을 수 있다.

가이드를 따라 make를 하고, `fastdecode`를 이용하면 해석하기 쉬운 형태의 로그를 얻을 수 있다.

![1550127530878](img\1550127530878.png)

모든 instruction이 다 수집되어 있는데, 대부분은 쓸모가 없다.

우리가 파악해야할 것은 `PT`에서 한 character당 반복문을 몇 번 반복했는가 이다. 

 `strlen(s)`을 Call하고 return하는 부분을 찾으면, 그 뒤의 tnt를 분석하면 될것이라고 판단할 수 있다.
(대부분의 로그는 프로세스 `init`, 함수 프롤로그, resolve 등에 관한 로그이므로 무시해도 된다.)

![1550128215046](img\1550128215046.png)

`strlen(s)`뒤의 IP는 0x4007cc이다.
따라서 `tip 0x4007cc`를 우선 찾는다. (*tip이라는 instruction은 return, jmp처럼 무조건적으로 pc가 jmp하는 부분을 기록한 것이다.)

![1550128152870](img\1550128152870.png)

0x52f1부터 많은 양의 `TNT8` instruction이 존재함을 알 수 있다. 

파이썬 스크립트를 작성하여 전부 파싱하고, 반복문의 분기 구조를 파악하여 반복횟수를 세는 스크립트를 작성하면, 문제를 풀 수 있을 것이다.



## 3. Solution

TNT파싱 스크립트는 잃어버림;

![1550128601190](img\1550128601190.png)

![1550128579790](img\1550128579790.png)

```python
file = open('tntdump.bin','rb')
data = file.read()

data=data.split()[2::3]
data=''.join(data)

state=0
res=''
for i in data:
	if state==0:
		cnt=0
		if i=='T':
			state=1
		if i=='N':
			break
	elif state==1:
		if i=='T':
			state=2
		if i=='N':
			state=0
	elif state==2:
		if i=='T':
			res+=chr(0x20+cnt)
			state=0
		if i=='N':
			state=1
			cnt+=1

print res
```

![1550128719377](img\1550128719377.png)

