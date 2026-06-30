import os
from typing import TypedDict, Annotated
import operator

import psycopg
from langgraph.graph import StateGraph,  START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import(
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from tools.train_tool import train_search

from dotenv import load_dotenv
load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

DATABASE_URL = os.getenv("DATABASE_URL")

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_requests: str
    flight_results: str
    train_results: str
    hotel_results: str
    itinerary: str
    final_response: str
    llm_calls: int
    
def flight_agent(state: TravelState):
    query = state["user_query"]
    
    # Check if flights are feasible (not local/regional trips)
    # International or long-distance domestic routes
    should_search_flights = any(kw in query.lower() for kw in 
        ["flight", "air", "international", "abroad", "overseas", "across"])
    
    if not should_search_flights and "train" in query.lower():
        # If explicitly asking for trains, skip flights
        return {
            "flight_results": "",
            "messages": [AIMessage(content="Flights not applicable for this trip")],
            "llm_calls": state.get("llm_calls", 0)
        }
    
    flight_data = search_flights(query)
    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight results fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)
    
    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls",0)+1
    }
    
def train_agent(state: TravelState):
    query = f"Train travel options for {state['user_query']}"
    
    # Only search trains if they're explicitly mentioned or feasible for the route
    should_search_trains = any(kw in state['user_query'].lower() for kw in 
        ["train", "rail", "railway", "express", "local", "metro", "india"])
    
    if not should_search_trains and any(kw in state['user_query'].lower() for kw in 
        ["flight", "air", "international"]):
        # If international/flight trip, trains likely not applicable
        return {
            "train_results": "",
            "messages": [AIMessage(content="Trains not applicable for this trip")],
            "llm_calls": state.get("llm_calls", 0)
        }
    
    train_results = train_search(query)
    
    if not train_results:
        return {
            "train_results": "",
            "messages": [AIMessage(content="No train routes available for this route")],
            "llm_calls": state.get("llm_calls", 0)
        }
    
    return {
        "train_results": train_results,
        "messages": [AIMessage(content="Train travel information fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    
def itinerary_agent(state: TravelState):
    prompt = f"""
    Create a travel itinerary.
    User Query: {state['user_query']}
    Flight Results: {state['flight_results']}
    Train Results: {state['train_results']}
    Hotel Results: {state['hotel_results']}
    """
    
    response = llm.invoke([
        SystemMessage(
            content="You are an expret travel planner"
        ),
        HumanMessage(content=prompt)
    ])
    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 2
    }
  
  
def final_agent(state: TravelState):
    final_prompt = f"""
    You are a travel planner. Use the information below to generate a clear, concise final travel recommendation.
    User Query: {state['user_query']}
    Flight Results: {state['flight_results']}
    Train Results: {state['train_results']}
    Hotel Results: {state['hotel_results']}
    Itinerary: {state['itinerary']}
    """

    response = llm.invoke([
        HumanMessage(content=final_prompt)
    ])

    return {
        "final_response": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
    

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("train_agent", train_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "train_agent")
graph.add_edge("train_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


def create_app():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    _conn = psycopg.connect(DATABASE_URL, autocommit=True)
    checkpointer = PostgresSaver(_conn)
    checkpointer.setup()
    return graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    app = create_app()
    config = {
        "configurable": {
            "thread_id": "user_roshan"
        }
    }
    user_input = input("Enter travel request: ")

    result = app.invoke(
        {
            "message": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_requests": "",
            "flight_results": "",
            "train_results": "",
            "hotel_results": "",
            "itinerary": "",
            "final_response": "",
            "llm_calls": 0
        },
        config=config
    )

    print("\nFINAL RESPONSE- \n")
    print(result.get("final_response", "No final response generated."))
    