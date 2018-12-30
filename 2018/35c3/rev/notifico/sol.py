# -*- coding: utf-8 -*-
import os
import copy
import re
from stat import S_ISREG
from hashlib import sha256
from Crypto.Cipher import AES

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
                else: link.append(os.readlink('/'.join([root,dir,file]))[3:])
            graph[key]=link 

hash_table={}
test=graph.keys()
test.sort()
for idx,key in enumerate(test):
    hash_table.update({idx:key})
    hash_table.update({key:idx}) 
for key in graph.keys():
    new_link=[hash_table[x] for x in graph[key]]
    new_link.sort()
    graph[hash_table[key]]=new_link
    del(graph[key])

dominate={}
for key in graph.keys():
    if len(graph[key]) not in dominate.keys():
        dominate.update({len(graph[key]):[]})
    dominate[len(graph[key])].append(key)

center = dominate[56][0]

candid=[]
for x in dominate[42]:
    if x in graph[center]:
        candid.append(x)

edge=[]
n_edge=[]
for c in candid:
    cnt=0
    for n in dominate[42]:
        if n in graph[c]:
            cnt+=1
    if cnt==29:
        edge.append(c)
    else:
        n_edge.append(c)

board=[[0 for _ in range(3)] for _ in range(3)]
base=edge[0]
board[0][0]=base
board[1][1]=center
del(candid[candid.index(base)])

addr=[(0,0),(1,2),(2,0),(0,1),(2,2),(1,0),(0,2),(2,1)]

for i in range(1,8):
    row=addr[i][0]
    col=addr[i][1]
    pre_row=addr[i-1][0]
    pre_col=addr[i-1][1]

    for c in candid:
        if c not in graph[board[pre_row][pre_col]]:
            board[row][col]=c
            del(candid[candid.index(c)])
            break

row_candid=[[0 for _ in range(12)] for _ in range(3)]
for idx,row in enumerate(board):
    x=graph[row[0]]
    y=graph[row[1]]
    z=graph[row[2]]
    common=[]
    for p in x:
        if p in y and p in z and p != center:
            common.append(p)
    row_candid[idx]=common
    

col_candid=[[0 for _ in range(12)] for _ in range(3)]
for i in range(3):
    x=graph[board[0][i]]
    y=graph[board[1][i]]
    z=graph[board[2][i]]
    common=[]
    for p in x:
        if p in y and p in z and p!= center:
            common.append(p)
    col_candid[i]=common


big_board=[[-1 for _ in range(15)] for _ in range(15)]
for i in range(3):
    for j in range(3):
        big_board[i*7][j*7]=board[i][j]

for row_elem in row_candid[0]:
    for col_elem in col_candid[0]:
        if col_elem in graph[row_elem]:
            cnt=0
            for p in graph[row_elem]:
                if p in graph[col_elem]:
                    cnt+=1
            if cnt==9:
                continue
            elif cnt>9:
                big_board[0][cnt-1]=row_elem
                big_board[cnt-1][0]=col_elem
            else:
                big_board[0][cnt-3]=row_elem
                big_board[cnt-3][0]=col_elem

for row_elem in row_candid[2]:
    for col_elem in col_candid[2]:
        if col_elem in graph[row_elem]:
            cnt=0
            for p in graph[row_elem]:
                if p in graph[col_elem]:
                    cnt+=1
            if cnt==9:
                continue
            elif cnt>9:
                big_board[14][14-cnt+1]=row_elem
                big_board[14-cnt+1][14]=col_elem
            else:
                big_board[14][14-cnt+3]=row_elem
                big_board[14-cnt+3][14]=col_elem

for i in range(1,14):
    for j in range(1,14):
        if i==6 or i==8 or j==6 or j==8:
            continue
        if i==7 or j==7:
            continue
        top=big_board[0][i]
        bot=big_board[14][i]
        left=big_board[j][0]
        right=big_board[j][14]
        
        for x in graph[top]:
            if x in graph[bot] and x in graph[left] and x in graph[right]:
                big_board[j][i]=x

for i in range(1,14):
    if i==6 or i==8 or i==7:
        continue
    top=big_board[0][7]
    bot=big_board[14][7]
    left=big_board[i][1]
    right=big_board[i][14]
    top2=big_board[7][0]
    bot2=big_board[7][14]
    left2=big_board[1][i]
    right2=big_board[14][i]
    
    for x in graph[top]:
        if x in graph[bot] and x in graph[left] and x in graph[right]:
            big_board[i][7]=x

    for x in graph[top2]:
        if x in graph[bot2] and x in graph[left2] and x in graph[right2]:
            big_board[7][i]=x



