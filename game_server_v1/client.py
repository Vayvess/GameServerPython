import time
import json
import socket
from proto import *

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect(SVR_ADDR)

req = {
    TCP_RTYPE: TCP_LOGIN,
    TCP_LOGIN_USERN: "test",
    TCP_LOGIN_PASSW: "testing"
}

data = json.dumps(req).encode("utf-8")
tcp_sock.sendall(len(data).to_bytes(2, 'big') + data)

msglen = int.from_bytes(tcp_sock.recv(2), 'big')
received = tcp_sock.recv(msglen)

received = json.loads(received.decode("utf-8"))
print(received)

tcp_sock.close()
