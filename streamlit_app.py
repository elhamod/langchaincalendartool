import streamlit as st
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA
from langchain_core.tools import Tool

from beautiful_date import Jan, Apr, Sept
import json
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA
from google.oauth2 import service_account
from beautiful_date import Jan, Apr, Sept

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import os

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
def get_events_tool():
    return list(calendar.get_events(calendar_id="mndhamod@gmail.com"))

# Create a Tool object without using decorators
event_tool = Tool(
    name="GetEvents",
    func=get_events_tool,
    description="Returns events from the user's calendar"
)


llm_with_tools = llm.bind_tools([event_tool])

st.write(llm_with_tools("What is the first event?"))
