# 🔤🧐 `tokmon` - CLI utility to monitor OpenAI API costs

`tokmon` enables you to monitor your program's OpenAI API token usage.

You use `tokmon` just like you would use the `time` utility, but instead of execution time you get token usage and cost.

## How to use `tokmon`

> **Warning**
> This is a debugging tool. It is not intended to be used in any consequential setting. Use your best judgement, your're on your own!

Prepend `tokmon` to your normal program invocation like so:
```bash
$ tokmon ./my_gpt_program --my_arg "hi"
```
After this, use your program just like you would normally (interactive usage is supported as well).

After your program finishes running (or `ctrl^C` is pressed), `tokmon` will automatically generate a cost report that looks like this:

```yaml
tokmon cost report:
================================================================================
Monitored invocation: ['./my_gpt_program', '--my_arg', 'hi']
Model: gpt-4
Usage: {'prompt_tokens': 74, 'completion_tokens': 13, 'total_tokens': 87}
Pricing: {'prompt_cost': 0.03, 'completion_cost': 0.06, 'per_tokens': 1000}
Cost: $0.003000
================================================================================
```

## Features
1. Measure token usage (breakdown by `prompt`, and `completion`) and $ cost.
2. You can run multiple instances of `tokmon` simultaenously
3. Works for interactive scripts as well

```zsh
usage: tokmon [-p PRICING] [-h] [program_name] ...

A utility to monitor OpenAI token cost of a target program.

positional arguments:
  program_name          The name of the monitored program
  args                  The command and arguments to run the monitored program

optional arguments:
  -p PRICING, --pricing PRICING
                        Path to a custom pricing JSON file
  -h, --help            Show this help message and exit
```

## Install from source
1. Clone the repository and `cd` to the project root.
2. Install the package and its dependencies using `pip install .`
3. You're ready to use `tokmon` (sourcing your terminal might be required).

To uninstall, run `pip uninstall tokmon`<br>
Tip: make sure that the expected python Library route is in your `PATH`.

## Run from the repo after cloning it
```bash
$ cd /path/to/tokmon
$ python -m tokmon.cli <program to monitor> [arguments...]
```

## How it works
`tokmon` uses the [mitmproxy library](https://github.com/mitmproxy/mitmproxy) to intercept HTTP requests and responses between your program and the OpenAI API.
It then processes the request and response data to calculate token usage and cost based on the provided pricing information (see [tokmon/pricing.json](tokmon/pricing.json) in this repo).

In most cases, `tokmon` relies on the `usage` field in OpenAI API respones in order to count token. For streaming requests, however, `tokmon` uses the OpenAI's [tiktoken library](https://github.com/openai/tiktoken) directly: as of writing OpenAI's API does not return usage data for streaming requests ([reference](https://community.openai.com/t/usage-info-in-api-responses/18862/11).)

## Pricing data
The pricing data was extracted from OpenAI's website with the help of ChatGPT.

`tokmon` is using [tokmon/pricing.json](tokmon/pricing.json) from its package. You can override it like so: `tokmon --pricing /path/to/your/custom_pricing.json`

```json
{   
    "last_updated": "2023-04-12",
    "data_sources": [
        "https://openai.com/pricing",
        "https://platform.openai.com/docs/models/model-endpoint-compatibility"
    ],
    "gpt-4": {"prompt_cost": 0.03, "completion_cost": 0.06, "per_tokens": 1000},
    "gpt-4-0314": {"prompt_cost": 0.03, "completion_cost": 0.06, "per_tokens": 1000},
    "gpt-4-32k": {"prompt_cost": 0.06, "completion_cost": 0.12, "per_tokens": 1000},
    "gpt-4-32k-0314": {"prompt_cost": 0.06, "completion_cost": 0.12, "per_tokens": 1000},
    "gpt-3.5-turbo": {"prompt_cost": 0.002, "completion_cost": 0.002, "per_tokens": 1000},
    "gpt-3.5-turbo-0301": {"prompt_cost": 0.002, "completion_cost": 0.002, "per_tokens": 1000},
    "text-davinci-003": {"cost": 0.02, "per_tokens": 1000},
    "text-curie-001": {"cost": 0.002, "per_tokens": 1000},
    "text-babbage-001": {"cost": 0.0005, "per_tokens": 1000},
    "text-ada-001": {"cost": 0.0004, "per_tokens": 1000},
    "text-embedding-ada-002": {"cost": 0.0004, "per_tokens": 1000}
}
```

> This pricing JSON is incomplete (missing DALL-E, etc.), it may be incorrect, and/or it may go out of date.

> Make sure to always check that you have the latest version.

## Current Limitations
1. Event streaming: `tokmon` will override this setting and buffer Server-Sent Events (SSE) data chunks until the `data: [DONE]` chunk is received. If the monitored program leverages event streaming, its behavior will be modified.
    - Status: looking into it. Pull requests welcome.
2. If your monitored program makes call more than 1 type of OpenAI models, your accounting will be incorrect.
    - Status: it's on the list

## Contributing
Help is wanted. If you'd like to contribute to the project, please follow these steps:
1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and test them.
4. Submit a pull request with a clear description of your changes and any relevant information.

## Warning
1. `tokmon` comes without any warranty or guarantee whatsoever.
2. Tested on macOS only.
3. This tool may not work as intended, have unknown side effects, and/or it may output incorrect information.
4. The pricing data in `pricing.json` may go out of date.
