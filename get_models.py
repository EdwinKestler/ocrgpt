import os
import openai
openai.organization = "org-P44J2sYyfEEfBF2gCYM7wSgX"
openai.api_key = os.getenv("OPENAI_API_KEY")

models = openai.Model.list()

for model in models['data']:
    print(f"{model.id}: {model.owned_by}")