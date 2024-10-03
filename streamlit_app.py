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
def get_events_tool(dummy):
    return list(calendar.get_events(calendar_id="mndhamod@gmail.com"))

# Create a Tool object 
event_tool = Tool(
    name="GetEvents",
    func=get_events_tool,
    description="Useful for getting the list of events from the user's calendar."
)

#------------
#IMPORTANT: Update this list with the new tools
tools = [event_tool]

# Create the LLM
llm = ChatOpenAI(api_key=st.secrets["OPENAI_API_KEY"], temperature=0.1)

agent_executor = create_react_agent(llm, tools )



#--------------------


# specify your own session_state key for storing messages
msgs = StreamlitChatMessageHistory(key="special_app_key")

if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an AI chatbot having a conversation with a human."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

# A chain that takes the prompt and processes it through the agent (LLM + tools)
chain = prompt | agent_executor

# Queries the LLM with full chat history.
chain_with_history = RunnableWithMessageHistory(
    chain,
    # lambda session_id: msgs,  # Always return the instance created earlier
    input_messages_key="question",
    history_messages_key="history",
)

for msg in msgs.messages:
        if (msg.type in ["ai", "human"]):
                st.chat_message(msg.type).write(msg.content)

if prompt := st.chat_input():
    # Add human message
    st.chat_message("human").write(prompt)
    msgs.add_user_message(prompt)

    config = {"configurable": {"session_id": "any"}}
    response = chain_with_history.invoke({"question": prompt}, config)

    # Add AI response.
    response = response["messages"][-1].content
    st.chat_message("ai").write(response)
    msgs.add_ai_message(response)
    
