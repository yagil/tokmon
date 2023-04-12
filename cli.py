import asyncio
import argparse
import json
import sys

from tokmon import monitor_cost, query_cost_data

PROG_NAME = "tokmon"

BOLD = "\033[1m"
RESET = "\033[0m"

def cli():
    """
    The {PROG_NAME} utility can be used to monitor the cost of OpenAI API calls made by a program.
    After te program has finished running, the {PROG_NAME} will print the total cost of the program.
    """

    parser = argparse.ArgumentParser(description="A utility to monitor OpenAI token cost.")
    
    # Future:
    # group = parser.add_mutually_exclusive_group()
    # group.add_argument("--daemon", action="store_true", help=f"Run {BOLD}{PROG_NAME}{RESET} in daemon mode")
    # group.add_argument("--query", metavar="PROGRAM_NAME", help="Query cost data for the specified program")

    parser.add_argument("--pricing-data", metavar="COST_DATA_JSON", help="JSON string of cost data, e.g.: {\"gpt-4-0314\": {\"cost\": 0.03, \"per_tokens\":1000}}")

    parser.add_argument("program_name", help="The name of the monitored program")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="The command and arguments to run the monitored program")

    default_pricing = {
                        'gpt-4-0314': {'cost': 0.03, 'per_tokens':1000},
                        'gpt-3.5-turbo-0301': {'cost': 0.002, 'per_tokens':1000},
                        'text-ada-001': {'cost': 0.0004, 'per_tokens':1000}
                       }

    args = parser.parse_args()

    pricing = json.loads(args.pricing_data) if args.pricing_data else default_pricing

    # support other providers in the future...
    OPENAI_API_PATH = "https://api.openai.com"

    run_as_daemon = False # future: args.daemon
    if run_as_daemon:
        print("Running as daemon...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(monitor_cost(OPENAI_API_PATH, pricing, daemon=True))
    else:
        print(f"Monitoring prorgam {args.program_name}...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(monitor_cost(OPENAI_API_PATH, pricing, args.program_name, *args.args))

if __name__ == '__main__':
    cli()