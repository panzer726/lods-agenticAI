import requests
import json

while True:
    user_msg = input("YOU: ")

    resp = requests.post("http://localhost:8000/message",json={"source":"terminal","content":user_msg})

    print(resp.json()["reply"])

