import asyncio
import os
import json
import subprocess
import io
import typing
import tiktoken

from typing import Optional, Dict

from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster

PORT = 7878

class CostInterceptor:
    def __init__(self, target_url, program_name, pricing):
        self.target_url = target_url
        self.program_name = program_name
        self.pricing = pricing
        self.cost_data = {}
        self.is_streaming = False
        self.tokenizer = None # we init this only if is_streaming is True
        self.stream_token_count = {"prompt_tokens": 0, "completion_tokens": 0} # mimic OpenAI's 'usage' dict format

    def responseheaders(self, flow: http.HTTPFlow):
        if self.target_url in flow.request.pretty_url:
            content_type = flow.response.headers.get("Content-Type", "")
            if "text/event-stream" in content_type:
                # Set stream=False to buffer the response
                flow.response.stream = False

    def request(self, flow: http.HTTPFlow):
        self.handle_request(flow)

    def response(self, flow: http.HTTPFlow):
        self.handle_response(flow)
            
    def handle_request(self, flow: http.HTTPFlow):
        if self.target_url in flow.request.pretty_url:
            try:
                request_data = json.loads(flow.request.content)
                print(request_data)
                request_model = request_data["model"]
                self.is_streaming = request_data["stream"]
                print(f"Model used: {request_model}. Streaming: {self.is_streaming}")

                if self.is_streaming:
                    self.init_tokenizer_if_needed(request_model)
                    self.accumulate_request_tokens(request_data)

            except json.JSONDecodeError:
                print("Failed to parse request data as JSON")

    def handle_response(self, flow: http.HTTPFlow):
        if not flow.request.url.startswith(self.target_url):
            return
    
        if flow.response.text:
            if self.is_streaming:
                cost = self.calculate_cost_stream(flow.response.text)
            else:    
                response_data = json.loads(flow.response.text)
                cost = self.calculate_cost(response_data)
        
            if self.program_name in self.cost_data:
                self.cost_data[self.program_name]["cost"] += cost
            else:
                self.cost_data[self.program_name] = {"cost": cost}
        else:
            raise Exception("No response data")
        
    def run(self, program_name, args):
        env = os.environ.copy()
        env["HTTP_PROXY"] = f"http://localhost:{PORT}"
        env["HTTPS_PROXY"] = f"http://localhost:{PORT}"
        env["REQUESTS_CA_BUNDLE"] = os.path.abspath("mitmproxy-ca-cert.pem")

        self.process = subprocess.Popen([program_name] + [arg for arg in args], env=env)

    # cost stuff (todo: move to separate class)
    # ---------------------------------------------------------

    def calculate_cost_for_tokens(self, model, tokens):
        price = self.pricing[model]["cost"]
        per_tokens = self.pricing[model]["per_tokens"]
        print(f"Model {model} price ${price} per {per_tokens} tokens")
        return (float(tokens) / per_tokens) * price
        
    def calculate_cost(self, response_data):
        """
        Calculate the cost based o the response data.
        This works for non-streaming. See `calculate_cost_stream` for streaming.
        """
        cost = 0

        model = response_data["model"]
        usage = response_data["usage"]
        print(usage)

        if model not in self.pricing:
            print(f"Model {model} not found in pricing data.  Skipping...")
            raise Exception("Model not found in pricing data")
        
        prompt_tokens = usage["prompt_tokens"] # unused
        completion_tokens = usage["completion_tokens"] # unused
        total_tokens = usage["total_tokens"]

        return self.calculate_cost_for_tokens(model, total_tokens)
    
    def total_cost(self, program_name):
        if program_name in self.cost_data:
            return self.cost_data[program_name]["cost"]
        return 0

    def accumulate_request_tokens(self, request_data):
        """
        Accumulate request costs for streaming requests.
        """
        assert self.is_streaming
        assert self.tokenizer is not None

        def count_tokens(text):
            return len(self.tokenizer.encode(text))

        def count_tokens_in_json(data):
            token_count = 0
            stack = [data]

            while stack:
                current = stack.pop()

                if isinstance(current, dict):
                    for key, value in current.items():
                        # empricially, the keys seem to not be counted towards the token count
                        # so we are not including this `token_count += count_tokens(key)`
                        stack.append(value)
                elif isinstance(current, list):
                    stack.extend(current)
                elif isinstance(current, str):
                    token_count += count_tokens(current)
                else:
                    token_count += count_tokens(str(current))

            return token_count

        tokens = count_tokens_in_json(request_data)
        print(f"Accumulating {tokens} tokens for prompt")
        self.stream_token_count["prompt_tokens"] += tokens


    def calculate_cost_stream(self, raw_messages: typing.List[str]):
        """
        When streaming, OpenAI's API doesn't return usage data.
        To work around this, we use tiktoken directly.

        See: https://community.openai.com/t/usage-info-in-api-responses/18862/11
        """
        
        model = None

        # mitmproxy buffers the returned SSE chunks as one big string
        for msg in raw_messages.split("\n"):
            if msg.startswith("data:"):
                try:
                    msg = msg[5:]
                    if "".join(msg.split()) == "[DONE]":
                        break
                    msg = json.loads(msg)
                    model = msg["model"]

                    if self.tokenizer is None:
                        self.init_tokenizer_if_needed(model)
                    
                    choice = msg["choices"][0]
                    if "delta" in choice:
                        if "content" in choice["delta"]:
                            tokens = choice["delta"]["content"]
                            encoded_tokens = self.tokenizer.encode(tokens)
                            self.stream_token_count["completion_tokens"] += len(encoded_tokens)

                except json.JSONDecodeError as e:
                    print(f"\n\n ! ! Failed to parse response data as JSON {e} --- <{msg}> ! !\n\n")
                except Exception as e:
                    print(f"\n\n ! ! Failed to parse response data: {e} ! !\n\n")
                    raise e
        
        prompt_tokens = self.stream_token_count["prompt_tokens"]
        completion_tokens = self.stream_token_count["completion_tokens"]
        total_tokens = prompt_tokens + completion_tokens
        
        print(f"< Model: {model}, [prompt tokens: {prompt_tokens}, completion tokens: {completion_tokens}, total tokens: {total_tokens}] >")
        return self.calculate_cost_for_tokens(model, total_tokens)
    
    def init_tokenizer_if_needed(self, model):
        """
        https://github.com/openai/tiktoken
        """
        if self.tokenizer is None:
            self.tokenizer = tiktoken.encoding_for_model(model)
            print(f"Initialized tokenizer for model {model}. Tokenizer: {self.tokenizer}")
            assert self.tokenizer.decode(self.tokenizer.encode("hello world")) == "hello world"
            

def run_mitmproxy(m):
    try:
        m.run()
    except KeyboardInterrupt:
        m.shutdown()
    except Exception as e:
        print(f"Exception while running mitmproxy: {e}")

async def monitor_cost(target_url:str, pricing:Dict, program_name: Optional[str] = None, *args:Optional[tuple], daemon:bool=False):
    opts = options.Options(listen_host='0.0.0.0', listen_port=PORT)
    m = DumpMaster(opts, with_termlog=False, with_dumper=False)

    constMonitor = CostInterceptor(target_url, program_name, pricing)
    m.addons.add(constMonitor)
    
    constMonitor.run(program_name, args)

    async def run_mitmproxy():
        try:
            await m.run()
        except KeyboardInterrupt:
            m.shutdown()
        except Exception as e:
            print(e)
            m.shutdown()

    async def wait_subprocess():
        while constMonitor.process.poll() is None:
            await asyncio.sleep(1)
        total_cost = constMonitor.total_cost(program_name)
        print(f"\nTotal cost for {program_name} {args} was ${total_cost}")
        m.shutdown()

    if daemon:
        while True:
            await asyncio.sleep(1)
    else:
        await asyncio.gather(run_mitmproxy(), wait_subprocess())

def query_cost_data(program_name):
    pass
