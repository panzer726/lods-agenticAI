import requests
import json
session = requests.Session()
import time

while True:
    user_msg = input("YOU: ")
    t1 = time.perf_counter()
    resp = session.post("http://127.0.0.1:8000/message",json={"source":"terminal","content":user_msg})
    print(time.perf_counter()-t1)
    print(resp.json()["reply"])

