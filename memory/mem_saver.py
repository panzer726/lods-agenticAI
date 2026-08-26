from llama_cpp import Llama
import time 
from memory import mem_handler
from fastembed import TextEmbedding

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

extractor = Llama(
    model_path="models/Alibaba/qwen3.5-2b-Q4_K_M.gguf/qwen3.5-2b-Q4_K_M.gguf",
        n_ctx=4096,
        verbose=False,
        flash_attn=True,
        n_threads=4,
        n_gpu_layers=0,
        n_batch=2048,
        offload_kqv=False   
)

filter = Llama(
    model_path="models/Alibaba/qwen2.5-0.5B-Instruct-Q4_K_M.gguf/qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
      n_ctx=1024,
      verbose=False,
      flash_attn=True,
      n_threads=4,
      n_gpu_layers=0,
      n_batch=2048,
      offload_kqv=False,
)

promptnew = """
Memory Extraction Engine

RULES
- Extract ONLY new, persistent long-term information introduced in [TARGET MESSAGE].
- NEVER answer questions asked in [TARGET MESSAGE]. You are an extractor, not a chatbot.
- Questions, queries, and requests contain NO personal information, output NONE.
- NEVER attribute the assistant's identity, role, or traits to the User.
- Use [BACKGROUND CONTEXT] ONLY for context, i.e. resolve pronouns, implicit references, and missing root entities. If [BACKGROUND CONTEXT] includes irrelevant details, ignore it.
- Each fact must be a single, self-contained line explicitly named with the full subject—never use relative time, vague pronouns, or shorthand.
- Consolidate causally related details into ONE single output line per [TARGET MESSAGE].
- Output NONE if [TARGET MESSAGE] contains no durable information, contains only transient conversational chatter, or contains only questions/queries.
"""

exract_prompt = f"""
/no_think
You are a memory extraction engine. 
Your only task is to extract durable user information from [TARGET MESSAGE].

RULES
- Extract ONLY new, persistent long-term information introduced in [TARGET MESSAGE].
- NEVER answer questions asked in [TARGET MESSAGE]. You are an extractor, not a chatbot.
- Questions, queries, and requests contain NO personal information. Output NONE.
- NEVER attribute the assistant's identity, role, or traits to the User.
- Use [BACKGROUND CONTEXT] ONLY for context, i.e. resolve pronouns, implicit references, and missing root entities. If [BACKGROUND CONTEXT] includes irrelevant details, ignore it.
- Each fact must be a single, self-contained line explicitly named with the full subject—never use relative time, vague pronouns, or shorthand.
- Consolidate causally related details into ONE single output line per [TARGET MESSAGE].
- Output NONE if [TARGET MESSAGE] contains no durable information, contains only transient conversational chatter, or contains only questions/queries.

Ex:
[BACKGROUND CONTEXT]
User: "My sister Maya and I went to the local animal shelter."
Assistant: "Oh nice! Did either of you end up adopting?"
User: "Yeah, she adopted a senior cat and I got a puppy."
Assistant: "How sweet! What did you end up naming him?"
[TARGET MESSAGE]
User: "Buster. He's a rescue beagle."
OUTPUT:
User named their rescue beagle puppy buster | name, dog

Ex:
[BACKGROUND CONTEXT]
User: "How do i create a list in python"
Assistant: "Enclose the items inside square brackets and separating each item with a comma"
[TARGET MESSAGE]
User: "How to create an object"
OUTPUT:
NONE

Ex:
[BACKGROUND CONTEXT]
[TARGET MESSAGE]
User: "Do you remember my friend joshua"
Output:
NONE | NONE

Ex:
[BACKGROUND CONTEXT]
User: "Create a new project file and index it as Mark 2."
Assistant: "Should I store it in the main database?"
[TARGET MESSAGE]
User: "Yes"
Output:
User instructed to store Mark 2 in the main database | project, file, storage, index

[BACKGROUND CONTEXT]
User: "Can you help me clean up this Excel spreadsheet?"
Assistant: "Sure! What needs to be formatted or fixed?"
User: "I need to remove duplicate entries in Column C."
Assistant: "You can use Excel's built-in 'Remove Duplicates' feature under the Data tab."
[TARGET MESSAGE]
User: "Thanks! I really appreciate it"
Output:
NONE

[BACKGROUND CONTEXT]
User: "Hey"
Assistant: "Good afternoon!"
[TARGET MESSAGE]
User: "Who are you? What is my name?"
Output:
NONE
"""

