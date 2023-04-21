# `tokmon` 🔤🧐 - CLI utility to monitor OpenAI token costs

`tokmon` enables you to monitor your program's OpenAI API token usage.

You use `tokmon` just like you would use the `time` utility, but instead of execution time you get token usage and cost.
<p align="center">
    <img src="https://user-images.githubusercontent.com/3611042/231910274-3872e13f-d9e6-4752-bc89-44e5d334e21f.gif" />
</p>

## Try it out

```bash

# Install tokmon
pip install tokmon

# Clone this repo and `cd` into the `tokmon` folder
git clone https://github.com/yagil/tokmon.git && cd tokmon

# export your OpenAI API key. This will be used in the test program (source in ./tests/python_example.py)
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY" 

# Run tokmon
tokmon --json_out=. python3 ./tests/python_example.py --prompt "say 'hello, tokmon!'"
```

After your program finishes running (or you `ctrl^C` it), `tokmon` will automatically generate a cost report that looks like this:<br>

```yaml
tokmon cost report:
================================================================================
Monitored invocation: ./python_example.py -i
Models: ['gpt-3.5-turbo-0301']
Total Usage: {'total_prompt_tokens': 49, 'total_completion_tokens': 44, 'total_tokens': 93}
Pricing: {'gpt-3.5-turbo-0301': {'prompt_cost': 0.002, 'completion_cost': 0.002, 'per_tokens': 1000}}
Total Cost: $0.000186
================================================================================

Writing cost summary to JSON file: /tmp/tokmon_usage_summary_1681426650.json
```

#### `tokmon` also supports this:
- If your program uses multiple OpenAI models in the same invocation, their respective usages will be reflected in the report.
- You can run multiple instances of `tokmon` simultaneously. Each invocation will generate a separate usage report.
- Pass a `--json_out /your/path/report.json` to get a detailed breakdown + conversation history in JSON format.

# Get started with `tokmon`

## Install `tokmon` via `pip`
```
pip install tokmon
```

Make sure installation worked by running
```
tokmon --help
```

To uninstall, run `pip uninstall tokmon`<br>


## Use `tokmon` with your application or script

> **Warning**
> This is a debugging tool. It is not intended to be used in any consequential setting. Use your best judgement, you're on your own!

Prepend `tokmon` to your normal program invocation like so:
```bash
$ tokmon <your program> [arg1] [arg2] ...
```
Run and use your program just like you would normally (arguments and all). Interactive usage is supported as well.


## Full usage and cost summary (JSON)

```json
{
    "total_cost": 0.0019199999999999998,
    "total_usage": {
        "total_prompt_tokens": 18,
        "total_completion_tokens": 23,
        "total_tokens": 41
    },
    "pricing_data": "{'gpt-4-0314': {'prompt_cost': 0.03, 'completion_cost': 0.06, 'per_tokens': 1000}}",
    "models": [
        "gpt-4-0314"
    ],
    "raw_data": [
        {
            "model": "gpt-4-0314",
            "usage": {
                "prompt_tokens": 18,
                "completion_tokens": 23,
                "total_tokens": 41
            },
            "cost": 0.0019199999999999998,
            "messages": [
                {
                    "role": "system",
                    "content": "You're a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "hello"
                },
                {
                    "role": "assistant",
                    "content": "Hello! How can I help you today? If you have any questions or need assistance, feel free to ask."
                }
            ]
        }
    ]
}
```

## How it works
`tokmon` uses the [mitmproxy library](https://github.com/mitmproxy/mitmproxy) to intercept HTTP requests and responses between your program and the OpenAI API.
It then processes the request and response data to calculate token usage and cost based on [tokmon/openai-pricing.json](tokmon/openai-pricing.json).

> `tokmon` works for programs in `python` / `node` (using OpenAI's clients), or `curl` (run directly, and not i.e. in a bash script).

> if you [manually install `mitmproxy`'s CA certificate](https://docs.mitmproxy.org/stable/concepts-certificates/#:~:text=Go%20to%20Settings%20%3E%20General%20%3E%20About,trust%20for%20the%20mitmproxy%20certificate), it should work for all executables (note: haven't tested this.)

In most cases, `tokmon` relies on the `usage` field in OpenAI's API responses for token counts. For streaming requests, however, `tokmon` uses OpenAI's [tiktoken library](https://github.com/openai/tiktoken) directly to count the tokens. As of writing OpenAI's API does not return usage data for streaming requests ([reference](https://community.openai.com/t/usage-info-in-api-responses/18862/11).)

## openai-pricing.json
The pricing data was extracted from OpenAI's website with the help of ChatGPT.

`tokmon` is using [tokmon/openai-pricing.json](tokmon/openai-pricing.json) from its package. 

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

You can override the default pricing with: `tokmon --pricing /path/to/your/custom-openai-pricing.json ...`

> This pricing JSON is incomplete (missing DALL-E, etc.), it may be incorrect, and it may go out of date.

> For best results, make sure to check that you have the latest pricing.

## Current Limitations
1. Event streaming: `tokmon` buffers Server-Sent Events (SSE) until the `data: [DONE]` chunk is received. If the monitored program leverages event streaming, its behavior will be modified.
    - Status: looking into it. Pull requests welcome.

## Contributing
If you'd like to contribute to the project, please follow these steps:
1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and test them.
4. Submit a pull request with a clear description of your changes and any relevant information.

## Warning
1. `tokmon` comes without any warranty or guarantee whatsoever.
2. `tokmon` was tested on macOS only. It might not work on other platforms.
3. This tool may not work as intended, have unknown side effects, may output incorrect information, or not work at all.
4. The pricing data in `openai-pricing.json` may go out of date.
