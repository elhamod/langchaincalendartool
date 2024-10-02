import streamlit as st
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA

from beautiful_date import Jan, Apr, Sept
import json
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA
from google.oauth2 import service_account
from beautiful_date import Jan, Apr, Sept

from pydantic import BaseModel, Field

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
    

class GetEvents(BaseModel):
    """Returns events from my calendar"""
     return list(calendar.get_events(calendar_id="mndhamod@gmail.com"))


llm_with_tools = llm.bind_tools([GetEvents])

st.write(llm_with_tools("What is the first event?")
