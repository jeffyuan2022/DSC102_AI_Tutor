import os
import time
from bs4 import BeautifulSoup
import re
import pandas as pd
import requests, json
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

# # Define a collection named "Question"
# questions = client.collections.create(
#         name="Question",
#         vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(),    # Set the vectorizer to "text2vec-openai" to use the OpenAI API for vector-related operations
#         generative_config=wvc.config.Configure.Generative.cohere(),             # Set the generative module to "generative-cohere" to use the Cohere API for RAG
#         properties=[
#             wvc.config.Property(
#                 name="question",
#                 data_type=wvc.config.DataType.TEXT,
#             ),
#             wvc.config.Property(
#                 name="answer",
#                 data_type=wvc.config.DataType.TEXT,
#             ),
#             wvc.config.Property(
#                 name="category",
#                 data_type=wvc.config.DataType.TEXT,
#             )
#         ]
#     )

# Load a dataset from URL
resp = requests.get(
    "https://raw.githubusercontent.com/weaviate-tutorials/quickstart/main/data/jeopardy_tiny.json"
)
data = json.loads(resp.text)
print(data)

# # Function to scrape one page of fact-checks
# def scrape_fact_checks(page_number):
#     url = f"https://www.politifact.com/factchecks/?page={page_number}"
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')

#     # List to store the fact-check data
#     data = []

#     # Find all fact-check articles on the page
#     fact_checks = soup.find_all('article', class_='m-statement')

#     for fact in fact_checks:
#         # Extract Author/Speaker
#         author = fact.find('a', class_='m-statement__name').text.strip()

#         # Extract the Date of the statement
#         date_string = fact.find('div', class_='m-statement__desc').text.strip()

#         # Use a regular expression to extract only the date portion (e.g., October 8, 2024)
#         date_match = re.search(r'([A-Za-z]+ \d{1,2}, \d{4})', date_string)
#         date = date_match.group(0) if date_match else "No date found"

#         # Extract the Claim (statement being fact-checked)
#         claim = fact.find('div', class_='m-statement__quote').find('a').text.strip()

#         # Extract the URL to the full fact-check article
#         link = "https://www.politifact.com" + fact.find('div', class_='m-statement__quote').find('a')['href']

#         # Extract the Rating (e.g., False, Pants on Fire)
#         rating = fact.find('div', class_='m-statement__meter').find('img')['alt'].strip()

#         # Append the extracted information to the list
#         data.append({
#             'Author/Speaker': author,
#             'Date': date,
#             'Claim': claim,
#             'Rating': rating,
#             'Link to Full Article': link
#         })

#     return data

# # Loop through multiple pages and collect data
# def scrape_multiple_pages(start_page, end_page):
#     all_data = []
#     for page_number in range(start_page, end_page + 1):
#         print(f"Scraping page {page_number}...")
#         page_data = scrape_fact_checks(page_number)
#         all_data.extend(page_data)
#         time.sleep(2)  # Sleep for 2 seconds between each page request

#     return all_data

# # Scrape data from page 1 to 2
# data = scrape_multiple_pages(1, 2)
# politifact_data = pd.DataFrame(data)
# test_link = politifact_data['Link to Full Article'].iloc[0]

# test_response = requests.get(test_link)
# soup = BeautifulSoup(test_response.text, 'html.parser')

# Add dataset to "Question" collection
questions = client.collections.get("Question")
with questions.batch.dynamic() as batch:
    for d in data:
        batch.add_object(properties={
            "answer": d["Answer"],
            "question": d["Question"],
            "category": d["Category"],
        })

client.close() # Free up resources