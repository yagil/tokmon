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
from tokmon.beam import BeamClient, BeamType

PROG_NAME = "tokmon"

BOLD = "\033[1m"
RESET = "\033[0m"
MAGENTA = "\033[35m"

WHITE = "\033[37m"
GRAY = "\033[90m"
GREEN = "\033[32m"
BLUE = "\033[34m"
ORANGE = "\033[33m"
PINK = "\033[95m"

def bold(s:str):
    return f"{BOLD}{s}{RESET}"

def color(s:str, color:str, bold:bool = True):
    if bold:
        return f"{BOLD}{color}{s}{RESET}"
    else:
        return f"{color}{s}{RESET}"

def print_usage_report(monitored_invocation:str, cost_summary: Dict):
    models = cost_summary["models"]
    pricing = cost_summary["pricing_data"]
    total_cost = cost_summary["total_cost"]
    total_usage = cost_summary["total_usage"]

    cost_str = f"${total_cost:.6f}"
    report_header = f"{PROG_NAME} cost report:"

    print(f"""
{color(report_header, GREEN)}
{color('='*80, GRAY, bold=False)}
{bold("Monitored invocation")}: {monitored_invocation}
{bold("Models")}: {models}
{bold("Total Usage")}: {total_usage}
{bold("Pricing")}: {pricing}
{color("Total Cost", MAGENTA)}: {color(cost_str, MAGENTA)}
{color('='*80, GRAY, bold=False)}
""")
          
# ASCII ART for the tokmon logo
# https://patorjk.com/software/taag/#p=display&f=Big&t=tokmon
TOKMON_LOGO = color("""
 ______   ______    __  __    __    __    ______    __   __    
/\__  _\ /\  __ \  /\ \/ /   /\ "-./  \  /\  __ \  /\ "-.\ \   
\/_/\ \/ \ \ \/\ \ \ \  _"-. \ \ \-./\ \ \ \ \/\ \ \ \ \-.  \  
   \ \_\  \ \_____\ \ \_\ \_\ \ \_\ \ \_\ \ \_____\ \ \_\ \"\_\ 
    \/_/   \/_____/  \/_/\/_/  \/_/  \/_/  \/_____/  \/_/ \/_/                                                                                                          
""", GREEN, bold=False)


OPENAI_API_PATH = "https://api.openai.com"
DEFAULT_JSON_OUT_PATH = "/tmp"

DEFAULT_BEAM_TYPE = BeamType.SUMMARY.value
DEFAULT_BEAM_URL = "http://localhost:9000"

