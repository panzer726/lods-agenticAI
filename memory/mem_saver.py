from llama_cpp import Llama
import time 
from memory import mem_handler
from fastembed import TextEmbedding

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

extractor_model = "Alibaba/qwen3.5-2b-Q4_K_M.gguf"
filter_model = "Alibaba/qwen3.5-2b-Q4_K_M.gguf"

fixed_llm_config = {
    "verbose": False,
    "flash_attn": True,
    "n_threads": 4,
    "n_gpu_layers": 0,
    "n_batch": 2048,
    "offload_kqv": False
}

extractor = Llama(
    model_path = f"../models/{extractor_model}/"
                 f"{extractor_model.split("/")[1]}",
    n_ctx = 4096,
    **fixed_llm_config
)
memory_filter = Llama(
    model_path = f"../models/{extractor_model}/"
                 f"{extractor_model.split("/")[1]}",
    n_ctx = 1024,
    **fixed_llm_config
)

with open("system_prompts/intent_extractor_prompt.txt",encoding="utf-8") as f:
    intent_extractor_prompt = f.read()

with open("system_prompts/memory_filter_prompt.txt",encoding="utf-8") as f:
    memory_filter_prompt = f.read()

def save(history):
    history = (
        f"[BACKGROUND CONTEXT]\n"
        f"{'\n'.join(history[:-1])}\n"
        f"[TARGET MESSAGE]\n"
        f"{history[-1]}"
    )
    
    extracted = extractor.create_chat_completion(
        [{"role":"system", "content":intent_extractor_prompt},
        {"role": "user", "content": history}],
        stream=True
    )

    ttft = None
    start = time.perf_counter()
    message = ""
    for chunk in extracted:
        if not ttft:
            ttft = time.perf_counter() - start
        print(chunk,"HAHAHA")
        delta = chunk["choices"][0]["delta"]
        if delta.get("content"):
            message += delta["content"]

    extracted = message.replace("<think>","").replace("</think>","").strip()
    filter_memory(extracted)


def filter_memory(to_filter):                                  #top_k and similarity threshold
    existing_memories = mem_handler.retrieve_memory(to_filter, 3, 0.65)

    for info in to_filter.split("\n"):
        info = info.strip()

        if 'NONE' in info:
            return print("\n[no memory extracted]")

        banned = ("User asked", "User is asking", "User wants to know", "Assistant:", "User:")
        if info.startswith(banned):
            continue
        
        if not existing_memories:
            print(f"[saved agad: {info}]")
            mem_handler.save_memory( info, time.strftime("%b %d %Y %H:%M") )
            continue
        
        filtered = memory_filter.create_chat_completion(
            [
                {"role":"system", "content": memory_filter_prompt},
                {"role":"user", "content":f"NEW MEMORY: {info}\n\nEXISTING MEMORIES:\n{existing_memories}"}
            ]
        )
        ["choices"][0]["message"]["content"]
        
        print(f"[{filtered}: {info}]")

        if filtered == "NEW":
            mem_handler.save_memory(info, time.strftime("%b %d %Y %H:%M"))
