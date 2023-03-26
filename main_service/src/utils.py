from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlencode


def is_valid(*, query: dict, secret: str) -> bool:
    """Check VK Apps signature"""
    vk_subset = OrderedDict(
        sorted(x for x in query.items() if x[0][:3] == "vk_"))
    hash_code = b64encode(HMAC(secret.encode(), urlencode(
        vk_subset, doseq=True).encode(), sha256).digest())
    decoded_hash_code = hash_code.decode(
        'utf-8')[:-1].replace('+', '-').replace('/', '_')
    return query["sign"] == decoded_hash_code


def parse_query_string(query_string):
    res = dict([pair.split("=") for pair in query_string.split("&")])
    res["vk_user_id"] = int(res["vk_user_id"])
    return res
