import json

u = {
    1: "Raphaelle"
}

v = json.dumps(u).encode("utf-8")
print(v, type(v))

w = v.decode("utf-8")
print(w, type(w))

x = json.loads(w)
print(x, type(x))
print(x == u)