filter_prompt = """
You are a memory deduplication filter. Compare the NEW MEMORY against the EXISTING MEMORIES list and output only one word.

Rules:
- DUPLICATE: the information already exists, even if rephrased.
- NEW: information is not present in EXISTING MEMORIES
- NEW: adds detail on EXISTING MEMORIES

Examples:
NEW MEMORY: User recently moved to BGC for work.
EXISTING MEMORIES:
- User lives in BGC.
- User has a dog named Bruno.
- User works at Google as a senior engineer.
- User's birthday is April 19.
Output: NEW

NEW MEMORY: User switched from coffee to tea last year.
EXISTING MEMORIES:
- User's favorite food is ramen.
- User owns a red SG guitar.
- User's mom's birthday is March 15.
- User is 27 years old.
- User hates mornings.
Output: NEW

NEW MEMORY: User's dog is a golden retriever.
EXISTING MEMORIES:
- User has a dog named Bruno.
- User works remotely.
- User likes sourdough bread.
- User is learning Japanese.
- User's sister is named Camille.
Output: NEW

NEW MEMORY: User's brother is 5'6 tall.
EXISTING MEMORIES:
- User's brother is tall.
- User's girlfriend's name is Riane.
- User prefers green tea.
- User runs a bakery in Makati.
- User studied Computer Engineering.
Output: NEW

NEW MEMORY: User works at Google.
EXISTING MEMORIES:
- User is a senior engineer at Google.
- User moved to Seattle for work.
- User likes dark roast coffee.
- User is ranked 1800 ELO in chess.
- User bought a house in BGC.
Output: DUPLICATE
"""


def save(history):

    history = (
        f"[BACKGROUND CONTEXT]\n"
        f"{'\n'.join(history[:-1])}\n"
        f"[TARGET MESSAGE]\n"
        f"{history[-1]}"
    )
    
    t1 = time.perf_counter()
    extracted = extractor.create_chat_completion([
        {"role":"system","content":exract_prompt},
        {"role": "user", "content": history }],
          max_tokens=256,
          temperature=0.0,
          top_p=0.95,
          top_k=40,
          min_p=0.05,
          repeat_penalty=1.1,
          presence_penalty=0,
          stream=True,
    )
    ft = False
    t1 = time.perf_counter()
    message = ""
    for chunk in extracted:
        if not ft:
            ft = True
            print("TTFT ng extractor:",time.perf_counter()-t1)
        delta = chunk["choices"][0]["delta"]
        if delta.get("content"):
            message += delta["content"]

    
    extracted = message.replace("<think>","").replace("</think>","").strip()
    extractor.reset()
    memories = mem_handler.retrieve_memory(extracted,3,0.65)
    #print("EXTRACTION TIME:",time.pef_counter()-t1)
    #print("\n\nMEMORIES:\n",memories,"\n")

    for info in extracted.split("\n"):
        info = info.strip()
        if info == "NONE" or info.startswith("NONE"):
            print("\n[no memory extracted]")
            return

        banned = ("User asked","User is asking","User wants to know","Assistant:","User:")
        if info.startswith(banned):
            print("ahahaha")
            continue
        
        if not memories:
            print(f"[saved agad: {info}]")
            mem_handler.save_memory(info, time.strftime("%b %d %Y %H:%M"))
            continue
        
        mem_filter = filter.create_chat_completion([
            {"role":"system","content": filter_prompt},
            {"role":"user","content":f"NEW MEMORY: {extracted}\n\nEXISTING MEMORIES:\n{memories}"}
            ],
            max_tokens=256,
            temperature=0.0,
            top_p=0.95,
            top_k=40,
            min_p=0.05,
            repeat_penalty=1.1,
            
            )["choices"][0]["message"]["content"]
        print(f"[{mem_filter}: {info}]")


        if mem_filter == "NEW":
            mem_handler.save_memory(info, time.strftime("%b %d %Y %H:%M"))