def diagonal(i,j):
    lu=big_board[i-1][j-1]
    ld=big_board[i+1][j-1]
    ru=big_board[i-1][j+1]
    rd=big_board[i+1][j+1]

    for x in graph[lu]:
        if x in graph[ld] and x in graph[ru] and x in graph[rd]:
            big_board[i][j]=x

for i in range(1,14):
    if i==5 or i==7 or i==9:
        continue
    diagonal(i,6)
    diagonal(6,i)
    diagonal(i,8)
    diagonal(8,i)



def rect(i,j):
    top=big_board[i-1][j]
    bot=big_board[i+1][j]
    left=big_board[i][j-1]
    right=big_board[i][j+1]
   
    for x in graph[top]:
        if x in graph[bot] and x in graph[left] and x in graph[right]:
            big_board[i][j]=x

for i in range(14):
    for j in range(14):
        try:
            rect(i,j)
        except:
            continue
        
def penta(x,y,z,u,v):
    for p in graph[x]:
        if p in graph[y] and p in graph[z] and p in graph[u] and p in graph[v]:
            return p

big_board[0][6]=penta(big_board[0][5],big_board[0][7],big_board[1][6],big_board[1][5],big_board[1][7])
big_board[0][8]=penta(big_board[0][7],big_board[0][9],big_board[1][8],big_board[1][7],big_board[1][9])
big_board[14][6]=penta(big_board[14][5],big_board[14][7],big_board[13][6],big_board[13][5],big_board[13][7])
big_board[14][8]=penta(big_board[14][7],big_board[14][9],big_board[13][7],big_board[13][8],big_board[13][9])
big_board[6][0]=penta(big_board[5][0],big_board[7][0],big_board[6][1],big_board[5][1],big_board[7][1])
big_board[6][14]=penta(big_board[5][14],big_board[7][14],big_board[6][13],big_board[5][13],big_board[7][13])
big_board[8][0]=penta(big_board[7][0],big_board[9][0],big_board[8][1],big_board[7][1],big_board[9][1])
big_board[8][14]=penta(big_board[7][14],big_board[9][14],big_board[8][13],big_board[7][13],big_board[9][13])

for row in big_board:
    print (row)

seq=[]
for i in range(225):
    for j in range(15):
        for k in range(15):
            if big_board[j][k]==i:
                seq.append([j,k])

def get_board(size):
    """Returns an n by n board"""
    board = [0]*size
    for ix in range(size):
        board[ix] = [0]*size
    return board

def print_solutions(solution):
    """Prints all the solutions in user friendly way"""
    for row in solution:
        print(row)
    print()
            
def is_safe(board, row, col, size):
    """Check if it's safe to place a queen at board[x][y]"""

    #check row on left side
    for iy in range(col):
        if board[row][iy] == 1:
            return False
    
    ix, iy = row, col
    while ix >= 0 and iy >= 0:
        if board[ix][iy] == 1:
            return False
        ix-=1
        iy-=1
    
    jx, jy = row,col
    while jx < size and jy >= 0:
        if board[jx][jy] == 1:
            return False
        jx+=1
        jy-=1
    
    return True

prog=0

def solve(board, col, size):
    """Use backtracking to find all solutions"""
    #base case
    if col >= size:
        return
    
    for i in range(size):
        if is_safe(board, i, col, size):
            board[i][col] = 1
            if col == size-1:
                check(board)
                board[i][col] = 0
                return
            solve(board, col+1, size)
            #backtrack
            board[i][col] = 0

enc_flag='\x99|8\x80oh\xf57\xd4\x81\xa5\x12\x92\xde\xf5y\xbc\xc0y\rG\xa8#l\xb6\xa1/\xfeE\xc5\x7f\x85\x9a\x82\x0b\x02Y{\xd9/\x92X>p\\\xb7H\xb1{\xcf\x8b/r=\x87-#\xae\x95\xb6\xd1\r\x03\x13'

def check(board):
    global prog
    prog+=1
    if prog%10000==0:
        print 'progress : {}'.format(prog)

    res=''
    for i in seq:
        if board[i[0]][i[1]]==1:
            res+='700'
        else:
            res+='400'

    flag=AES.new(sha256(res.encode()).digest(),AES.MODE_ECB).decrypt(enc_flag)
    try:
        if '35C3' in flag.decode():
            print_solutions(board)
            print("Looks good, here is your output: {}".format(flag))
    except:
	return

size = 15
board = get_board(size)
solve(board, 0, size)
print "Something Wrong..."
