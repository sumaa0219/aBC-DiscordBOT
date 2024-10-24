from pydantic import BaseModel
import datetime


class vc(BaseModel):
    lastinTime: datetime.datetime
    lastoutTime: datetime.datetime
    lastinChannelID: int
