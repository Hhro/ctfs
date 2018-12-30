#-*- coding : utf-8
import csv
from PIL import Image

f=open('blink.csv','r')
rdr=csv.reader(f)

for i in range(13):
	next(rdr)

col=0
row_data=[[0 for _ in range(128)] for _ in range(2)]
latch=[[0 for _ in range(128)] for _ in range(2)]
prev=[0 for _ in range(15)]
parsed=[[] for i in range(64)]

while 1:
	try:
		line=next(rdr)
		OE,lat,clk,E,D,C,B,A,_,_,G2,G1,R2,R1=line[1:12]+[int(p) for p in line[12:16]]

		row_data[0][col]=int(R1 and G1)
		row_data[1][col]=int(R2 and G2)

		if clk=='0' and prev[3]=='1': # clk changes 1 to 0
			col+=1
			col%=128

		if lat=='0' and prev[2]=='1': # lat changes 1 to 0
			latch=row_data

		if OE=='0' and prev[1]=='1': # OE changes 1 to 0
			row=int(E+D+C+B+A,2)
			parsed[row]=latch[0][-15:]+latch[0][:-15]
			parsed[row+32]=latch[1][-15:]+latch[1][:-15]

		prev=line

	except:
		f.close()
		res=[]
		for i in parsed:
			for j in i:
				res.append((255*j,255*j,0*j))

		image=Image.new('RGB',(128,64))
		image.putdata(res)
		image.save('flag.png')
		break