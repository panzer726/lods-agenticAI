from llama_cpp import Llama
import time 
import os
import threading
from memory import mem_handler
from memory import mem_saver

llm = Llama(
    model_path="models/Alibaba/qwen3-4B-Instruct-2507-Q4_K_M.gguf/qwen3-4B-Instruct-2507-Q4_K_M.gguf",
      n_ctx=2048,
      verbose=False,
      flash_attn=True,
      n_threads=4,
      n_gpu_layers=0,
      n_batch=512,
      offload_kqv=False
)

def chat(history,stream=True):
    ft = False
    t1 = time.perf_counter()
    response = llm.create_chat_completion(history,stream=stream, max_tokens=1024,temperature=1,repeat_penalty=1,top_p=0.95,min_p=0.05)
    message = ""
    for chunk in response:
        if not ft:
            ft = True
            print("TTFT:",time.perf_counter()-t1,"ms")
            print("LODS: ",flush=True,end="")
        delta = chunk["choices"][0]["delta"]
        if delta.get("content"):
            print(delta["content"],flush=True,end="")
            message += delta["content"]

    return message


chat_history = []
conversation = ["","","",""]
def append_history(role, content):
    chat_history.append({
        "role": role.lower(),
        "content": str(content)
        })

    conversation.append(f"{role}: {content}")


while True:

    datenow = time.strftime("%b %d %Y %I:%M %p")
    user_msg = input("\n")
    append_history("User", user_msg)

    if user_msg == "quit":
        os.system("cls")
        break

    memories = mem_handler.retrieve_memory(user_msg,score_val=0.4,top_k=5)

    prompt = f"""

- Limit response to 1-3 sentences.

MEMORIES(ignore if irrelevant):
{memories}
"""
    

    #print("\nMEMORIES:\n",mem_handler.retrieve_memory(user_msg,score_val=0.7,top_k=5),"\n")

    infos = chat( [{"role":"system", "content":prompt}] + chat_history)
    #print("MOLLY:",infos)

    conversation = conversation[-4:]  # magiging last 4 items nalang
    threading.Thread(target=mem_saver.save,args=(conversation,)).start()
    append_history("Assistant", infos)

    if len(chat_history) > 14:
        chat_history = chat_history[-7:]

        


