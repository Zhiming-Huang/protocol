#!/usr/bin/env python3

import struct

a = 1
b = 2
c = 3
d = 'abcd'
s = struct.pack('!BBB',a,b,c)

y = b''
print(s)

e = d.encode()

print(e)

print(s + e)

print(y + s + e)