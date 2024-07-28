import json

import starlette
from ray import serve
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import re


ray_serve_logger = logging.getLogger("ray.serve")
#MODEL = "Open-Orca/Mistral-7B-OpenOrca"
MODEL = "microsoft/Orca-2-13b"
# #MODEL = 'microsoft/DialoGPT-small'
DEVICE = 'auto' # 'cpu'

expected_categories = {
        "ArchitectureDesign",
        "GenAiUsage",
        "SensitiveDataHandling",
        "ThirdParty",
        "UserPermissionsAndAccessManagement"
    }
UNEXPECTED_CATEGORY_VALUE = "Other"


def get_prompt1(title, description):
    prompt_prefix = """
This ticket is classified as high-risk.

Based on the context provided, select the most appropriate risk category from the list below. Use "Other" only if absolutely none of the categories apply. Provide a concise reason that aligns explicitly with the selected category. Additionally, provide:
1. Up to 3 relevant questions that the AppSec team can ask during a security review with the developer implementing the ticket.
2. A threat model based on the STRIDE model, breaking down the feature request into 5 potential threats and writing "threat stories" that explain the impact and mitigation approach.

Respond in the following format:
"Risk Category: [Selected Category] ### Reason: [Brief Explanation] ### Security Review: [up to 3 questions] ### Threat Model: [threat stories for STRIDE]."

Risk Categories:
- Architecture Design (e.g., flaws in overall system design, insecure architecture patterns, or scalability issues)
- GenAi Usage (e.g., risks related to the use of generative AI, such as model vulnerabilities or data poisoning)
- Sensitive Data Handling (e.g., exposure or improper handling of personal data, financial information, or confidential business data)
- Third Party (e.g., security risks from third-party applications, unsafe integrations with external systems)
- User Permissions And Access Management (e.g., improper access controls, weak authentication mechanisms, or identity theft)

If none of the categories apply, use "Other" as the "Risk Category" with a clear reason why it does not fit any of the provided categories. If you are certain that this ticket is not risky, use "Not Risky" as the "Risk Category".

*Security Review* should contain context-specific questions derived from the ticket. These questions are intended for the security review with the developer to ensure that all potential security risks are addressed.

*Threat Model* should be based on the STRIDE model, breaking down the feature request into potential threats and writing "threat stories" that explain the impact and mitigation approach for each of the following threats: Spoofing, Tampering, Repudiation, Information Disclosure, and Denial of Service.

Sample Response:
"Risk Category: Sensitive Data Handling ### Reason: The ticket involves handling user financial data in a cash transfer modal ### Security Review: 1. How is the financial data within the cash transfer modal being secured in transit and at rest? 2. What encryption methods are being used specifically for the data entered in the cash transfer modal? 3. Are there any access controls or authentication mechanisms in place to ensure only authorized users can execute transfers via the cash transfer modal? ### Threat Model: 1. *Spoofing*: An attacker may impersonate a legitimate user to initiate a cash transfer. Mitigation: Implement multi-factor authentication for users accessing the cash transfer modal. 2. *Tampering*: Financial details entered into the cash transfer modal could be altered by an attacker. Mitigation: Use HTTPS to secure the data input and transmission. 3. *Repudiation*: Users might deny authorizing a cash transfer initiated through the modal. Mitigation: Implement secure logging and audit trails that capture user actions within the cash transfer modal. 4. *Information Disclosure*: Sensitive financial information entered into the cash transfer modal might be exposed to unauthorized users. Mitigation: Encrypt data at rest and enforce strict access controls to limit data exposure. 5. *Denial of Service*: An attacker could attempt to flood the cash transfer service, rendering it unavailable for legitimate users. Mitigation: Implement rate limiting and monitoring to detect and mitigate excessive requests targeting the cash transfer modal."
    """
    return f"""
This is the details of a ticket:
title:
{title}
description:
{description}
{prompt_prefix}
    """

def categorical_response1(model, tokenizer, title, description):
    system_message = """
Role: Application Security (AppSec) Assistant
Directive: Adhere strictly to the provided guidelines.
Task: Upon review of the specified Jira ticket, determine and concisely state the security risk it presents.
    """
    user_message = get_prompt1(title, description)
    prompt = f"<|im_start|>system\n{system_message}<|im_end|>\n<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant"
    inputs = tokenizer(prompt, return_tensors='pt').to('cuda')
    outputs = model.generate(
    **inputs, max_new_tokens=1024, use_cache=True, do_sample=True,
    temperature=0.1, top_p=1)
    res = tokenizer.batch_decode([outputs[0][inputs['input_ids'].size(1):]])[0]
    return res


def get_expected_category(category):
    if category in expected_categories:
        return category
    else:
        return UNEXPECTED_CATEGORY_VALUE


def clean_text(text):
    if text.startswith(": "):
        text = text[2:]
    if text.endswith("<|im_end|>"):
        text = text[:-10]
    return text


def extract_risk_info(text):
    text = clean_text(text)
    # Using regex to capture the key information after the colon and comma.
    # matches = re.findall(r'Risk Category: (.*?) ### Reason: (.*) ### AppSec Questions: (.*)', text)
    matches = re.findall(r'Risk Category: (.*?) ### Reason: (.*) ### Security Review: (.*) ### Threat Model: (.*).',
                         text)
    if matches:
        # Assumes only one match is found and takes the first one.
        risk_category, reason, questions, threat_model = matches[0]
        # Clean up the reason by removing any trailing special characters.
        reason = reason.strip()
        # Create the dictionary with the extracted information.
        expected_category = get_expected_category(risk_category.strip().replace(" ", ""))
        risk_info = {
            "category": expected_category,
            "reasoning": reason,
            "securityReviewQuestions": questions,
            "threatModel": threat_model.replace('</s', "")
        }
    else:
        risk_info = {
            "category": None,
            "reasoning": None,
            "securityReviewQuestions": None,
            "threatModel": None
        }
    return risk_info


@serve.deployment(ray_actor_options={"num_gpus": 3})
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.warning(f"1111111111111")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        ray_serve_logger.warning(f"2222222222222")
        self.model = AutoModelForCausalLM.from_pretrained(MODEL, device_map=DEVICE)
        ray_serve_logger.warning(f"3333333333")

    def translate(self, text: str) -> str:
        #return self.model(text)[0]["translation_text"]
        return "bbbbbbbbbbbb"

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()
        ray_serve_logger.warning(f"Missing title or description field in the json request = {req}")
        #reason_cat_json = {"error": "NO DATA - missing text field"}
        if 'title' in req and 'description' in req:
            title = req['title']
            description = req['description']
            response2 = categorical_response1(self.model, self.tokenizer, title, description)
            reason_cat = extract_risk_info(response2)
        return reason_cat


#app = Translator.options(route_prefix="/translate").bind()
app = RiskyReasoning.bind()


