import unittest
from tokmon.tokmon import TokenMonitor

class TestTokenMonitor(unittest.TestCase):

    def setUp(self):
        self.target_url = "https://api.openai.com"
        self.pricing = {
            "gpt-4": {
                "prompt_cost": 0.03,
                "completion_cost": 0.06,
                "per_tokens": 1000
            }
        }
        self.program_name = "my_gpt_program"
        self.args = ["--my_arg", "hi"]
        self.tokmon = TokenMonitor(self.target_url, self.pricing, self.program_name, *self.args)

    def test_init(self):
        self.assertEqual(self.tokmon.target_url, self.target_url)
        self.assertEqual(self.tokmon.program_name, self.program_name)
        self.assertEqual(self.tokmon.args, tuple(self.args))
        self.assertEqual(self.tokmon.pricing, self.pricing)

    # More tests are needed
    # examples:
    #     - feed a request to handle_request and check that the usage_data is updated as expected
    #     - feed a response to handle_response and check that the usage_data is updated as expected
    #     - same as the above but for streaming

    # ...

if __name__ == "__main__":
    unittest.main()
