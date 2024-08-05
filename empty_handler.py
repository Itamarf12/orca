import time
import starlette
from ray import serve
import logging

ray_serve_logger = logging.getLogger("ray.serve")

#@serve.deployment(ray_actor_options={"num_cpus": 3})
@serve.deployment()
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.warning(f"1111111111111")

    def translate(self, text: str) -> str:
        return "bbbbbbbbbbbb"

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()
        ray_serve_logger.warning(f"Missing title or description field in the json request = {req}")
        time.sleep(10)
        return "hellooooooo"



app = RiskyReasoning.bind()


