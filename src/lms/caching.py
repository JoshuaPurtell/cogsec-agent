import hashlib
from typing import Dict, List, Type

from diskcache import Cache
from pydantic import BaseModel

# Create a cache object
cache = Cache(directory="temp/cache")


def generate_cache_key(messages: List[Dict], model: str) -> str:
    key = "".join([msg["content"] for msg in messages]) + model
    return hashlib.sha256(key.encode()).hexdigest()


def generate_cache_key_with_response_model(
    messages: List[Dict], model: str, response_model: Type[BaseModel]
) -> str:
    key = (
        "".join([msg["content"] for msg in messages])
        + model
        + str(response_model.schema())
    )
    return hashlib.sha256(key.encode()).hexdigest()