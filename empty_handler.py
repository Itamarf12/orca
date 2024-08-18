import time
import starlette
from ray import serve
import logging
import ray

ray_serve_logger = logging.getLogger("ray.serve")

#@serve.deployment(ray_actor_options={"num_cpus": 3})


@ray.remote
class HeavyComputeActor:
    def heavy_compute(self, data):
        # Simulate a heavy computation (e.g., 3 seconds of work)
        time.sleep(3)
        return {"result": f"Processed {data}"}


# @serve.deployment()
# class RiskyReasoning:
#     def __init__(self):
#         ray_serve_logger.warning(f"1111111111111")
#
#     def translate(self, text: str) -> str:
#         return "bbbbbbbbbbbb"
#
#     async def __call__(self, request: starlette.requests.Request):
#         req = await request.json()
#         #pending_requests = ray.serve.context.get_serve_handle_stats().get("RiskyFeatures", {}).get("pending_requests",
#         #                                                                                           0)
#         #ray_serve_logger.warning(f"pending_requests  {pending_requests}")
#         deployments = serve.get_replica_context()
#
#
#
#         ray_serve_logger.warning(f"Missing title or description field in the json request = {deployments}")
#         time.sleep(10)
#         return f"hellooooooo "

@serve.deployment
class RiskyReasoning:
    def __init__(self):
        # Create a remote actor instance
        self.actor = HeavyComputeActor.remote()

    async def __call__(self, request: starlette.requests.Request):
        # Get input data from the request
        data = await request.json()

        # Submit work to the remote actor
        result_ref = self.actor.heavy_compute.remote(data["title"])

        # Get the result (will block until result is ready)
        result = await ray.get(result_ref)

        return result



app = RiskyReasoning.bind()


