from fastapi import FastAPI
from pydantic import BaseModel
import os
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from lw_task import utils
import boto3
from lw_task.prompt import make_prompt

app = FastAPI()

openai_api_key = utils.get_secret()
os.environ["OPENAI_API_KEY"] = openai_api_key
table_name = "CustomerInformation"

dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")


class GenAIRequest(BaseModel):
    company_name: str = "Shoby"
    n_words: int = 800
    target_audience: str = "People who likes the outdoors."
    tone_of_voice: str = "Educational"
    model: str = "gpt-4o-mini"
    seed_sentence: str = (
        "Your day with Shoby. Hiking day from morning til evening. Mention all products in the story."
    )
    domain: str = "Advertisement"


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/generate_ai_text")
def generate_ai_text(request: GenAIRequest):

    table = dynamodb_resource.Table(table_name)

    # Todo: Setup error handling if the customer or domain does not exist.
    response = table.get_item(
        Key={
            "customer": "Shoby",
            "domain": "advertisement",
        }
    )
    customer_information = response["Item"]["info"]
    model = ChatOpenAI(model=request.model)
    prompt = make_prompt(
        request.company_name,
        customer_information,
        request.n_words,
        request.target_audience,
        request.tone_of_voice,
        request.domain,
        request.seed_sentence,
    )

    message = HumanMessage(content=[{"type": "text", "text": prompt}])
    res = model.invoke([message])
    print(res.content)
    return res.content
