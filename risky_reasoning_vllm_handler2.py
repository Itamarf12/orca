import time
import starlette
from ray import serve
import logging
import ray
import vllm
from outlines import models
from transformers import AutoTokenizer, AutoModelForCausalLM

import re
from typing import List
from enum import Enum

from pydantic import BaseModel, constr, conint
import outlines
import time



ray_serve_logger = logging.getLogger("ray.serve")
ray_serve_logger.setLevel(logging.DEBUG)
MODEL_NM = "microsoft/Orca-2-13b"
DEVICE = 'auto' # 'cpu'



@serve.deployment()
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.warning(f"1111111111111")


    def translate(self, text: str) -> str:
        return "bbbbbbbbbbbb"

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()
        return f"hellooooooo12 "


app = RiskyReasoning.bind()


