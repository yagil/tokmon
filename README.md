# `tokmon`
#### `tokmon` monitors the OpenAI API costs of a particular run of a program that uses the OpenAI API.

# Demo
...

# Usage
Use `tokmon` like you would use the `time` utlity to measure exeuction time.

```bash
# $ tokmon <program_to_monitor> [arguments...]
$ tokmon ./gpt_count_to_10.py
# ... when gpt_count_to_10.py finishes running...
$ Total cost for ./venv/bin/python ('gpt_count_to_10.py') was $0.00147
```

# Setup
```
...
```

# Options
```bash
usage: cli.py [-h] [--pricing-data COST_DATA_JSON] program_name ...

A utility to monitor OpenAI token cost.

positional arguments:
  program_name          The name of the monitored program
  args                  The command and arguments to run the monitored program

optional arguments:
  -h, --help            show this help message and exit
  --pricing-data COST_DATA_JSON
                        JSON string of cost data, e.g.: {"gpt-4-0314": {"cost": 0.03, "per_tokens":1000}}
```

# How it works
```
...
```

# Warning
...