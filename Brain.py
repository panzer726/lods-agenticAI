from groq import Groq
import subprocess
import json
from memory import mem_saver
from memory import mem_handler
import threading
from dotenv import load_dotenv
import os
load_dotenv()

with open("system_prompts/main_prompt.txt",encoding="utf-8") as f:
    prompt = f.read()

model = "qwen/qwen3.8-27b"
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
            reasoning_effort="none"
        )

        return output.choices[0].message
    
    except Exception as e:
        print(f"[ERROR calling model] {e}")

def append_msgs(role,content,tool_id=None):
    msgs.append( {"role": role, "content": content} )
    if tool_id is not None:
        msgs[-1]["tool_call_id"] = tool_id

    convo.append(f"{role}: {content}")

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Run Python code for general purpose. Always print results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "a very short python code to execute. Always print results."}
                },
                "required": ["code"]
            }
        }
    },
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
    }
]

def handle_message(user_msg):
    append_msgs("user",user_msg)
    global msgs
    msgs = [msgs[0], *msgs[1:][-7:]]

    #threading.Thread(target=mem_saver.save,args=(convo[-6:],),daemon=True,).start()
    output = call_model()

    if output is None:
        return("ERROR: OUTPUT IS NONE")

    while output.tool_calls:
        tool = output.tool_calls[0]
        msgs.append(output)
        output = run_tools(tool.function, tool.id, json.loads(tool.function.arguments))
        if output is None:
            print("erororroro")
            break

    append_msgs("assistant",output.content)
    return(output.content)

def run_shell(command):
    result = subprocess.run(command,shell=True,capture_output=True,text=True,)
    return result.stdout + result.stderr

def run_python(code):
    result = subprocess.run(code,shell=True,capture_output=True,text=True,)
    return result.stdout + result.stderr

def run_tools(tool, id, args):
    match tool.name:

        case "run_python":
            print("[running python]", args["code"])
            result = run_python(args["code"])
            append_msgs("tool", result, id)

        case "run_shell":
            print("[running shell command",args["command"],"]")
            shell_result = run_shell(args["command"])
            append_msgs("tool", shell_result, id)

        case _:
            append_msgs("tool", f"Unknown tool: {tool.name}", id)

    return call_model()
