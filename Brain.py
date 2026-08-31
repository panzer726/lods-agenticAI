from groq import Groq
import json
from memory import mem_saver
from memory import mem_handler
import threading
import time
from dotenv import load_dotenv
import os
load_dotenv(override=True)
from types import SimpleNamespace
from tool_functions import run_shell, view_reminders, manage_reminders, web_search, control_light

with open("system_prompts/main_prompt.txt",encoding="utf-8") as f:
    prompt = f.read()

with open("tools.json","r") as f:
    tools = json.load(f)

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
            print("[created a reminder]")
            result = manage_reminders(args) # needs fix
            append_msgs("tool", result, id, tool.name)
            append_msgs("tool", "created/finished a reminder", id, tool.name)
            return SimpleNamespace( **{"content": result, "tool_calls": []} ) #kunyari galing sa llm yung dict
                                            # change result to 'success' since redundant sya
        case "web_search":
            print("[searching the web]")
            search_result = web_search(args["query"])
            append_msgs("tool", search_result, id, tool.name)
            print(msgs,"HAHAHA", args["query"])

        case "control_light":
            print("[modifying light]")
            result = control_light(args)
            append_msgs("tool", result, id, tool.name)

            
        case _:
            append_msgs("tool", f"Unknown tool: {tool.name}", id, tool.name)

    return call_model()
