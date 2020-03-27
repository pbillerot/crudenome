#/usr/bin/python3
# coding: utf-8

import socket

hote = "localhost"
port = 7777

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((hote, port))
print( "Connection on {}".format(port))

socket.send(u"Hey my name is Olivier!")

print ("Close")
socket.close()