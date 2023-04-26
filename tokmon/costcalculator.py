from typing import List, Tuple, Dict

class CostCalculator:
    def __init__(self, pricing_data: Dict[str, Dict[str, float]]) -> None:
        self.pricing_data = pricing_data

    def calculate_cost_for_tokens(self, tokens, price, per_tokens):
        return (float(tokens) / per_tokens) * price

    def calculate_round_trip_cost(self, request: Dict, response: Dict):
        """
        Calculate cost & usage for a single round trip (request -> response)
        """
        model = response["model"]
        usage_data = response["usage"]
        
        prompt_tokens = usage_data["prompt_tokens"]
        completion_tokens = usage_data["completion_tokens"]
        total_tokens = usage_data["total_tokens"]
        assert total_tokens == prompt_tokens + completion_tokens, "Total tokens does not match prompt + completion tokens"

        # prepare pricing data
        model_pricing_data = self.pricing_data[model]
        per_tokens = model_pricing_data["per_tokens"]

        if "prompt_cost" in model_pricing_data:
            """Model differentiates between prompt and completion costs"""
            prompt_price = model_pricing_data["prompt_cost"]
            completion_price = model_pricing_data["completion_cost"]

            prompt_cost = self.calculate_cost_for_tokens(prompt_tokens, prompt_price, per_tokens)
            completion_cost = self.calculate_cost_for_tokens(completion_tokens, completion_price, per_tokens)
            total_cost = prompt_cost + completion_cost
        else:
            """Model has a single cost for all tokens"""
            price = model_pricing_data["cost"]
            total_cost = self.calculate_cost_for_tokens(total_tokens, price, per_tokens)

        messages = request["messages"] + response["messages"]

        cost_summary = {
            "model": model,
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens },
            "cost": total_cost,
            "messages": messages
        }
        
        return model_pricing_data, cost_summary

    def calculate_cost(self, conversation_id: str, usage_data: List[Tuple[Dict, Dict]]):
        """
        Calculate cost & usage for all of (request, response) pairs, return a summary
        """
        total_cost = 0.0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        pricing_data = {}
        models = set()
        raw_data = []

        for request, response in usage_data:
            model_pricing, round_trip_cost = self.calculate_round_trip_cost(request, response)
            usage = round_trip_cost["usage"]
            total_prompt_tokens += usage["prompt_tokens"]
            total_completion_tokens += usage["completion_tokens"]
            total_tokens += usage["total_tokens"]
            total_cost += round_trip_cost["cost"]
            model = round_trip_cost["model"]
            models.add(model)
            pricing_data[model] = model_pricing
            raw_data.append(round_trip_cost)

        return {
            "tokmon_conversation_id": conversation_id,
            "total_cost": total_cost,
            "total_usage": {
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens,
            },
            "pricing_data": str(pricing_data),
            "models": list(models),
            "raw_data": raw_data
        }