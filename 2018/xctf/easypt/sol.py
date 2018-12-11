file = open('tntdump','rb')
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

