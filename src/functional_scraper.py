import os
from typing import Annotated, TypedDict
from datetime import datetime
import zoneinfo
import asyncio

from langgraph.func import entrypoint, task
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

import httpx
from bs4 import BeautifulSoup
from langgraph.func import task

from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)

@task
async def scrape_website(url: str) -> str:
    """Fetches a webpage and extracts its main text content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # 1. Fetch the webpage asynchronously
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()  # Raise an error if the request failed
    
    # 2. Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Remove unwanted elements like scripts, styles, and navigation
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.extract()
        
    # 3. Extract and clean the text
    text = soup.get_text(separator="\n")
    cleaned_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    
    return cleaned_text


@task
def summarize(text:str):
    """Summarizes the given text"""
    result = (llm | StrOutputParser()).invoke([
        SystemMessage("You are a text summarization pipeline that provides a text summary and returns ONLY the text summary given the text"),
        HumanMessage(text),
    ])
    return result


@entrypoint()
async def pipeline(url: str) -> str:
    """Scrapes a URL and returns its summary."""
    # Step 1: Scrape the website text
    raw_text = await scrape_website(url)
    
    # Truncate text slightly if it's massive, just to stay safe with context limits
    truncated_text = raw_text[:10000] 
    
    # Step 2: Pass the text to your summarizer
    summary = await summarize(truncated_text)
    
    return summary


async def main():
    # Use .invoke() instead of calling pipeline() directly
    result = await pipeline.ainvoke("https://en.wikipedia.org/wiki/Artificial_intelligence")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())