import asyncio
import argparse
import json
import sys

from tokmon import monitor_cost
from typing import Dict

PROG_NAME = "tokmon"

BOLD = "\033[1m"
RESET = "\033[0m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"
GREEN = "\033[32m"

def bold(s:str):
    return f"{BOLD}{s}{RESET}"

def color(s:str, color:str, bold:bool = True):
    if bold:
        return f"{BOLD}{color}{s}{RESET}"
    else:
        return f"{color}{s}{RESET}"

def generate_usage_report(monitored_invocation:str ,model:str, usage_data:Dict, pricing:Dict, total_cost:float):
    model_pricing = pricing[model]

    cost_str = f"${total_cost:.9f}"
    report_header = f"{PROG_NAME} cost report:"

    return f"""
{color(report_header, GREEN)}
{color('='*80, GRAY, bold=False)}
{bold("Monitored invocation")}: {monitored_invocation}
{bold("Model")}: {model}
{bold("Usage")}: {usage_data}
{bold("Pricing")}: {model_pricing}
{color("Cost", MAGENTA)}: {color(cost_str, MAGENTA)}
{color('='*80, GRAY, bold=False)}
    """

def cli():
    """
    The {PROG_NAME} utility can be used to monitor the cost of OpenAI API calls made by a program.
    After te program has finished running, the {PROG_NAME} will print the total cost of the program.
    """

    parser = argparse.ArgumentParser(description="A utility to monitor OpenAI token cost.")

    parser.add_argument("program_name", help="The name of the monitored program")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="The command and arguments to run the monitored program")

    args = parser.parse_args()

    pricing = json.load(open("pricing.json", "r"))

    # support other providers in the future...
    OPENAI_API_PATH = "https://api.openai.com"
    
    monitored_prog = f"{args.program_name} { ' '.join(args.args) if args.args else ''}"
    print(f"Monitoring program for token costs {color(monitored_prog, GREEN)}...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    model, usage_data, total_cost = loop.run_until_complete(monitor_cost(OPENAI_API_PATH, pricing, args.program_name, *args.args))
    monitored_invocation = [args.program_name] + [arg for arg in args.args]
    report = generate_usage_report(monitored_invocation, model, usage_data, pricing, total_cost)
    print(f"\n{report}")

if __name__ == '__main__':
    cli()