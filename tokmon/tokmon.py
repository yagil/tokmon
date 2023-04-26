import asyncio
import os
import json
import subprocess
import typing
import time
import uuid
from typing import List, Tuple, Dict, Callable, TypeVar, Optional

import tiktoken
from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster

from tokmon.utils import find_available_port, count_tokens_in_json

PORT = find_available_port(7878)

RequestResponseHandler = Callable[[str, Dict, Dict], None]

class TokenMonitor:
    def __init__(self,
                 target_url: str,
                 program_name: str,
                 *args: tuple,
                 verbose:bool = False,
                 req_res_handler: RequestResponseHandler = None
                ):
        self.mitm: Optional[DumpMaster] = None
        self.target_url = target_url
        self.program_name = program_name
        self.args = args
        self.process = None
        self.using_stream = False
        self.verbose = verbose
        self.history: List[Tuple[Dict, Dict]] = []
        self.current_request = None
        self.req_res_handler = req_res_handler
        self.conversation_id = str(uuid.uuid4())

    # Issue: https://github.com/yagil/tokmon/issues/4
    # 
    # def responseheaders(self, flow: http.HTTPFlow):
    #     if self.target_url in flow.request.pretty_url:
    #         content_type = flow.response.headers.get("Content-Type", "")
    #         if "text/event-stream" in content_type:
    #             flow.response.stream = True

    def request(self, flow: http.HTTPFlow):
        self.handle_request(flow)

    def response(self, flow: http.HTTPFlow):
        self.handle_response(flow)

    def append_history(self, request: Dict, response: Dict):
        self.history.append((request, response))
            
    def handle_request(self, flow: http.HTTPFlow):
        if self.target_url not in flow.request.pretty_url:
            return
        
        try:
            if self.current_request is not None:
                print("Warning: multiple requests in flight. This is not supported.")
            
            if flow.request.content is None:
                raise Exception("No request data")
            
            request_data = json.loads(flow.request.content)
            self.current_request = request_data

            if self.verbose:
                print(request_data)
            
            self.using_stream = request_data["stream"] if "stream" in request_data else False

        except json.JSONDecodeError:
            print("Failed to parse request data as JSON")

        except Exception as e:
            print(f"Error handling request: {str(e)}")

    def handle_response(self, flow: http.HTTPFlow):
        if not flow.request.url.startswith(self.target_url):
            return
    
        model = ""
        content = ""
        usage = None

        if flow.response and flow.response.text is not None:
            if self.using_stream:
                model, content, usage = self.handle_stream_response(flow.response.text)
            else:    
                response_data = json.loads(flow.response.text)
                model = response_data["model"]
                content = response_data["choices"][0]["message"]["content"]
                usage = response_data["usage"]
        else:
            raise Exception("No response data")
        
        request = self.current_request
        response = {
            "model": model,
            "messages": [{"role": "assistant", "content": content}],
            "usage": usage
        }

        # Add the request and response to the rolling history
        self.append_history(request, response)

        # Invoke the delegate callback for additional handling on the response object
        if self.req_res_handler is not None:
            self.req_res_handler(self.conversation_id, request, response)

        self.current_request = None

        if self.verbose:
            print(response)

    async def run_monitored_program(self) -> bool:
        env = os.environ.copy()

        # mitproxy automatically generates a CA cert and stores it in ~/.mitmproxy ...
        # ... but this coroutine might be called before mitmproxy has had a chance to generate the cert ... ¯\_(ツ)_/¯.
        mitmproxy_path = os.path.expanduser("~/.mitmproxy")
        mitmproxy_abs_path = os.path.abspath(mitmproxy_path)
        timeout_seconds = 2
        start = time.time()
        while not os.path.exists(mitmproxy_abs_path):
            await asyncio.sleep(0.1) # yield to other coroutines
            if time.time() - start > timeout_seconds:
                raise Exception("\n\n*** Error: Cert file wasn't created in time. Try to run `mitmproxy` manually first, and then try running tokmon again.\n\n")

        ca_cert_file = "mitmproxy-ca-cert.pem"
        ca_cert_abs_path = os.path.join(mitmproxy_abs_path, ca_cert_file)

        # set the HTTP proxy environment variables
        env["HTTP_PROXY"] = f"http://localhost:{PORT}"
        env["HTTPS_PROXY"] = f"http://localhost:{PORT}"

        # Add `mitmproxy`'s CA cert to the environment variables of the monitored program
        env["REQUESTS_CA_BUNDLE"] = ca_cert_abs_path # for monitored programs using Python's Requests Library
        env["NODE_EXTRA_CA_CERTS"] = ca_cert_abs_path # for monitored programs using Node.js
        
        # Support for manually adding `mitmproxy`'s CA cert in the monitored program
        env["TOKMON_SSL_CERT_FILE"] = ca_cert_abs_path

        if self.program_name == 'curl':
            print()
            args = ['--cacert', ca_cert_abs_path] + [arg for arg in self.args]
        else:
            args = [arg for arg in self.args]

        try:
            self.process = subprocess.Popen([self.program_name] + args, env=env)
            return True
        except FileNotFoundError:
            print(f"[tokmon] Error: Program not found '{self.program_name}'. Did you type its path and name correctly?")
        except Exception as e:
            print(e)
            
        return False
    
    def encode(self, model, text):
        """
        Learn more: https://github.com/openai/tiktoken
        """
        tokenizer = tiktoken.encoding_for_model(model)
        return tokenizer.encode(text)

    def handle_stream_response(self, raw_messages: typing.List[str]):
        """
        When streaming, OpenAI's API doesn't return usage data.
        To work around this, we use tiktoken directly.

        See: https://community.openai.com/t/usage-info-in-api-responses/18862/11
        """
        
        assert self.current_request is not None

        model = None

        completion_tokens = 0
        completion_content = ""

        # mitmproxy buffers the returned SSE chunks as one big string
        for msg in raw_messages.split("\n"):
            if msg.startswith("data:"):
                try:
                    msg = msg[5:]
                    if "".join(msg.split()) == "[DONE]":
                        break
                    msg = json.loads(msg)
                    model = msg["model"]
                    
                    choice = msg["choices"][0]
                    if "delta" in choice:
                        if "content" in choice["delta"]:
                            tokens = choice["delta"]["content"]
                            completion_content += tokens
                            encoded_tokens = self.encode(model, tokens)
                            completion_tokens += len(encoded_tokens)

                except json.JSONDecodeError as e:
                    print(f"\n\n ! ! Failed to parse response data as JSON {e} --- <{msg}> ! !\n\n")
                except Exception as e:
                    print(f"\n\n ! ! Failed to parse response data: {e} ! !\n\n")
                    raise e
        
        encode_lambda = lambda text: self.encode(model, text)
        prompt_tokens = count_tokens_in_json(encode_lambda, self.current_request)
        total_tokens = prompt_tokens + completion_tokens
        
        # mimic the usage data returned by the API in the non streaming case
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
        return model, completion_content, usage
    
    async def start_monitoring(self):        
        opts = options.Options(listen_host='0.0.0.0', listen_port=PORT)
        if self.verbose:
            print(f"Starting mitmproxy on port {PORT}...")
        self.mitm = DumpMaster(opts, with_termlog=False, with_dumper=False)
        self.mitm.addons.add(self)

        async def run_mitmproxy():
            try:
                await self.mitm.run()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"Exception while running mitmproxy: {e}")
            finally:
                self.stop_monitoring()

        async def wait_subprocess():
            success = await self.run_monitored_program()
            if success:   
                while self.process.poll() is None:
                    await asyncio.sleep(1)
            self.stop_monitoring()

        await asyncio.gather(run_mitmproxy(), wait_subprocess())
    
    def stop_monitoring(self):
        if self.process:
            self.process.terminate()
        self.mitm.shutdown()

    def usage_summary(self):
        return self.conversation_id, self.history
