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



prompt1_prefix = """
This ticket is classified as high-risk.

Based on the context provided, select the most appropriate risk category from the list below. Use "Other" only if absolutely none of the categories apply, ensuring that at least one of the predefined categories is considered first. Provide a concise reason that aligns explicitly with the selected category. 

User response should include:
- **Risk Category**: Choose one of the predefined categories.
- **Reason**: A concise explanation aligning explicitly with the selected category.

### Risk Categories:
#### **Architecture Design**
- **Definition**: This category involves risks related to the overall design and structure of the application or system. It includes changes that could impact the foundational components, modules, or frameworks in a way that affects the scalability, maintainability, or performance of the system.
- **Examples**: Significant alterations to the application architecture, integration of new frameworks, refactoring large portions of the codebase, or redesigning key components.

#### **Gen AI Usage**
- **Definition**: This category pertains to the use of generative AI technologies within the application. This includes risks associated with implementing, training, and integrating AI models, as well as ensuring that they operate correctly and ethically.
- **Examples**: Using AI for automatic content generation, implementing chatbots using natural language processing models, training new AI models, or integrating AI-driven recommendations.

#### **Sensitive Data Handling**
- **Definition**: This category involves risks associated with the processing, storage, and transmission of sensitive data. It includes ensuring compliance with data privacy regulations and protecting data from unauthorized access and breaches.
- **Examples**: Encrypting sensitive information, implementing data masking, ensuring compliance with GDPR or HIPAA, and securing data at rest and in transit.

#### **User Permissions And Access Management**
- **Definition**: This deals with risks related to managing user permissions and access controls within the system. It includes ensuring that users have the appropriate levels of access and preventing unauthorized actions.
- **Examples**: Implementing role-based access control (RBAC), managing user authentication and authorization, setting up multi-factor authentication, and auditing user access logs.

#### **Third Party**
- **Definition**: This category involves risks associated with integrating or relying on third-party services, libraries, or platforms. This includes dependency management and ensuring that third-party components do not introduce vulnerabilities.
- **Examples**: Integrating third-party APIs, using external libraries or frameworks, dealing with third-party service outages, or compliance with third-party service agreements.


**Note**:
1. **Step 1**: Fully understand the ticket’s details and requirements.
2. **Step 2**: Identify and select the most appropriate risk category from the predefined options that have the greatest impact on this ticket.
3. **Step 3**: Provide a concise explanation for why this selected category is the most fitting.

Use the selected risk category to guide your response. Focus on identifying the primary category only.
"""

prompt2_prefix = """
This is a high-risk ticket and the risk type is '{risk_type}'.

Based on the context provided generate:
A list of up to 3 relevant questions that the AppSec team can ask during a security review with the developer implementing the ticket.

### Instructions:
**Security Review Questions**:
   - Develop up to 3 specific, context-relevant questions that the AppSec team should ask during the security review. These questions should help ensure that all potential security risks are identified and addressed.

**Note**:
- The "Security Review Questions" must be highly context-specific, addressing the particular details of the ticket. For instance, if the ticket involves changes to database permissions, make sure that the questions specifically pertain to the specific database premissions related issues.
- Ensure you comprehend the ticket's requirements and write "Security Review Questions" only specifically related to the changes requested in the ticket.
- Make sure to give the most valuable security review questions.
"""

prompt3_prefix = """
This is a high-risk ticket and the risk type is '{risk_type}'.

Generate a detailed threat model using the STRIDE model, breaking down the feature request into 6 potential threats. Each threat should include:

- **Threat Model using STRIDE**: A list of 6 potential threats with a clear "threat story" including:
  - Story: Hypothetical scenario of the threat.
  - Impact: Potential negative effects.
  - Mitigation: Steps to mitigate the threat.

### STRIDE Model:

  - **Spoofing**: How an attacker might impersonate another user.
  - **Tampering**: How data could be maliciously altered.
  - **Repudiation**: How actions might be falsely denied.
  - **Information Disclosure**: How sensitive info could be exposed.
  - **Denial of Service**: How service might be disrupted.
  - **Elevation of Privilege**: How unauthorized access might be gained.

**Note**: Make sure the "Threat Model" is specific to the ticket's details and requested changes only.
"""

