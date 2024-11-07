import os
import json
import weaviate
import weaviate.classes as wvc
from dotenv import load_dotenv

load_dotenv()
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_APIKEY")

# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=wvc.init.Auth.api_key(weaviate_api_key),
    headers={
        "X-OpenAI-Api-Key": openai_api_key
    }
)

questions = client.collections.get("Question")

response = questions.query.near_text(
    query="biology",
    limit=2
)

for obj in response.objects:
    print(json.dumps(obj.properties, indent=2))

client.close()  # Free up resources