from groq import Groq
import json
from memory.mem_handler import retrieve_memory
import time
from dotenv import load_dotenv
load_dotenv(override=True)
from tool_functions import run_shell, view_reminders, manage_reminders, web_search, control_light, save_memory

from LLM import call_model
model = "openai/gpt-oss-20b"
msgs = []

with open("system_prompts/main_prompt.txt", encoding="utf-8") as f:
    prompt = f.read()

with open("tools.json","r") as f:
    tool_list = json.load(f)
#=============================================================================#
#=============================================================================#
def append_msgs(role, content, tool_id=None, tool_name=None):
    msg = {"role": role, "content": content}
    
    if tool_id is not None:
        msg["tool_call_id"] = tool_id

    if tool_name is not None:
        msg["name"] = tool_name

    msgs.append(msg)
#=============================================================================#
#=============================================================================#
def handle_message(user_msg):
    global msgs

    if user_msg=="!reset":
        msgs = []
        return "───────── New chat ─────────"

    append_msgs("user",user_msg)
    msgs = msgs[-9:]

    memories = retrieve_memory(user_msg)
    memories = "\n".join( [mem["content"]+"|"+mem["date_sent"] for mem in memories] )
    formatted_prompt = prompt.replace('$memories', memories).replace('$time', time.strftime("%b %d %Y %H:%M"))

    output = call_model(msgs, tool_list, formatted_prompt)

    while output.tool_calls:
        msgs.append(output)

        for tool in output.tool_calls:
            run_tools(tool.function, tool.id, json.loads(tool.function.arguments))

        output = call_model(msgs,tool_list,prompt)
        
    if output.reasoning: print("THINKING: ",output.reasoning)

    append_msgs("assistant",output.content)
    return output.content
#=============================================================================#
#=============================================================================#
def run_tools(tool, id, args):
    match tool.name:

        case "run_shell":
            result = run_shell(args["command"])

        case "view_reminders":
            result = view_reminders()

        case "manage_reminder":
            result = manage_reminders(args)
        
        case "web_search":
            result = web_search(args["query"])

        case "control_light":
            result = control_light(args)

        case "save_infos":
            result = save_memory(args["infos"])

        case _:
            return append_msgs("tool", f"Unknown tool: {tool.name}", id, tool.name)

    print("TOOL USED:",tool.name, args)
    append_msgs("tool", result, id, tool.name)
#=============================================================================#
#=============================================================================#
