import sys
from typing import Optional
import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def main(model: str, prompt: Optional[str] = None, stream: bool = False):
    messages = [{"role": "system", "content": "You're a helpful assistant."}]

    if not prompt:
        prompt = input("Enter prompt and press ENTER\n")
    else:
        print(f"Prompt: {prompt}\n")
    messages.append({"role": "user", "content": prompt})
    print()

    call_res = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=stream,
        )
    
    if stream:
        # if stream=True call_res is a generator
        for msg in call_res:
            choice = msg.choices[0]
            if "delta" in choice:
                if "content" in choice["delta"]:
                    token = choice["delta"]["content"]
                    print(token, end="", flush=True)
    else:
        print("Got response.")

if __name__ == "__main__":
    # if sys.arv contains '--prompt' then run headless
    headless = False
    if len(sys.argv) > 2:
        headless = sys.argv[1] == "--prompt"

    stream = "--stream" in sys.argv

    # model = "gpt-3.5-turbo"
    model = "gpt-4"
    
    if headless:
        main(model, prompt=sys.argv[2], stream=stream)
    else:
        main(stream=stream)