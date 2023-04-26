from enum import Enum
from typing import Dict
import requests

CHAT_EXCHANGE_API_ENDPOINT = "api/exchange"
USAGE_SUMMARY_API_ENDPOINT = "api/summary"

class BeamClient(object):
    def __init__(self, remote_url: str, verbose: bool = False) -> None:
        self.remote_url = remote_url
        self.verbose = verbose

    def get_summary_for_transport(self, monitored_program:str, summary: Dict) -> Dict:
        """
        Get Summary for Transport

        Get the summary JSON object for transport to the remote server.

        Args:
            monitored_program (str): The monitored program invocation
            summary (Dict): The usage summary JSON object

        Returns:
            Dict: The summary JSON object for transport to the remote server
        """
        return {
            "tokmon_conversation_id": summary["tokmon_conversation_id"],
            "monitored_program": monitored_program,
            "total_cost": summary["total_cost"],
            "total_usage": summary["total_usage"],
            "pricing_data": summary["pricing_data"],
            "models": summary["models"]
        }

    def send_rt_blob(self, monitored_program:str, conversation_id: str, request: Dict, response: Dict, summary: Dict) -> None:
        """
        Send Round-Trip Blob

        Send a request-response pair to the remote server.

        Args:
            monitored_program (str): The monitored program invocation
            conversation_id (str): The conversation ID
            request (Dict): The request JSON object
            response (Dict): The response JSON object
            summary (Dict): The usage summary up to this point JSON object

        Returns:
            None
        """
        json_payload = {
            "tokmon_conversation_id": conversation_id,
            "request": request,
            "response": response,
            "summary": self.get_summary_for_transport(monitored_program, summary)
        }

        remote_url = self.remote_url[:-1] if self.remote_url.endswith("/") else self.remote_url
        path = f"{remote_url}/{CHAT_EXCHANGE_API_ENDPOINT}"

        # Send the JSON object to the remote server
        try:
            res = requests.post(path, json=json_payload)
            if self.verbose:
                print(f"Beaming to {path}: {res.status_code}")
            if res.status_code != 200:
                raise Exception(f"Failed to beam to {path}: {res.status_code}")
        except Exception as e:
            if self.verbose:
                print(f"Error beaming to {path}: {str(e)}")
            raise e
        
    def send_summary_blob(self, monitored_program:str, summary: Dict) -> None:
        """
        Send Summary Blob
        
        Send the final usage summary to the remote server.
        
        Args:
            monitored_program (str): The monitored program invocation
            summary (Dict): The usage summary JSON object
            
            Returns:
                None
                
        """
        summary_for_transport = self.get_summary_for_transport(monitored_program, summary)

        json_payload = {
            "summary": summary_for_transport
        }

        remote_url = self.remote_url[:-1] if self.remote_url.endswith("/") else self.remote_url
        path = f"{remote_url}/{USAGE_SUMMARY_API_ENDPOINT}"

        # Send the JSON object to the remote server
        try:
            res = requests.post(path, json=json_payload)
            if self.verbose:
                print(f"Beaming to {path}: {res.status_code}")
            if res.status_code != 200:
                raise Exception(f"Failed to beam to {path}: {res.status_code}")
        except Exception as e:
            if self.verbose:
                print(f"Error beaming to {path}: {str(e)}")
            raise e