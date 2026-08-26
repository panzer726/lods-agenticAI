from llama_cpp import Llama
import json
from json_repair import repair_json
import time 
import re
import sqlite3
from datetime import date
import os
import subprocess
import sys

from memory import mem_handler

debug_mode = False
 

# Load the local model directly into RAM
#print("Starting AI...\n")
llm = Llama(
    model_path="models/llama3.2-3b-q4-k-m.gguf",
    n_ctx=2048,
    verbose=False,
    n_batch=2048
)


personality = """
PERSONALITY:
You are Molly, created by Jear.
- Witty, concise, and direct with a sense of humor.
- Proactively flag potential issues and require confirmation before executing dangerous commands.
- Ask for clarification on vague commands rather than making assumptions.
- Use time as context quietly without stating it explicitly unless asked.
- Abilities: save memory, execute Python scripts.
"""

#binawasan ko na prompt about json instrunction and nagrely nalang ako sa json_repair
system_prompt1 = '''
Respond only with a raw JSON array. Each object starts and end with curly brackets and the whole response must start and end with square brackets.

SCHEMA:
[ { "type": "chat", "content": "<message to user>" }, { "type": "save_memory", "content": "<short, specific fact to save> | <context>" }, { "type": "run_task", "code": "<single line python code>", "external_packages": "<third-party libraries>" } ]

RULES:
1. Always start the array with exactly ONE {"type": "chat"} object (1–3 sentences max).
2. Look at MEMORIES. If the user's statement is already recorded there, DO NOT output a "save_memory" object. Return ONLY the "chat" object.
3. Append "run_task" ONLY when system execution is strictly required. Escape internal quotes in code.
4. Append "save_memory" ONLY when user mesage is fact/preference/opinion/rule/command
5. Do not put built-in package in external_packages i.e. os and subprocess.

#EXAMPLES:
MEMORIES
- None
"Hi" → [ {"type": "chat", "content": "Hey! What are we breaking today?"} ]

MEMORIES
- None
"i just bought silver metal covers for them" → [ {"type": "chat", "content": "Awesome sir! Silver covers are classics for SGs. Did you solder the covers to ground?"}, {"type": "save_memory", "content": "User just bought silver metal covers for his SG Guitar. | Gibson guitar, band, music, guitar hardware"} ]

MEMORIES
- User likes to play valorant and his main character is phoenix (aug 20, 2024 10:54)
"I love playing Valorant" → [ {"type": "chat", "content": "Still rocking Phoenix, or are you switching it up today?"} ]

MEMORIES
- None
"List files in current directory" → [ {"type": "chat", "content": "Pulling up your directory contents now." }, { "type": "run_task", "code": "import os; print(os.listdir('.'))", "external_packages": "None"} ]
'''


tries = 0
def chat(history,stream=True):
    response = llm.create_chat_completion(history,stream=stream, max_tokens=300,temperature=0.3)

    message = ""
    if stream:
        for chunk in response:
            delta = chunk["choices"][0]["delta"]
            if delta.get("content"):
                print(delta["content"],flush=True,end="")
                message += delta["content"]
    else:
        message = response["choices"][0]["message"]["content"]

    try:    
        message = json.loads(repair_json(message))
        return message if isinstance(message,list) else [message]
    
    except: 
        print(f"\n\n[kamali nanaman sa json yung ai]\n{message}\n\n")
        history[len(history)-1]["content"] += "\n(make json valid. add commas between objects, "
        "make sure each objects starts and ends with curly brackets, "
        "whole response should starts and ends with square brackets. no apostrophe, no json markup.)"

        return chat(history, stream) if tries < 2 else 0


chat_history = []
def append_history(role, content):
    chat_history.append({
        "role": role,
        "content": str(content)
        })


def run_task(info):
    try:
        if info["external_packages"] != "None":
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + [pkg.strip() for pkg in info.get("external_packages").split(",")] )

        with open("task_runner/scratch.py", "w") as f:
            f.write(info["code"])
            result = subprocess.run(
            ["python", "task_runner/scratch.py"],
            capture_output=True, text=True, timeout=10
            )
        return result.stdout if result.stdout else "Error"
    except Exception as e:
        return e




while True:
    datenow = time.strftime("%b %d %Y %H:%M")
    user_msg = input("\nYOU: ")
    append_history("user", user_msg)

    if user_msg == "quit":
        os.system("cls")
        break

    prompt = f'''
        current date: {datenow}

        {mem_handler.retrieve_memory(user_msg)}
        (Note: Disregard irrelevant information)

        OUTPUT FORMAT   :
        {system_prompt1}
    '''

    #print("\nMemories:\n",mem_handler.retrieve_memory(user_msg),"\n")

    infos = chat( [{"role":"system", "content":prompt}] + chat_history)
    append_history("assistant", infos)
    #[#print("MOLLY: ",info["content"]) for info in infos if info.get("type") == "chat"]

    for info in infos:
        match info["type"]:

            case "run_task":
                result = run_task(info)

                append_history("user", f"summarize. here is the taskrun result: {result} (Note: you cannot do task_run again.)" )
                chat_history.append( {"role": "user", "content":f"summarize. here is the taskrun result: {result} (Note: you cannot do task_run again.)"} )
                infos = chat( [{"role":"system", "content":prompt}] + chat_history)
                #[#print("MOLLY: ",info["content"]) for info in infos if info.get("type") == "chat"]
                #print(infos)
                for i in infos:
                    if i["type"] == "save_memory":
                        mem_handler.save_memory(i.get("content"),datenow)
                        ##print([f"memory saved: '{i.get("content")}'"])

                append_history("assistant", infos)


            case "save_memory":
                mem_handler.save_memory(info["content"],datenow)
                ##print([f"memory saved: '{info["content"]}'"])  

    if len(chat_history)>=7:
        chat_history.pop(0)
        chat_history.pop(0)
        
    print("\n", json.dumps(chat_history,indent=4).replace("\r",""),"\n")


