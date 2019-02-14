import midi
from base64 import b64decode
pattern=midi.read_midifile("flag.mid")

res=''
for i in range(len(pattern[0])/2):
    res+=(chr(pattern[0][2*i].pitch+pattern[0][2*i+1].pitch))

print b64decode(res)
