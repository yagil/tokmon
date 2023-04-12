# tokmon - CLI utility to monitor OpenAI API costs

`tokmon` is a command-line utility that helps you monitor the token costs of your OpenAI API calls. It works by intercepting the API requests and responses, calculating the token usage, and generating a cost report based on the pricing information.

## Usage

Use `tokmon` like you would use the `time` utility to measure execution time.

`tokmon` will automatically generate a cost report when the target program finishes executing. Pressing `ctrl^C` will also trigger a usage report.

```
# $ tokmon <program_to_monitor> [arguments...]
$ tokmon gpt4

[tokmon] Monitoring program for token costs gpt4  ...

... after `gpt4` finishes running OR ctrl^C ...

tokmon cost report:
================================================================================
Monitored invocation: ['gpt4']
Model: gpt-4
Usage: {'prompt_tokens': 74, 'completion_tokens': 13, 'total_tokens': 87}
Pricing: {'prompt_cost': 0.03, 'completion_cost': 0.06, 'per_tokens': 1000}
Cost: $0.003000
================================================================================
```

# Known Limitations
1. Event streaming: `tokmon` will override this setting and buffer Server-Sent Events (SSE) data chunks until the `data: [DONE]` chunk is received. If the monitored program leverages event streaming, its behavior will be modified.

# Setup
1. Clone the repository and navigate to the project directory.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Run `tokmon` with your desired program and arguments.

# Options
```bash
usage: tokmon [-h] program_name ...

A utility to monitor OpenAI token cost of a target program.

positional arguments:
  program_name  The name of the monitored program
  args          The command and arguments to run the monitored program

optional arguments:
  -h, --help    show this help message and exit
```

# How it works
`tokmon` uses the [mitmproxy library](https://github.com/mitmproxy/mitmproxy) to intercept HTTP requests and responses between your program and the OpenAI API. It then processes the request and response data to calculate token usage and cost based on the provided pricing information.

For streaming requests, `tokmon` uses the OpenAI's [tiktoken library](https://github.com/openai/tiktoken) to count tokens directly, because as of writing the OpenAI API does not return usage data for streaming requests.

# Warning
1. This tool may not work as intended, have uknown side effects, or output incorrect information. Use your own judgement!
2. This tool is intended for debugging during development. It is not intended to be used in production.
3. The pricing data in `pricing.json` may go out of date.