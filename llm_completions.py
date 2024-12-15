import cohere
import os
import json

from dotenv import load_dotenv
load_dotenv()

from chatbot import Chatbot
from document_url import Documents
from upload import Loader

COHERE_API_KEY = os.environ["COHERE_API_KEY"]
LOADER_PATH = os.environ["LOADER_PATH"]
sources = []

co = cohere.Client(COHERE_API_KEY)
with open("source.json", "r") as file:
    source = json.load(file)
    sources.extend(source)

file_docs = Loader(LOADER_PATH)
documents = Documents(sources)

chatbot = Chatbot(documents, file_docs)


async def complete_response(message):
    # Get the chatbot response
    response = chatbot.generate_response(message)
    discord_response = ""

    # Print the chatbot response
    print("Chatbot:")
    citations_flag = False
    
    for event in response:
        stream_type = type(event).__name__
        
        # Text
        if stream_type == "StreamTextGeneration":
            discord_response += f"{event.text}"
            print(event.text, end="")
        
        

        # Citations
        if stream_type == "StreamCitationGeneration":
            if not citations_flag:
                print("\n\nCITATIONS:")
                citations_flag = True
            print(event.citations[0])
            
        # Documents
        if citations_flag:
            if stream_type == "StreamingChat":
                print("\n\nDOCUMENTS:")
                documents = [{'id': doc['id'],
                            'text': doc['text'][:50] + '...',
                            'title': doc['title'],
                            'source': doc['url']} 
                            for doc in event.documents]
                for doc in documents:
                    print(doc)

    print(f"\n{'-'*100}\n")
    complete_response=discord_response
    discord_response = ""
    return complete_response

