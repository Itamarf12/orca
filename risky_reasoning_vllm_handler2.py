import time
import starlette
from ray import serve
import logging
import ray
import vllm
from outlines import models
from transformers import AutoTokenizer, AutoModelForCausalLM

# import re
# from typing import List
# from enum import Enum
# from pydantic import BaseModel, constr, conint
# import outlines
# import time



ray_serve_logger = logging.getLogger("ray.serve")
ray_serve_logger.setLevel(logging.DEBUG)
MODEL_NM = "microsoft/Orca-2-13b"
DEVICE = 'auto' # 'cpu'


@ray.remote
class Actor:
    async def heavy_compute(self):
        # taking a long time...
        # await asyncio.sleep(5)
        return

@serve.deployment()
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.warning(f"1111111111111")
        self.actor = Actor.remote()

    def translate(self, text: str) -> str:
        return "bbbbbbbbbbbb"

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()
        NUM_TASKS = 1000
        result_refs = []
        # When NUM_TASKS is large enough, this will eventually OOM.
        for _ in range(NUM_TASKS):
            result_refs.append(self.actor.heavy_compute.remote())
        ray.get(result_refs)
        ray_serve_logger.warning(f"Missing title or description field in the json request")
        time.sleep(10)
        return f"hellooooooo1 "

# @serve.deployment
# class RiskyReasoning:
#     def __init__(self):
#         # Create a remote actor instance
#         self.actor = HeavyComputeActor.remote()
#
#     async def __call__(self, request: starlette.requests.Request):
#         # Get input data from the request
#         data = await request.json()
#
#         # Submit work to the remote actor
#         result_ref = self.actor.heavy_compute.remote(data["title"])
#
#         # Get the result (will block until result is ready)
#         result = await ray.get(result_ref)
#
#         return result



app = RiskyReasoning.bind()


