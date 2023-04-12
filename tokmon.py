import asyncio
import os
import json
import subprocess
import io
import typing

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
            
    def run(self, program_name, args):
        env = os.environ.copy()
        env["HTTP_PROXY"] = f"http://localhost:{PORT}"
        env["HTTPS_PROXY"] = f"http://localhost:{PORT}"
        env["REQUESTS_CA_BUNDLE"] = os.path.abspath("mitmproxy-ca-cert.pem")

        self.process = subprocess.Popen([program_name] + [arg for arg in args], env=env)

    def calculate_cost(self, response_data):
        cost = 0

        model = response_data["model"]
        usage = response_data["usage"]

        if model not in self.pricing:
            print(f"Model {model} not found in pricing data.  Skipping...")
            raise Exception("Model not found in pricing data")
        
        price = self.pricing[model]["cost"]
        per_tokens = self.pricing[model]["per_tokens"]

        prompt_tokens = usage["prompt_tokens"] # unused
        completion_tokens = usage["completion_tokens"] # unused
        total_tokens = usage["total_tokens"]

        # for now just use the total token count
        cost = (float(total_tokens) / per_tokens) * price

        return cost
    
    def total_cost(self, program_name):
        if program_name in self.cost_data:
            return self.cost_data[program_name]["cost"]
        return 0
    
    def handle_request(self, flow: http.HTTPFlow):
        if self.target_url in flow.request.pretty_url:
            try:
                request_data = json.loads(flow.request.content)
                # TODO: Implement?
                print(f"Request data: {request_data}")
            except json.JSONDecodeError:
                print("Failed to parse request data as JSON")

    def handle_streamed_responses(self, raw_messages: typing.List[str]):
        print("""
        
        tokmon doesn't support streaming responses yet.  See this:

        Bug: https://community.openai.com/t/usage-info-in-api-responses/18862/11

        > hallacy (OpenAI Staff)
        > Dec '22
        > The feature wasn’t enabled in streaming by default because we found that it could breaking existing integrations.
        > It does exist though! If you would like it turned on, send us a message at help.openai.com

        """)
        for msg in raw_messages.split("\n"):
            pass 
                                
    def handle_response(self, flow: http.HTTPFlow):
        if not flow.request.url.startswith(self.target_url):
            return

        dataWasStreamed = False
        content_type = flow.response.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            dataWasStreamed = True
    
        if flow.response.text:
            if dataWasStreamed:
                self.handle_streamed_responses(flow.response.text)
            else:    
                response_data = json.loads(flow.response.text)
                cost = self.calculate_cost(response_data)
                if self.program_name in self.cost_data:
                    self.cost_data[self.program_name]["cost"] += cost
                else:
                    self.cost_data[self.program_name] = {"cost": cost}

def run_mitmproxy(m):
    try:
        m.run()
    except KeyboardInterrupt:
        m.shutdown()

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

    async def wait_subprocess():
        while constMonitor.process.poll() is None:
            await asyncio.sleep(1)
        total_cost = constMonitor.total_cost(program_name)
        print(f"Total cost for {program_name} {args} was ${total_cost}")
        m.shutdown()

    if daemon:
        while True:
            await asyncio.sleep(1)
    else:
        await asyncio.gather(run_mitmproxy(), wait_subprocess())

def query_cost_data(program_name):
    pass
