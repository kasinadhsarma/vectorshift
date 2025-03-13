from pydantic import BaseModel
from typing import List, Optional

class IntegrationItemParameter(BaseModel):
    name: str
    value: str
    type: str  # string, number, boolean, etc.

class IntegrationItem(BaseModel):
    id: str
    name: str
    type: str  # page, database, contact, etc.
    source: str  # notion, airtable, hubspot, etc.
    parameters: List[IntegrationItemParameter]

