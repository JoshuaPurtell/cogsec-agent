from typing import Dict, List, Type
from openai import AsyncOpenAI
import asyncio
from pydantic import BaseModel
from src.lms.caching import (
    cache,
    generate_cache_key,
    generate_cache_key_with_response_model,
)

import instructor

#)
client = instructor.patch(AsyncOpenAI(
))

async def hit_oai_with_model(
    messages: List[Dict],
    response_model: Type[BaseModel],
    model: str,
    temperature,
    max_tokens,
):
    r = await client.chat.completions.create(
        model=model,
        response_model=response_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return r

async def async_openai_chat_completion(
    messages: List[Dict],
    model: str = "gpt-3.5-turbo-0125",
    temperature=0.0,
    max_tokens=150,
) -> BaseModel:
    key = generate_cache_key(messages, model)
    if key in cache:
        return cache[key]
    output = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    cache[key] = output.choices[0].message.content
    return output.choices[0].message.content

async def async_openai_chat_completion_with_response_model(
    messages: List[Dict],
    model: str = "gpt-3.5-turbo-0125",
    response_model: Type[BaseModel] = None,
    temperature=0.0,
    max_tokens=150,
) -> BaseModel:
    key = generate_cache_key_with_response_model(messages, model, response_model)
    if key in cache:
        return response_model.parse_raw(cache[key])
    output = await hit_oai_with_model(messages, response_model, model, temperature, max_tokens)
    cache[key] = output.json()
    return response_model.parse_raw(cache[key])