is_risky_prompt = """
This ticket has been flagged as a high-risk item. Your task is to review this ticket thoroughly and confirm whether it indeed represents a risk.

Please follow these steps:
1. Carefully analyze the content and details of the ticket.
2. Assess whether it meets the criteria for being classified as risky based on potential vulnerabilities, impact on security, and other relevant risk factors.
3. If you determine that the ticket is indeed risky, respond with "True."
4. If you are uncertain or conclude that the ticket is not risky, respond with "False."

Your response should be either "True" (for risky) or "False" (for not risky).
"""




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



def get_prompt1(title, description, prompt_prefix):
    return f"""
This is the details of a ticket: 
title: 
{title}

description:
{description}

{prompt_prefix}
    """

def get_system_user_prompt(title, description, prompt_prefix):
    system_message = """
Role: Application Security (AppSec) Assistant
Directive: Adhere strictly to the provided guidelines.
Task: Upon review of the specified Jira ticket, determine and concisely state the security risk it presents.    
    """
    user_message = get_prompt1(title, description, prompt_prefix)
    prompt = f"<|im_start|>system\n{system_message}<|im_end|>\n<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant"
    return prompt


def retries(generator, prompt, res_obj, has_elements, retries=3):
    cur_iter = 0
    while has_elements(res_obj):
        res_obj = generator(prompt, max_tokens=MAX_TOKENS)
        cur_iter += 1
        print(f"iteration: {cur_iter}")
        if cur_iter > retries:
            break
    return res_obj

def get_risky_info(is_risky_generator, risky_generator, risky_security_review, risky_threat_model, title, description):
    is_risky_gen = is_risky_generator(get_prompt1(title, description, is_risky_prompt))
    if is_risky_gen == "True":
        start = time.time()
        risky_ticket = risky_generator(get_system_user_prompt(title, description, prompt1_prefix),
                                       max_tokens=MAX_TOKENS)
        print("1")
        print(time.time() - start)
        risky_category = risky_ticket.category.value
        prefix = prompt2_prefix.replace("{risk_type}", risky_category)
        security_review = SecurityReview(security_review_questions=[])
        threat_model = ThreatModel(threat_model=[])
        if risky_ticket.category != "Other":
            security_review = retries(
                risky_security_review,
                get_system_user_prompt(title, description, prefix),
                security_review,
                lambda x: len(x.security_review_questions) == 0)
            #                 security_review = risky_security_review(get_system_user_prompt(title, description, prefix))
            print("2")
            print(time.time() - start)
            prefix = prompt3_prefix.replace("{risk_type}", risky_category)
            threat_model = retries(
                risky_threat_model,
                get_system_user_prompt(title, description, prefix),
                threat_model,
                lambda x: len(x.threat_model) == 0)
            # threat_model = risky_threat_model(get_system_user_prompt(title, description, prefix))
            print("3")
            print(time.time() - start)
            return (risky_ticket, security_review, threat_model)
    return None


def threat_model_to_markdown(threat_model: List[Threat]) -> str:
    markdown_text = ""
    for threat in threat_model:
        markdown_text += f"#### {threat.category}\n"
        markdown_text += f"- **Story:** {threat.story}\n"
        markdown_text += f"- **Impact:** {threat.impact}\n"
        markdown_text += f"- **Mitigation:** {threat.mitigation}\n\n"
    return markdown_text


def security_review_to_markdown(security_review_questions: List[str]):
    markdown_text = ""
    for i, question in enumerate(security_review_questions):
        markdown_text += f"{i + 1}. {question}\n"
    return markdown_text


def extract_risk_info(x):
    return {
        "category": x[0].category.value,
        "reason": x[0].reason,
        "security review questions": security_review_to_markdown(x[1].security_review_questions),
        "threat model": threat_model_to_markdown(x[2].threat_model)
    }

def is_input_valid(req):
    title = None
    description = None
    if 'title' in req and 'description' in req:
        title = req['title']
        description = req['description']
    if title is None or description is None:
        ray_serve_logger.error(f"Risky-Feature-Reasoning-Inference : Input request is not valid")
        return None, None
    return title, description

@serve.deployment()
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.warning(f"1111111111111")
        self.is_risky_generator, self.risky_generator, self.risky_security_review, self.risky_threat_model = load_model()


    def translate(self, text: str) -> str:
        return "bbbbbbbbbbbb"

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()
        return f"hellooooooo12 "


app = RiskyReasoning.bind()


