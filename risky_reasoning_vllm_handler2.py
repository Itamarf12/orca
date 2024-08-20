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



class ThreatCategory(str, Enum):
    spoofing = "Spoofing"
    tampering = "Tampering"
    repudiation = "Repudiation"
    information_disclosure = "Information disclosure"
    denial_of_service = "Denial of service"
    elevation_of_privilege = "Elevation of privilege"

class RiskCategory(str, Enum):
    architecture_design = "Architecture Design",
    gen_ai_usage = "Gen Ai Usage",
    sensitive_data_handling = "Sensitive Data Handling",
    third_party = "Third Party",
    user_permissions_and_access_management = "User Permissions And Access Management"
    Other = "Other"

class Threat(BaseModel):
    category: ThreatCategory
    story: str
    impact: str
    mitigation: str

class RiskyTicketInfo(BaseModel):
    category: RiskCategory
    reason: str
    security_review_questions: List[str]
    threat_model: List[Threat]

class RiskyTicket(BaseModel):
    category: RiskCategory
    reason: str

class SecurityReview(BaseModel):
    security_review_questions: List[str]

class ThreatModel(BaseModel):
    threat_model: List[Threat]

class RiskyTicketMeta(BaseModel):
    security_review_questions: List[str]
    threat_model: List[Threat]

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
        return f"hellooooooo12 "


app = RiskyReasoning.bind()


