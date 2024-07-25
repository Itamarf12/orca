import json

import starlette
from transformers import AutoTokenizer, AutoModelForCausalLM
from ray import serve
import logging
import re
import pandas as pd


ray_serve_logger = logging.getLogger("ray.serve")
MODEL = "Open-Orca/Mistral-7B-OpenOrca"
MODEL = "microsoft/Orca-2-13b"
# #MODEL = 'microsoft/DialoGPT-small'
DEVICE = 'auto' # 'cpu'



def get_prompt1(title, description):
    prompt_prefix = """
This ticket is classified as high-risk. Based on the context provided, choose the most appropriate risk category and give a concise reason. Respond with just the selected category and its one-sentence justification, in the following format: "Risk Category: [Selected Category], Reason: [Brief Explanation]."
Risk Categories:
- Sensitive Data Handling
- User Access and Identity Management
- APIs and Web Services
- External Applications and Integrations
- Infrastructure and Platform Security
If none apply, use "Other" for the category.
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
    inputs = tokenizer(prompt, return_tensors='pt') #.to('cuda')
    outputs = model.generate(
    **inputs, max_new_tokens=256, use_cache=True, do_sample=True,
    temperature=0.2, top_p=0.95)
    res = tokenizer.batch_decode([outputs[0][inputs['input_ids'].size(1):]])[0]
    return res






def clean_text(text):
    if text.startswith(": "):
        text = text[2:]
    if text.endswith("<|im_end|>"):
        text = text[:-10]
    return text


def extract_risk_info(text):
    text = clean_text(text)
    # Using regex to capture the key information after the colon and comma.
    matches = re.findall(r'Risk Category: (.*?), Reason: (.*)', text)

    if matches:
        # Assumes only one match is found and takes the first one.
        risk_category, reason = matches[0]

        # Clean up the reason by removing any trailing special characters.
        reason = reason.strip().strip('</s>')

        # Create the dictionary with the extracted information.
        risk_info = {
            "Risk Category": risk_category.strip(),
            "Reason": reason,
        }
    else:
        risk_info = {
            "Risk Category": None,
            "Reason": None,
        }
    return pd.Series(risk_info)


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
        # ray_serve_logger.warning(f"1111111111111")
        # self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        # ray_serve_logger.warning(f"2222222222222")
        # self.model = AutoModelForCausalLM.from_pretrained(MODEL, device_map=DEVICE)
        # ray_serve_logger.warning(f"3333333333")


        req = await request.json()
        ray_serve_logger.warning(f"Missing title or description field in the json request = {req}")
        reason_cat_json = {"error": "NO DATA - missing text field"}
        if 'title' in req and 'description' in req:
            title = req['title']
            description = req['description']
            response2 = categorical_response1(self.model, self.tokenizer, title, description)
            reason_cat = extract_risk_info(response2)
            reason_cat_dict = {"issueRiskPredictionCategory": reason_cat['Risk Category'],
                               "issueRiskPredictionExplanation": reason_cat['Reason']}
            reason_cat_json = json.dumps(reason_cat_dict)
        return reason_cat_json


#app = Translator.options(route_prefix="/translate").bind()
app = RiskyReasoning.bind()


