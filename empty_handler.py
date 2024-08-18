import time
import starlette
from ray import serve
import logging
import ray

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
        #pending_requests = ray.serve.context.get_serve_handle_stats().get("RiskyFeatures", {}).get("pending_requests",
        #                                                                                           0)
        #ray_serve_logger.warning(f"pending_requests  {pending_requests}")
        deployments = serve.get_replica_context()



        ray_serve_logger.warning(f"Missing title or description field in the json request = {deployments}")
        time.sleep(10)
        return f"hellooooooo "



app = RiskyReasoning.bind()


