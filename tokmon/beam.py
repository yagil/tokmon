from enum import Enum
from typing import Dict
import requests

class BeamType(Enum):
    """ Beam the summary JSON object """
    SUMMARY = "summary"
    """ Beam every request-response pair """
    REQRES = "reqres"

class BeamClient(object):
    def __init__(self, remote_url: str, beam_type: BeamType, verbose: bool = False):
        self.remote_url = remote_url
        self.beam_type = beam_type
        self.verbose = verbose

    def beam(self, conversation_id: str, request: Dict, response: Dict):
        # Create the JSON object from the request and response
        json_payload = {
            "tokmon_conversation_id": conversation_id,
            "request": request,
            "response": response
        }

        # Send the JSON object to the remote server
        try:
            response = requests.post(self.remote_url, json=json_payload)
            if self.verbose:
                print(f"Beaming to {self.remote_url}: {response.status_code}")
            if response.status_code != 200:
                raise Exception(f"Failed to beam to {self.remote_url}: {response.status_code}")
        except Exception as e:
            if self.verbose:
                print(f"Error beaming to {self.remote_url}: {str(e)}")
            raise e
        
    def beam_summary(self, summary: Dict):
        
        summary_for_transport = None
        
        if self.beam_type == BeamType.SUMMARY:
            summary_for_transport = summary
        else:    
            summary_for_transport = {
                "tokmon_conversation_id": summary["tokmon_conversation_id"],
                "total_cost": summary["total_cost"],
                "total_usage": summary["total_usage"],
                "pricing_data": summary["pricing_data"],
                "models": summary["models"]
            }

        json_payload = {
            "summary": summary_for_transport
        }

        # Send the JSON object to the remote server
        try:
            response = requests.post(self.remote_url, json=json_payload)
            if self.verbose:
                print(f"Beaming to {self.remote_url}: {response.status_code}")
            if response.status_code != 200:
                raise Exception(f"Failed to beam to {self.remote_url}: {response.status_code}")
        except Exception as e:
            if self.verbose:
                print(f"Error beaming to {self.remote_url}: {str(e)}")
            raise e