# import time
# import starlette
# from ray import serve
# import logging
# import ray
# import vllm
# from outlines import models

import starlette
from ray import serve
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import re
import vllm
from outlines import models
from typing import List
from enum import Enum
from pydantic import BaseModel, constr, conint
import outlines
import time
# Initialize Ray and Ray Serve

ray_serve_logger = logging.getLogger("ray.serve")
ray_serve_logger.setLevel(logging.DEBUG)
MODEL_NM = "microsoft/Orca-2-13b"
DEVICE = 'auto' # 'cpu'



def load_model():
    ray_serve_logger.debug(f"Risky-Feature-Reasoning-Inference : Start Model loading ...")
    vllm_model = vllm.LLM(MODEL_NM, tensor_parallel_size=4)
    outline_vllm_model = models.VLLM(vllm_model)
    is_risky_generator = outlines.generate.choice(outline_vllm_model,
                                                  ["True", "False"])  # , sampler=multinomial(temperature=0.001))
    risky_generator = outlines.generate.json(outline_vllm_model, RiskyTicket,
                                             whitespace_pattern="")  # , sampler=multinomial(temperature=0.001))
    risky_security_review = outlines.generate.json(outline_vllm_model, SecurityReview, whitespace_pattern="")
    risky_threat_model = outlines.generate.json(outline_vllm_model, ThreatModel, whitespace_pattern="")
    ray_serve_logger.debug(f"Is-Risky-Feature-Inference : Model was loaded successfully.")
    return is_risky_generator, risky_generator, risky_security_review, risky_threat_model



@serve.deployment()
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.warning(f"1111111111111")
        

    def translate(self, text: str) -> str:
        return "bbbbbbbbbbbb"

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()

        ray_serve_logger.warning(f"Missing title or description field in the json request")
        time.sleep(10)
        return f"hellooooooo "


app = RiskyReasoning.bind()


