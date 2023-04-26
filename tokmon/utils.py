import socket

from typing import Callable, List, Any

def find_available_port(start_port: int):
    """
    To allow multiple instances of tokmon to run concurrently.
    """
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1

def count_tokens_in_json(encode_fn: Callable[[str], List[str]], data: Any) -> int:
    token_count = 0
    stack = [data]

    while stack:
        current = stack.pop()

        if isinstance(current, dict):
            for key, value in current.items(): # 'key' is unused
                # empricially, the keys seem to not be counted towards the token count
                # so we are not including this `token_count += count_tokens(key)`
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            token_count += len(encode_fn(current))
        else:
            token_count += len(encode_fn( str(current) ) )

    return token_count