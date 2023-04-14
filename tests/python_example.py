#!/usr/bin/env python3
import sys
from typing import Optional
import openai
from dotenv import load_dotenv
import os
import signal

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

messages = [{"role": "system", "content": "You're a helpful assistant."}]

# catch ctrl c
def signal_handler(sig, frame):
    print("Exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main(model: str, prompt: Optional[str] = None, stream: bool = False, interactive: bool = False):
    if interactive:
        print("'-i' flag found. Running in a loop...")
        while True:
            call_openai(model, prompt, stream)
    else:
        call_openai(model, prompt, stream)

def call_openai(model: str, prompt: Optional[str], stream: bool):
    if not prompt:
        prompt = input("Enter prompt and press ENTER\n")
    else:
        print(f"Prompt: {prompt}")
    messages.append({"role": "user", "content": prompt})
    print()

    call_res = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=stream,
            temperature=0,
        )
    
    gpt_response = ""
    if stream: # when stream is True, call_res is a generator
        for msg in call_res:
            choice = msg.choices[0]
            if "delta" in choice:
                if "content" in choice["delta"]:
                    tokens = choice["delta"]["content"]
                    gpt_response += tokens
                    print(tokens, end="", flush=True)
    else:
        gpt_response = call_res.choices[0].message.content
        print(gpt_response)
    messages.append({"role": "assistant", "content": gpt_response})

if __name__ == "__main__":
    # if sys.arv contains '--prompt' then run headless
    headless = False
    if len(sys.argv) > 2:
        headless = sys.argv[1] == "--prompt"

    stream = "--stream" in sys.argv
    interactive = "-i" in sys.argv

    model = "gpt-3.5-turbo"
    # model = "gpt-4"
    
    if headless:
        main(model, prompt=sys.argv[2], stream=stream, interactive=interactive)
    else:
        main(model, stream=stream, interactive=interactive)