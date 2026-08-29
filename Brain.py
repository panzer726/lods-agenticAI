from groq import Groq
import subprocess
import json
from memory import mem_saver
from memory import mem_handler
import threading
import time
from dotenv import load_dotenv
import os
load_dotenv(override=True)
from types import SimpleNamespace
import sqlite3

with open("system_prompts/main_prompt.txt",encoding="utf-8") as f:
    prompt = f.read()

model = "openai/gpt-oss-20b"
client = Groq(api_key=os.getenv('groq_api_key'))
convo = []
msgs = [ {"role":"system","content":prompt}]

def call_model():
    try:
        output = client.chat.completions.create(
            model=model,
            messages=msgs,
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            tools=tools,
            reasoning_effort="low"
        )

        return output.choices[0].message
    
    except Exception as e:
        print(f"[ERROR calling model] {e}")

def append_msgs(role, content, tool_id=None, tool_name=None):
    msg = {"role": role, "content": content}
    
    if tool_id is not None:
        msg["tool_call_id"] = tool_id

    if tool_name is not None:
        msg["name"] = tool_name

    msgs.append(msg)
    convo.append(f"{role}: {content}")

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run Windows shell to interact with operating system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Windows CMD command only."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_reminder",
            "description": "create or finish a reminder to user",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "finish"]},
                    "trigger_time": {"type": "integer", "description": "How many seconds from now until the reminder should trigger."},
                    "content": {"type": "string", "description": "A short description of the reminder"},
                    "reply_to_user": {"type": "string", "description": "a short affirmation"}
                },
                "required": ["reply_to_user", "action", "trigger_time", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_reminders",
            "description": "check incoming reminders",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

def handle_message(user_msg):
    global msgs

    if user_msg=="/reset":
        msgs = [{"role":"system","content":prompt}]
        return "conversation resetted!"

    append_msgs("user",user_msg)
    msgs[0]["content"] = prompt + "TIME: " + time.strftime("%I:%M %p, %b %d %Y")
    msgs = [msgs[0], *msgs[1:][-7:]]

    #threading.Thread(target=mem_saver.save,args=(convo[-6:],),daemon=True,).start()
    output = call_model()

    if output is None:
        return("ERROR: OUTPUT IS NONE")

    while output.tool_calls:
        if output is None:
            print("erororroro")
            break
        tool = output.tool_calls[0]
        
        msgs.append(output)
        output = run_tools(tool.function, tool.id, json.loads(tool.function.arguments))

    append_msgs("assistant",output.content)
    return(output.content)

def run_shell(command):
    result = subprocess.run(command,shell=True,capture_output=True,text=True,timeout=5)
    return result.stdout + result.stderr

def view_reminders():
    conn = sqlite3.connect("memory/reminders.db",timeout=5)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM reminders").fetchall()
    output = ""
    for row in rows:
        local_time = time.localtime(row['trigger_time'])
        output += f"{row['content']} in {time.strftime("%I:%M %p, %b %d %Y",local_time)} \n"

    conn.close()

    output = "No reminders set" if output == "" else output
    return output

def manage_reminders(args):
    conn = sqlite3.connect("memory/reminders.db",timeout=5)
    action = args["action"]
    match action:

        case "create":
             conn.execute("""
                 INSERT INTO reminders (content, trigger_time)
                 VALUES (?, ?)
             """,
                (args["content"], int(time.time()) + args["trigger_time"])
            )
             conn.commit()

        case "finish":
            conn.execute("DELETE FROM reminders WHERE content LIKE ?", (f"%{args["content"]}%",))
            conn.commit()

    conn.close()
    return args["reply_to_user"]


def run_tools(tool, id, args):
    match tool.name:

        case "run_shell":
            print("[running shell command",args["command"],"]")
            shell_result = run_shell(args["command"])
            append_msgs("tool", shell_result, tool_id=id, tool_name=tool.name)

        case "view_reminders":
            print("[checking reminders list]")
            reminder_list = view_reminders()
            append_msgs("tool", reminder_list, id, tool.name)

        case "manage_reminder":
            manage_reminders(args)
            print("[created a reminder]")
            append_msgs("tool", "created/finished a reminder", id, tool.name)
            return SimpleNamespace( **{"content": args["reply_to_user"], "tool_calls": []} ) #kunyari galing sa llm yung dict
            
        case _:
            append_msgs("tool", f"Unknown tool: {tool.name}", id, tool.name)

    return call_model()
