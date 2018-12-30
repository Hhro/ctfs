# -*- coding: utf-8 -*-

xml=['<?xml version="1.0" encoding="UTF-8"?>\n']

'''
     불고기 : copy
     paella : push X
     宫保鸡丁: log
     rösti : pop X, pop Y, push X+Y
     Борщ : found
     दाल :solve
     ﺢُﻤُّﺻ : pop X, pop Y, pusht X/Y γύρος : filtering
     stroopwafels : pop X pop Y, push Y>X
     לאַטקעס) : pop X, pop Y, push X-Y
     '''

def sub():
    xml.append('<plate><לאַטקעס></לאַטקעס></plate>')

def init():
    xml.append('<meal><course>')

def push(X):
    xml.append('<plate><paella>'+str(X)+'</paella></plate>')

def copy():
    xml.append('<plate><불고기></불고기></plate>')

def cmp():
    xml.append('<plate><ラーメン></ラーメン></plate>')

def found():
    xml.append('<plate><Борщ></Борщ></plate>')

def solve(): 
    xml.append('<plate><दाल></दाल></plate>')

def filtering():
      xml.append('<plate><γύρος></γύρος></plate>')

def div():
      xml.append('<plate><حُمُّص></حُمُّص></plate>')

def add():
      xml.append('<plate><rösti></rösti></plate>') 
def log():
    xml.append('<plate><宫保鸡丁></宫保鸡丁></plate>')

def jmp():
    xml.append('<plate><æblegrød></æblegrød></plate>')

def pop_cmp():
    xml.append('<plate><stroopwafels></stroopwafels></plate>')

def fini():
    xml.append('</course>')

def make_sol():
    init()
    log()
    found()
    found()
    solve()
    push(4294967296)
    push(0)
    push(1)
    push(1)
    jmp()
    xml.append('</course>')
    xml.append('<course>')

    push(0)
    copy()
    push(2)
    copy()
    sub()
    push(1)
    pop_cmp()
    push(0)
    copy()
    push(1)
    sub()
    jmp()
    
    push(2)
    push(2)
    copy()
    push(2)
    copy()
    add()
    div()
    push(0)
    copy()
    cmp()
    push(1)
    add()
    filtering()
    push(0)
    copy()
    push(2)
    copy()
    pop_cmp()
    push(1)
    add()
    push(1)
    jmp()
    fini()
    xml.append('<course>')
    
    push(1)
    copy()
    push(1)
    copy()
    sub()
    push(1)
    pop_cmp()
    push(0)
    copy()
    push(1)
    sub()
    jmp()

    push(2)
    push(2)
    copy()
    push(2)
    copy()
    add()
    div()
    push(0)
    copy()
    cmp()
    push(2)
    sub()
    filtering()
    push(0)
    copy()
    push(2)
    copy()
    pop_cmp()
    push(1)
    add()
    push(1)
    jmp()
    fini()
    xml.append('</meal>')

make_sol()
file=open('solve.xml','wb')
file.write('\n'.join(xml))
file.close()
