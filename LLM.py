from groq import Groq
import os

model = "openai/gpt-oss-20b"
client = Groq(api_key=os.getenv('groq_api_key'))
def call_model(msgs,tools,system_prompt):
    try:
        output = client.chat.completions.create(
            model=model,
            messages=[{"role":"system","content":system_prompt}, *msgs],
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            tools=tools,
            reasoning_effort="low"
        )
        
        return output.choices[0].message
    
    except Exception as e:
        raise RuntimeError(f"[ERROR calling model] {e}")
