import streamlit as st
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA
from langchain_core.prompts import ChatPromptTemplate
from beautiful_date import Jan, Apr, Sept
from langgraph.prebuilt import create_react_agent
import json
from google.oauth2 import service_account
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool  # Use the Tool object directly
from langchain_openai import ChatOpenAI
import os
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents import initialize_agent
from langchain.agents import AgentType

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

llm = ChatOpenAI()


# Get the credintials from Secrets.
credentials = service_account.Credentials.from_service_account_info(
        json.loads(st.secrets["MYJSON"]),
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

# Create the GoogleCalendar.
calendar = GoogleCalendar(credentials=credentials)
    
# Define the tool manually
def get_events_tool(dummy):
    return list(calendar.get_events(calendar_id="mndhamod@gmail.com"))




# Create a Tool object without using decorators
event_tool = Tool(
    name="GetEvents",
    func=get_events_tool,
    description="Useful for getting the list of events from the user's calendar."
)

tools = [event_tool]

# agent = initialize_agent(tools, llm    , verbose=True)
agent_executor = create_react_agent(llm, tools )

# response = agent.run("What is the first event?")
response  = agent_executor.invoke(
{"messages": [HumanMessage(content="What is the first event?")]}
)











# # Construct the tool calling agent
# agent = create_tool_calling_agent(llm, tools, prompt)

# # Create an agent executor by passing in the agent and tools
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# agent_executor.invoke(
#     {
#         "input": "What is the first event?"
#     }
# )








# # Create a Tool object without using decorators
# event_tool = Tool(
#     name="GetEvents",
#     func=get_events_tool,
#     description="Returns events from the user's calendar"
# )


# llm_with_tools = llm.bind_tools([event_tool])
# chain = llm_with_tools | (lambda x: x.tool_calls[0]["args"]) | get_events_tool

# prompt = ChatPromptTemplate.from_messages(
#     [("human", "What is the first event?" )]
# )



st.write(response)




