import asyncio
import os
import json
import subprocess
import typing
import time

import tiktoken

from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster

from costcalculator import CostCalculator

PORT = 7878

class TokenMonitor:
    def __init__(self, target_url, pricing, program_name, *args, verbose=False):
        self.mitm = None
        self.target_url = target_url
        self.program_name = program_name
        self.args = args
        self.pricing = pricing
        self.process = None
        self.usage_data = {program_name: {}}
        self.using_stream = False
        self.tokenizer = None
        self.model = {} # { program_name: model}
        self.verbose = verbose

    # def responseheaders(self, flow: http.HTTPFlow):
    #     if self.target_url in flow.request.pretty_url:
    #         content_type = flow.response.headers.get("Content-Type", "")
    #         if "text/event-stream" in content_type:
    #             flow.response.stream = True

    def request(self, flow: http.HTTPFlow):
        self.handle_request(flow)

    def response(self, flow: http.HTTPFlow):
        self.handle_response(flow)
            
    def handle_request(self, flow: http.HTTPFlow):
        if self.target_url in flow.request.pretty_url:
            try:
                request_data = json.loads(flow.request.content)
                if self.verbose:
                    print(request_data)
                self.model[self.program_name] = request_data["model"]
                self.using_stream = request_data["stream"]

                if self.using_stream:
                    self.init_tokenizer_if_needed(self.model[self.program_name])
                    self.accumulate_stream_request_tokens(request_data)

            except json.JSONDecodeError:
                print("Failed to parse request data as JSON")

    def handle_response(self, flow: http.HTTPFlow):
        if not flow.request.url.startswith(self.target_url):
            return
    
        if flow.response.text:
            if self.using_stream:
                self.accumulate_stream_response_tokens(flow.response.text)
            else:    
                response_data = json.loads(flow.response.text)
                self.usage_data[self.program_name] = response_data["usage"]
        else:
            raise Exception("No response data")

    async def run_monitored_program(self):
        env = os.environ.copy()

        # mitproxy automatically generates a CA cert and stores it in ~/.mitmproxy ...
        mitmproxy_path = os.path.expanduser("~/.mitmproxy")
        mitmproxy_abs_path = os.path.abspath(mitmproxy_path)
        # ... but this coroutine might be called before mitmproxy has had a chance to generate the cert ... ¯\_(ツ)_/¯.
        timeout_seconds = 2
        start = time.time()
        while not os.path.exists(mitmproxy_abs_path):
            await asyncio.sleep(0.1) # yield to other coroutines
            if time.time() - start > timeout_seconds:
                raise Exception("\n\n*** Error: Cert file wasn't created in time. Try to run `mitmproxy` manually first, and then try running tokmon again.\n\n")

        ca_cert_file = "mitmproxy-ca-cert.pem"
        ca_cert_abs_path = os.path.join(mitmproxy_abs_path, ca_cert_file)

        env["REQUESTS_CA_BUNDLE"] = ca_cert_abs_path
        env["HTTP_PROXY"] = f"http://localhost:{PORT}"
        env["HTTPS_PROXY"] = f"http://localhost:{PORT}"
            
        self.process = subprocess.Popen([self.program_name] + [arg for arg in self.args], env=env)
    
    def init_tokenizer_if_needed(self, model):
        """
        Learn more: https://github.com/openai/tiktoken
        """
        if self.tokenizer is None:
            self.tokenizer = tiktoken.encoding_for_model(model)
            if self.verbose:
                print(f"Initialized tokenizer for model {model}. Tokenizer: {self.tokenizer}")
            assert self.tokenizer.decode(self.tokenizer.encode("hello world")) == "hello world"

    def accumulate_stream_request_tokens(self, request_data):
        """
        Accumulate request costs for streaming requests.
        """
        assert self.using_stream
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
        if self.verbose:
            print(f"Accumulating {tokens} tokens for prompt")
        self.usage_data[self.program_name]["prompt_tokens"] = tokens

    def accumulate_stream_response_tokens(self, raw_messages: typing.List[str]):
        """
        When streaming, OpenAI's API doesn't return usage data.
        To work around this, we use tiktoken directly.

        See: https://community.openai.com/t/usage-info-in-api-responses/18862/11
        """
        
        model = None

        completion_tokens = 0

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
                            completion_tokens += len(encoded_tokens)

                except json.JSONDecodeError as e:
                    print(f"\n\n ! ! Failed to parse response data as JSON {e} --- <{msg}> ! !\n\n")
                except Exception as e:
                    print(f"\n\n ! ! Failed to parse response data: {e} ! !\n\n")
                    raise e
        
        assert "prompt_tokens" in self.usage_data[self.program_name]
        prompt_tokens = self.usage_data[self.program_name]["prompt_tokens"]
        total_tokens = prompt_tokens + completion_tokens
        
        self.usage_data[self.program_name]["completion_tokens"] = completion_tokens
        self.usage_data[self.program_name]["total_tokens"] = total_tokens

    def token_usage(self, program_name):
        """
        Returns the model and usage data for the given program name.
        """
        if program_name not in self.usage_data:
            raise Exception(f"Program {program_name} not found in usage data")
        return self.model[self.program_name], self.usage_data[program_name]
    
    async def start_monitoring(self):        
        opts = options.Options(listen_host='0.0.0.0', listen_port=PORT)
        self.mitm = DumpMaster(opts, with_termlog=False, with_dumper=False)
        self.mitm.addons.add(self)

        async def run_mitmproxy():
            try:
                await self.mitm.run()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(e)
            finally:
                self.stop_monitoring()

        async def wait_subprocess():
            await self.run_monitored_program()
            while self.process.poll() is None:
                await asyncio.sleep(1)
            self.stop_monitoring()

        await asyncio.gather(run_mitmproxy(), wait_subprocess())
    
    def stop_monitoring(self):
        self.process.terminate()
        self.mitm.shutdown()

    def calculate_usage(self):
        costCalculator = CostCalculator(self.pricing)
        model, usage_data = self.token_usage(self.program_name)
        total_cost = costCalculator.calculate_cost(model, usage_data)
        return model, usage_data, total_cost
