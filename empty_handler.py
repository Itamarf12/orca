import time
import starlette
from ray import serve
import logging
import ray


# Initialize Ray and Ray Serve

ray_serve_logger = logging.getLogger("ray.serve")

#@serve.deployment(ray_actor_options={"num_cpus": 3})


@ray.remote
class HeavyComputeActor:
    def heavy_compute(self, data):
        # Simulate a heavy computation (e.g., 3 seconds of work)
        time.sleep(3)
        return {"result": f"Processed {data}"}


@serve.deployment()
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.warning(f"1111111111111")
        self.actor = HeavyComputeActor.remote()

    def translate(self, text: str) -> str:
        return "bbbbbbbbbbbb"

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()
        result_ref = self.actor.heavy_compute.remote(req["title"])
        result = await ray.get(result_ref)

        ray_serve_logger.warning(f"Missing title or description field in the json request")
        time.sleep(10)
        return f"hellooooooo "

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


