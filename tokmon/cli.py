import asyncio
import argparse
import json
import sys
import os
import pkg_resources
import time
from typing import List, Tuple, Dict

from tokmon.tokmon import TokenMonitor
from tokmon.costcalculator import CostCalculator

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

def generate_usage_report(monitored_invocation:str, cost_summary: Dict):
    models = cost_summary["models"]
    pricing = cost_summary["pricing_data"]
    total_cost = cost_summary["total_cost"]
    total_usage = cost_summary["total_usage"]

    cost_str = f"${total_cost:.6f}"
    report_header = f"{PROG_NAME} cost report:"

    return f"""
{color(report_header, GREEN)}
{color('='*80, GRAY, bold=False)}
{bold("Monitored invocation")}: {monitored_invocation}
{bold("Models")}: {models}
{bold("Total Usage")}: {total_usage}
{bold("Pricing")}: {pricing}
{color("Total Cost", MAGENTA)}: {color(cost_str, MAGENTA)}
{color('='*80, GRAY, bold=False)}
"""

OPENAI_API_PATH = "https://api.openai.com"

def cli():
    """
    The {PROG_NAME} utility can be used to monitor the cost of OpenAI API calls made by a program.
    After te program has finished running, the {PROG_NAME} will print the total cost of the program.
    """

    parser = argparse.ArgumentParser(description="A utility to monitor OpenAI token cost of a target program.",
                                     add_help=False)

    current_time = int(time.time())
    default_json_out = os.path.join("/tmp", f"tokmon_cost_summary_{current_time}.json")

    parser.add_argument("program_name", nargs="?", help="The name of the monitored program")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="The command and arguments to run the monitored program")
    parser.add_argument("-p", "--pricing", type=str, help="Path to a custom pricing JSON file", default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output")
    parser.add_argument("-j", "--json_out", type=str, help="Path to a JSON file to write the cost summary to. Saves to /tmp by default", default=default_json_out)
    parser.add_argument("-n", "--no_json", action="store_true", help="Do not write a cost summary to a JSON file")
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")

    args = parser.parse_args()

    if not args.program_name:
        parser.print_help()
        sys.exit(1)

    # Note: pricing data may go out of date
    if args.pricing:
        pricing_json = args.pricing
    else:
        pricing_json = pkg_resources.resource_filename("tokmon", "pricing.json")

    with open(pricing_json, "r") as f:
        pricing = json.load(f)

    monitored_prog = f"{args.program_name} { ' '.join(args.args) if args.args else ''}"

    # Instantiate the token monitor
    tokmon = TokenMonitor(OPENAI_API_PATH, args.program_name, *args.args, verbose=args.verbose)
    cost_summary = {}

    try:
        monitoring_str = f"[{PROG_NAME}] Monitoring program for token costs for {color(monitored_prog, GREEN)} ..."
        print(f"{color(monitoring_str, MAGENTA)}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(tokmon.start_monitoring())
    except KeyboardInterrupt:
        interrupted_str = f"\n[{PROG_NAME}] Interrupted. Generating token usage report ..."
        print(f"{color(interrupted_str, MAGENTA)}")
    finally:
        tokmon.stop_monitoring()
        usage_summary = tokmon.usage_summary()
        
        if len(usage_summary) > 0:
            cost_summary = calculate(usage_summary, pricing)
            report = generate_usage_report(monitored_prog, cost_summary)
            print(f"\n{report}")
        else:
            status_str = f"[{PROG_NAME}] No OpenAI API calls detected for `{monitored_prog}`."
            print(f"{color(status_str, MAGENTA)}")

        if args.json_out and not args.no_json:
            print(f"Writing cost summary to JSON file ... {color(args.json_out, GREEN)} {color('(run with --no_json to disable this behavior)', GRAY)}")
            with open(args.json_out, "w") as f:
                json.dump(cost_summary, f, indent=4)
            

def calculate(usage_summary: List[Tuple[Dict, Dict]], pricing: Dict):
    costCalculator = CostCalculator(pricing)
    usage_with_cost = costCalculator.calculate_cost(usage_summary)
    return usage_with_cost

if __name__ == '__main__':
    cli()