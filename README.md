# `tokmon` 🔤🧐 - CLI utility to monitor OpenAI token costs

`tokmon` enables you to monitor your program's OpenAI API token usage.

You use `tokmon` just like you would use the `time` utility, but instead of execution time you get token usage and cost.

## How to use `tokmon`

> **Warning**
> This is a debugging tool. It is not intended to be used in any consequential setting. Use your best judgement, you're on your own!

Prepend `tokmon` to your normal program invocation like so:
```bash
$ tokmon ./my_gpt_program --my_arg "hi"
```
Run and use your program just like you would normally (with any arguments). Interactive usage is supported as well.

After your program finishes running (or you `ctrl^C` it), `tokmon` will automatically generate a cost report that looks like this:

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

- You can run multiple instances of `tokmon` simultaenously. Each invocation will generate a separate usage report.

## Install from source
1. Clone the repository and `cd` to the project root.
2. Install the package and its dependencies using `pip install .`
3. You're ready to use `tokmon` (sourcing your terminal might be required).

To uninstall, run `pip uninstall tokmon`<br>
Tip: make sure that the expected python Library route is in your `PATH`.

## How it works
`tokmon` uses the [mitmproxy library](https://github.com/mitmproxy/mitmproxy) to intercept HTTP requests and responses between your program and the OpenAI API.
It then processes the request and response data to calculate token usage and cost based on [tokmon/pricing.json](tokmon/pricing.json).

In most cases, `tokmon` relies on the `usage` field in OpenAI's API respones for token counts. For streaming requests, however, `tokmon` uses OpenAI's [tiktoken library](https://github.com/openai/tiktoken) directly to count the tokens. As of writing OpenAI's API does not return usage data for streaming requests ([reference](https://community.openai.com/t/usage-info-in-api-responses/18862/11).)

## pricing.json
The pricing data was extracted from OpenAI's website with the help of ChatGPT.

`tokmon` is using [tokmon/pricing.json](tokmon/pricing.json) from its package. 

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

You can override the default pricing with: `tokmon --pricing /path/to/your/custom_pricing.json ...`

> This pricing JSON is incomplete (missing DALL-E, etc.), it may be incorrect, and it may go out of date.

> For best results, make sure to check that you have the latest pricing.

## Current Limitations
1. Event streaming: `tokmon` buffers Server-Sent Events (SSE) until the `data: [DONE]` chunk is received. If the monitored program leverages event streaming, its behavior will be modified.
    - Status: looking into it. Pull requests welcome.
2. If your monitored program makes calls to more than 1 type of OpenAI models, your accounting will be incorrect (e.g. both gpt-3.5-turbo and gpt-4 at the same program.)
    - Status: it's on the list.

## Contributing
If you'd like to contribute to the project, please follow these steps:
1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and test them.
4. Submit a pull request with a clear description of your changes and any relevant information.

## Warning
1. `tokmon` comes without any warranty or guarantee whatsoever.
2. `tokmon` was tested on macOS only.
3. This tool may not work as intended, have unknown side effects, may output incorrect information, or not work at all.
4. The pricing data in `pricing.json` may go out of date.
