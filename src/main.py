import os
from typing import Annotated, TypedDict
from datetime import datetime
import zoneinfo
import asyncio


from langchain_core.tools import tool
from langchain_core.messages import AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from dotenv import load_dotenv
load_dotenv()



# 1. State — shared data carried through the graph
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # add_messages: appends new message to the list, doesn't overwrite


# 2. 4 tools
@tool
def get_weather(city: str) -> str:
    """Returns the weather for a given city."""
    return f"{city}: 22°C, clear"

@tool
def calculator(expression: str) -> str:
    """Evaluates simple math expression, e.g. '3 * 4'."""

    try:
        res = str(eval(expression, {"__builtins__": {}}))
        print(f"calculator called with '{expression}' with result '{res}'\n")
        return res
    except Exception as e:
        print(f"calculator failed for '{expression}'\n")
        return f"Error: {e}"

@tool
def search_docs(query: str) -> str:
    """Searches internal documentation (placeholder)."""
    return f"Found 3 results for '{query}' (mock)."

@tool
def get_time(timezone: str = "Europe/Istanbul") -> str:
    """Returns the current time for a given timezone."""
    return datetime.now(zoneinfo.ZoneInfo(timezone)).strftime("%H:%M:%S")

tools = [get_weather, calculator, search_docs, get_time]

# 3. Model — the LangChain equivalent of your AsyncOpenAI setup
llm = ChatOpenAI(
    model="gpt-4o-mini",
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
llm_with_tools = llm.bind_tools(tools)

# 4. Nodes — each node: function(state) -> partial state update
def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)  # prebuilt: automatically executes tool_calls from the last message

# 5. Graph — connect nodes with edges
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition)  # if the last message has a tool_call, go to "tools", otherwise END
graph.add_edge("tools", "agent")  # after a tool runs, go back to agent

app = graph.compile()



async def main():
    # Invoke the graph
    response = await app.ainvoke({"messages": [("user", input("> "))]})
    
    # Option A: Print the full state dictionary
    # print("--- Full State ---")
    # print(response)
    
    # Option B: Cleanly print the last AI message
    print("\n--- Final Answer ---")
    print(response["messages"][-1].content)

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())

