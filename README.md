# 🔤🧐 `tokmon` - CLI utility to monitor OpenAI API costs

`tokmon` is a command-line utility that helps you monitor the token costs of your OpenAI API calls during development.

You use `tokmon` just like you would use the `time` utility, but instead of execution time you get token usage and cost.

## How to use `tokmon`

> **Warning**
> This is a debugging and development tool. It is not intended to be used in any setting that matters. Use your best judgement, your on your own!

Prepend `tokmon` to your normal program execution like so:
```bash
$ tokmon ./my_gpt_program --my_arg "hi"
```
After this, use your program just like you would normally (interactive usage is supported as well).

After `./my_gpt_program` finishes running or `ctrl^C` is pressed, `tokmon` will automatically generate a cost report that looks like this:

```bash
================================================================================
Monitored invocation: ['./my_gpt_program', '--my_arg', 'hi']
Model: gpt-4
Usage: {'prompt_tokens': 74, 'completion_tokens': 13, 'total_tokens': 87}
Pricing: {'prompt_cost': 0.03, 'completion_cost': 0.06, 'per_tokens': 1000}
Cost: $0.003000
================================================================================
```

## Setup
1. Clone the repository and navigate to the project directory.
2. Install the package and its dependencies using `pip install .`.
3. Run `tokmon` with your desired program and arguments (you may need to source your `.zshrc` / `.bashrc` file first).

## How it works
`tokmon` uses the [mitmproxy library](https://github.com/mitmproxy/mitmproxy) to intercept HTTP requests and responses between your program and the OpenAI API. It then processes the request and response data to calculate token usage and cost based on the provided pricing information (see [pricing.json](pricing.json) in this repo).

In most cases, `tokmon` relies on the `usage` field in OpenAI API respones in order to count token. For streaming requests, however, `tokmon` uses the OpenAI's [tiktoken library](https://github.com/openai/tiktoken) directly: as of writing OpenAI's API does not return usage data for streaming requests ([reference](https://community.openai.com/t/usage-info-in-api-responses/18862/11).)

## Current Limitations
1. Event streaming: `tokmon` will override this setting and buffer Server-Sent Events (SSE) data chunks until the `data: [DONE]` chunk is received. If the monitored program leverages event streaming, its behavior will be modified.
    - Status: looking into it. Pull requests welcome.

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
