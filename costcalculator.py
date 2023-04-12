from typing import Dict

class CostCalculator:
    def __init__(self, pricing_data: Dict[str, Dict[str, float]]):
        self.pricing_data = pricing_data

    def calculate_cost_for_tokens(self, tokens, price, per_tokens):
        return (float(tokens) / per_tokens) * price
        
    def calculate_cost(self, model, usage_data):        
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
            cost = model_pricing_data["cost"]
            total_cost = self.calculate_cost_for_tokens(total_tokens, cost, per_tokens)

        return total_cost