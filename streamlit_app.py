from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA
from google.oauth2 import service_account

from beautiful_date import Jan, Apr, Sept, Oct
import json
import os
from datetime import date, datetime
from beautiful_date import hours


from langchain_core.runnables.utils import ConfigurableFieldSpec
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
# from langgraph.prebuilt import create_react_agent
from langchain.agents.react.agent import create_react_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool, StructuredTool  # Use the Tool object directly
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain.callbacks.tracers import ConsoleCallbackHandler
from pydantic import BaseModel, Field
import streamlit as st






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

class GetEventargs(BaseModel):
    from_datetime: datetime = Field(description="beginning of date range to retrieve events")
    to_datetime: datetime = Field(description="end of date range to retrieve events")

# Define the tool 
def get_events(from_datetime, to_datetime):
    events = calendar.get_events(calendar_id="mndhamod@gmail.com", time_min=from_datetime, time_max=to_datetime)
    # print(list(events), from_datetime, to_datetime)
    return list(events)

# Create a Tool object 
list_event_tool = StructuredTool(
    name="GetEvents",
    func=get_events,
    args_schema=GetEventargs,
    description="Useful for getting the list of events from the user's calendar."
)

#------------

#-------
### IMPORTANT: For addign event: 

# Define the tool 
def add_event(start_date_time, length_hours, event_name):
    start = start_date_time
    end = start + length_hours * hours
    event = Event(event_name,
                  start=start,
                  end=end)
    return calendar.add_event(event, calendar_id="mndhamod@gmail.com")

# Create a Tool object 
class AddEventargs(BaseModel):
    start_date_time: datetime = Field(description="start date and time of event")
    length_hours: int = Field(description="length of event")
    event_name: str = Field(description="name of the event")

add_event_tool = StructuredTool(
    name="AddEvent",
    func=add_event,
    args_schema=AddEventargs,
    description="Useful for adding an event with a start date, event name, and length in hours the list of events. Calls get_events to make sure if the new event has been deleted."
)

#------------

#IMPORTANT: Update this list with the new tools
tools = [list_event_tool, add_event_tool]

# Create the LLM
llm = ChatOpenAI(api_key=st.secrets["OPENAI_API_KEY"], temperature=0.1)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful Google Calendar assistant"),
        ("human", "{input}"),
        # Placeholders fill up a **list** of messages
        ("placeholder", "{agent_scratchpad}"),
    ]
)


agent = create_tool_calling_agent(llm, tools, prompt)
# agent = create_react_agent(llm, tools, prompt=prompt)

# agent = create_react_agent(llm, tools )
agent = AgentExecutor(
    agent=agent,  # type: ignore
    tools=tools,
    # verbose=True,
    # agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Ensure this is a valid AgentType
    # tools=tools,
    # llm=llm,
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
    st_callback = StreamlitCallbackHandler(st.container())
    response = agent.invoke({"input": entered_prompt}, {"callbacks": [st_callback, ConsoleCallbackHandler()]})#, {'callbacks': [ConsoleCallbackHandler()]})
    # response = agent.invoke({"messages": [HumanMessage(content=entered_prompt)]})

    # Add AI response.
    # response = response["messages"][-1].content
    response = response["output"]
    st.chat_message("ai").write(response)
    msgs.add_ai_message(response)
    