def cli():
    """
    The `tokmon` utility can be used to monitor the cost of OpenAI API calls made by a program.
    After te program has finished running, the `tokmon` will print the total cost of the program.
    """
    parser = argparse.ArgumentParser(description=f"""
{TOKMON_LOGO}        

{color("A utility to monitor your program's OpenAI token usage.", GREEN)}

{color("• Example Usage:", BLUE)} {color("tokmon --json_out='.' <your program> [arg1] [arg2] ...", ORANGE, bold=False)}

{color("• Important: you need to include the `--` arguments before the target program name and arguments.", MAGENTA)}

{color("• Report Bugs & Get Help: https://github.com/yagil/tokmon/issues", GRAY)}

""",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     add_help=False)

    current_time = int(time.time())

    parser.add_argument("program_name", nargs="?", help="The name of the monitored program")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="The command and arguments to run the monitored program")
    parser.add_argument("-p", "--pricing", type=str, help="Path to a custom OpenAI pricing JSON file", default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output")
    parser.add_argument("-j", "--json_out", type=str, help="Path to a JSON file to write the cost summary to. Saves to /tmp by default", default=DEFAULT_JSON_OUT_PATH)
    parser.add_argument("-n", "--no_json", action="store_true", help="Do not write a cost summary to a JSON file")
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    
    parser.add_argument("--beam", type=str, choices=["summary", "reqres"], help="""The type of data to send to the tokmon beam server.
• 'summary': sends a JSON object with the usage summary at the end of the program.
• 'reqres': sends a JSON object after every request-response pair, and the usage summary (minus 'raw_data') at the end.
    """, default=None, nargs="?", const=DEFAULT_BEAM_TYPE)
    parser.add_argument("--beam_url", type=str, help="[Optional] Override the default URL for the tokmon beam server", default=DEFAULT_BEAM_URL)

    args = parser.parse_args()

    if args.no_json and args.json_out != DEFAULT_JSON_OUT_PATH:
        parser.error("Cannot use --json_out and --no_json together")
        sys.exit(1)

    if not args.program_name:
        parser.print_help()
        sys.exit(1)

    # Note: openai-pricing data may go out of date
    if args.pricing:
        pricing_json = args.pricing
    else:
        pricing_json = pkg_resources.resource_filename(PROG_NAME, "openai-pricing.json")

    with open(pricing_json, "r") as f:
        pricing = json.load(f)

    monitored_prog = f"{args.program_name} { ' '.join(args.args) if args.args else ''}"

    beam_client = None
    if args.beam:
        # convert args.beam to beam_type Enum
        beam_type = BeamType(args.beam)
        beam_url = args.beam_url
        if beam_url is None:
            beam_url = DEFAULT_BEAM_URL
        beam_client = BeamClient(beam_url, beam_type=beam_type, verbose=args.verbose)
        
        if args.verbose:
            print(f"[{PROG_NAME}] Starting a beam server: {beam_url}. Type: {beam_type}.")

    # Instantiate the token monitor
    tokmon = TokenMonitor(OPENAI_API_PATH, args.program_name, *args.args, verbose=args.verbose, beam_client=beam_client)

    try:
        monitoring_str = f"[{PROG_NAME}] Monitoring token usage for {color(monitored_prog, GREEN)} ..."
        print(f"{color(monitoring_str, MAGENTA)}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(tokmon.start_monitoring())
    except KeyboardInterrupt:
        interrupted_str = f"\n[{PROG_NAME}] Interrupted. Generating token usage report ..."
        print(f"{color(interrupted_str, MAGENTA)}")
    finally:
        tokmon.stop_monitoring()
        
        # Get the usage summary
        conversation_id, usage_summary = tokmon.usage_summary()
        
        # If no usage was detected, print a message and exit
        if len(usage_summary) == 0:
            status_str = f"[{PROG_NAME}] No OpenAI API calls detected for `{monitored_prog}`."
            print(f"{color(status_str, MAGENTA)}")
            return

        # Print usage report to the terminal
        cost_summary = generate_summary_object(conversation_id, usage_summary, pricing)
        print_usage_report(monitored_prog, cost_summary)

        if beam_client:
            beam_client.beam_summary(cost_summary)

        # Write usage report to a JSON file (indepedent of beam'ing)
        if args.json_out and not args.no_json:
            json_out_filename = f"{PROG_NAME}_usage_summary_{current_time}.json"
            out_dir_path = args.json_out
            if not os.path.exists(out_dir_path):
                print(f"** Path does not exist: {out_dir_path}, falling back to {DEFAULT_JSON_OUT_PATH}")
                out_dir_path = DEFAULT_JSON_OUT_PATH
            json_out_path = os.path.join(out_dir_path, f"{json_out_filename}")
            print(f"Writing cost summary to JSON file: {color(json_out_path, GREEN)} {color('(run with --no_json to disable this behavior)', GRAY)}")
            with open(json_out_path, "w") as f:
                 json.dump(cost_summary, f, indent=4)

def generate_summary_object(conversation_id:str, usage_summary: List[Tuple[Dict, Dict]], pricing: Dict):
    costCalculator = CostCalculator(pricing)
    usage_with_cost = costCalculator.calculate_cost(conversation_id, usage_summary)
    return usage_with_cost

if __name__ == '__main__':
    cli()