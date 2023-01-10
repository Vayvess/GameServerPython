import json
import time
import socket
import sqlite3
import selectors
from proto import *


class Session:
    def __init__(self, conn):
        self.conn = conn
        self.usern = "anon"
        self.logged = False

    def send_req(self, req):
        try:
            data = json.dumps(req).encode("utf-8")
            self.conn.sendall(len(data).to_bytes(2, 'big') + data)
        except Exception as neterr:
            print(neterr, req)


class Server:
    def __init__(self):
        self.db = sqlite3.connect("database.db")
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setblocking(False)
        self.tcp_sock.bind(SVR_ADDR)
        self.tcp_sock.listen()

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.tcp_sock, selectors.EVENT_READ, None)

        # GAMESERVER
        # self.tick_rate = 1 / 64

    def handle_accept(self):
        print("new client !")
        conn, addr = self.tcp_sock.accept()
        conn.setblocking(False)
        sess = Session(conn)
        self.selector.register(conn, selectors.EVENT_READ, sess)

    def handle_disconnect(self, sess):
        print(f"{sess.usern} disconnected from the server !")
        self.selector.unregister(sess.conn)
        sess.conn.close()

    def req_login(self, sess: Session, req):
        if sess.logged:
            return
        usern, passw = req[TCP_LOGIN_USERN], req[TCP_LOGIN_PASSW]
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE usern=? AND passw=?", (usern, passw))
        res = cursor.fetchone()
        if res is None:
            sess.send_req({TCP_RTYPE: TCP_AUTHEN, TCP_STATUS: False})
        else:
            sess.send_req({TCP_RTYPE: TCP_AUTHEN, TCP_STATUS: True})
            sess.usern = usern
            sess.logged = True

    def handle_req(self, sess, req):
        rtype = req[TCP_RTYPE]
        if rtype == TCP_LOGIN:
            self.req_login(sess, req)

    def handle_event(self, sess):
        try:
            msglen = int.from_bytes(sess.conn.recv(2), 'big')
            data = sess.conn.recv(msglen)
        except ConnectionResetError:
            self.handle_disconnect(sess)
        else:
            if len(data) > 0:
                try:
                    data = json.loads(data.decode("utf-8"))
                except json.decoder.JSONDecodeError as jserr:
                    print(jserr, data)
                else:
                    self.handle_req(sess, data)
            else:
                self.handle_disconnect(sess)

    def handle_tcp(self, timeout=None):
        events = self.selector.select(timeout)
        for key, mask in events:
            if key.data is None:
                self.handle_accept()
            else:
                self.handle_event(key.data)

    def start(self):
        while 1:
            self.handle_tcp()

    def stop(self):
        self.selector.close()
        self.tcp_sock.close()
        self.db.close()


if __name__ == '__main__':
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("server shut down !")
