from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA
from google.oauth2 import service_account

from beautiful_date import Jan, Apr, Sept
import json
import os

import streamlit as st

from langchain_core.runnables.utils import ConfigurableFieldSpec
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool  # Use the Tool object directly
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain.callbacks.tracers import ConsoleCallbackHandler



## Google Calendar

# Get the credintials from Secrets.
credentials = service_account.Credentials.from_service_account_info(
        json.loads(st.secrets["MYJSON"]),
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

# Create the GoogleCalendar.
calendar = GoogleCalendar(credentials=credentials)


#-------
### IMPORTANT: Here is an example of a listing event tool. For other features, replicate this code and edit

# Define the tool 
def get_events(dummy):
    return list(calendar.get_events(calendar_id="mndhamod@gmail.com"))

# Create a Tool object 
list_event_tool = Tool(
    name="GetEvents",
    func=get_events,
    description="Useful for getting the list of events from the user's calendar."
)

#------------

#-------
### IMPORTANT: For addign event: 

# Define the tool 
def add_event(start_date, start_time, length_hours):
    from beautiful_date import hours
    start = (start_date)[start_time]
    end = start + length_hours * hours
    event = Event('Meeting',
                  start=start,
                  end=end)
    r = gc.add_event(event)
    st.write(r)
    return r

# Create a Tool object 
add_event_tool = Tool(
    name="AddEvent",
    func=add_event,
    description="Useful for adding an event with a start date, start time, and length in hours the list of events. Returns whethere addition was successful or failed."
)

#------------

#IMPORTANT: Update this list with the new tools
tools = [list_event_tool, add_event_tool]

# Create the LLM
llm = ChatOpenAI(api_key=st.secrets["OPENAI_API_KEY"], temperature=0.1)


agent = create_react_agent(llm, tools )
agent = AgentExecutor.from_agent_and_tools(
    agent=agent,  # type: ignore
    tools=tools,
    verbose=True,
)


#--------------------


# specify your own session_state key for storing messages
msgs = StreamlitChatMessageHistory(key="special_app_key")

if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", "You are an AI chatbot having a conversation with a human."),
#         # MessagesPlaceholder(variable_name="chat_history", optional=True),
#         # MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
#         MessagesPlaceholder(variable_name="history"),
#         ("human", "{question}"),
#     ]
# )



# # A chain that takes the prompt and processes it through the agent (LLM + tools)
# chain = prompt | agent

# # Queries the LLM with full chat history.
# chain_with_history = RunnableWithMessageHistory(
#     chain,
#     lambda session_id: StreamlitChatMessageHistory(),  # Always return the instance created earlier
#     input_messages_key="question",
#     history_messages_key="history"
# )

for msg in msgs.messages:
        if (msg.type in ["ai", "human"]):
                st.chat_message(msg.type).write(msg.content)

if entered_prompt := st.chat_input():
    # Add human message
    st.chat_message("human").write(entered_prompt)
    msgs.add_user_message(entered_prompt)

    config = {"configurable": {"session_id": "any"}} #, 'callbacks': [ConsoleCallbackHandler()]
    # response = chain_with_history.invoke({"question": entered_prompt}, config)
    response = agent.invoke({"input": entered_prompt})

    # Add AI response.
    response = response["messages"][-1].content
    st.chat_message("ai").write(response)
    msgs.add_ai_message(response)
    
