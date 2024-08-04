import starlette
from ray import serve
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import re


ray_serve_logger = logging.getLogger("ray.serve")
ray_serve_logger.setLevel(logging.DEBUG)
#MODEL = "Open-Orca/Mistral-7B-OpenOrca"
MODEL = "microsoft/Orca-2-13b"
DEVICE = 'auto' # 'cpu'

MAX_INPUT_TOKENS = 3500
MAX_OUTPUT_TOKENS = 1024

expected_categories = {
        "ArchitectureDesign",
        "GenAiUsage",
        "SensitiveDataHandling",
        "ThirdPartyIntegrationsAndDependencies",
        "UserPermissionsAndAccessManagement"
    }
UNEXPECTED_CATEGORY_VALUE = "Other"


def get_prompt1(title, description, prompt_prefix):
    return f"""
This is the details of a ticket:
title:
{title}
description:
{description}
{prompt_prefix}
    """

def categorical_response1(model, tokenizer, title, description, prompt_prefix):
    system_message = """
Role: Application Security (AppSec) Assistant
Directive: Adhere strictly to the provided guidelines.
Task: Upon review of the specified Jira ticket, determine and concisely state the security risk it presents.
    """
    user_message = get_prompt1(title, description, prompt_prefix)
    prompt = f"<|im_start|>system\n{system_message}<|im_end|>\n<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant"
    inputs = tokenizer(prompt, return_tensors='pt', max_length=MAX_INPUT_TOKENS).to('cuda')
    outputs = model.generate(
    **inputs, max_new_tokens=MAX_OUTPUT_TOKENS, use_cache=True, do_sample=True,
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


def clean_result_value(input_string):
    if input_string is None:
        return None
    if len(input_string) < 10 and "N/A" in input_string:
        return None
    substring = "</s"
    if input_string.endswith(substring):
        return input_string[:-len(substring)]
    return input_string


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

        security_review_questions_clean = clean_result_value(questions)
        security_review_questions = convert_to_markdown(security_review_questions_clean)
        threat_model_clean = clean_result_value(threat_model)
        threat_model = convert_to_markdown(threat_model_clean)

        risk_info = {
            "category": expected_category,
            "reasoning": reason,
            "securityReviewQuestions": security_review_questions,
            "threatModel": threat_model
        }
    else:
        risk_info = {
            "category": None,
            "reasoning": None,
            "securityReviewQuestions": None,
            "threatModel": None
        }
    return risk_info


def is_risky_response(model, tokenizer, title, description):
    is_risky_prompt = """
This is a ticket, which was marked as risky ticket. 
Your task: make sure that this ticket is risky. Please go over this ticket and make sure it's risky. If you're not sure mark it as not risky.
Respond in the following format:
"### is risky: [bool] ###"

Sample response:
"### is risky: False ###"
"""
    return categorical_response1(model, tokenizer, title, description, is_risky_prompt)


def text_generation_response(model, tokenizer, title, description):
    prompt_prefix = """
This ticket is classified as high-risk.

Based on the context provided, select the most appropriate risk category from the list below. Use "Other" only if absolutely none of the categories apply. Provide a concise reason that aligns explicitly with the selected category. Additionally, provide:
1. Up to 3 relevant questions that the AppSec team can ask during a security review with the developer implementing the ticket.
2. A threat model based on the STRIDE model, breaking down the feature request into 5 potential threats and writing "threat stories" that explain the impact and mitigation approach.

Respond in the following format:
"Risk Category: [Selected Category] ### Reason: [Brief Explanation] ### Security Review: [up to 3 questions] ### Threat Model: [threat stories for STRIDE]."

*Risk Category* should be one of the following:
- Architecture Design (e.g., flaws in overall system design, insecure architecture patterns, or scalability issues)
- GenAi Usage (e.g., risks related to the use of generative AI, such as model vulnerabilities or data poisoning)
- Sensitive Data Handling (e.g., exposure or improper handling of personal data, financial information, or confidential business data)
- Third Party (e.g., security risks from third-party applications, unsafe integrations with external systems)
- User Permissions And Access Management (e.g., improper access controls, weak authentication mechanisms, or identity theft)

If none of the categories apply, use "Other" as the "Risk Category" with a clear reason why it does not fit any of the provided categories. If you are certain that this ticket is not risky, use "Not Risky" as the "Risk Category".

*Security Review* should contain context-specific questions derived from the ticket. These questions are intended for the security review with the developer to ensure that all potential security risks are addressed.

*Threat Model* should also contain context-specific information and be based on the STRIDE model, breaking down the feature request into potential threats and writing "threat stories" that explain the impact and mitigation approach for each of the following threats: Spoofing, Tampering, Repudiation, Information Disclosure, and Denial of Service.

**Important Note**:
Security Review and Threat Model must always be **context-specific**. For example, if a ticket is about changing permissions in a specific database, ensure that the "Security Review" questions and the "Threat Model" specifically address issues related to database permissions.
"""
    return categorical_response1(model, tokenizer, title, description, prompt_prefix)


def is_risky_res(res):
    return "True" in res

def convert_to_markdown(text):
    # Use a regular expression to find all items that start with a digit followed by a closing parenthesis
    matches = re.findall(r'\d+\) .*?(?=\d+\)|$)', text)
    # Initialize a list to hold formatted markdown lines
    markdown_lines = []
    # Iterate through the matches and format them as markdown list items
    for match in matches:
        # Strip the text to remove any leading/trailing whitespaces
        markdown_lines.append(match.strip().replace(')', '.', 1))
    # Join the markdown lines with new lines to form the final markdown string
    markdown_text = '\n'.join(markdown_lines)
    return markdown_text


def is_input_valid(req):
    title = None
    description = None
    if 'title' in req and 'description' in req:
        title = req['title']
        description = req['description']
    if title is None or description is None:
        ray_serve_logger.error(f"Risky-Feature-Reasoning-Inference : Input request is not valid. request = {req}")
        return None, None
    return title, description

@serve.deployment(ray_actor_options={"num_gpus": 3})
class RiskyReasoning:
    def __init__(self):
        ray_serve_logger.debug(f"Risky-Feature-Reasoning-Inference : Start Model loading ...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(MODEL, device_map=DEVICE)
        ray_serve_logger.debug(f"Is-Risky-Feature-Inference : Model was loaded successfully.")

    async def __call__(self, request: starlette.requests.Request):
        req = await request.json()
        reason_cat = {
                    "Risk Category": None,
                    "Reason": None,
                    "Security Review": None,
                    "Threat Model": None
                }

        title, description = is_input_valid(req)
        if title and description:
            response1 = is_risky_response(self.model, self.tokenizer, title, description)
            ray_serve_logger.debug(f"Risky-Feature-Reasoning-Inference : response for is risky is {response1}")
            if "True" in response1:
                response2 = text_generation_response(self.model, self.tokenizer, title, description)
                reason_cat = extract_risk_info(response2)
        return reason_cat

#app = Translator.options(route_prefix="/translate").bind()
app = RiskyReasoning.bind()


