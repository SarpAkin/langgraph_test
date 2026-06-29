from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini")

response = llm.invoke([HumanMessage(content="Say hello in 3 languages!")])
print(response.content)
