from datetime import datetime
from typing import Optional, List, Any

class IntegrationItem:
    def __init__(
        self,
        id: str,
        type: str,
        name: str,
        # Base properties
        directory: bool = False,
        parent_path_or_name: Optional[str] = None,
        parent_id: Optional[str] = None,
        creation_time: Optional[datetime] = None,
        last_modified_time: Optional[str] = None,
        url: Optional[str] = None,
        visibility: Optional[bool] = True,
        source: Optional[str] = None,
        # File-specific properties
        mime_type: Optional[str] = None,
        children: Optional[List[str]] = None,
        # Integration-specific properties
        email: Optional[str] = None,          # HubSpot contacts, Slack users
        company: Optional[str] = None,        # HubSpot contacts
        industry: Optional[str] = None,       # HubSpot companies
        domain: Optional[str] = None,         # HubSpot companies
        deal_stage: Optional[str] = None,     # HubSpot deals
        deal_amount: Optional[float] = None,  # HubSpot deals
        properties: Optional[dict] = None,     # Generic properties storage
        # Metadata properties
        delta: Optional[str] = None,
        drive_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        # Required fields
        self.id = id
        self.type = type
        self.name = name
        
        # Base properties
        self.directory = directory
        self.parent_path_or_name = parent_path_or_name
        self.parent_id = parent_id
        self.creation_time = creation_time
        self.last_modified_time = last_modified_time
        self.url = url
        self.visibility = visibility
        self.source = source

        # File-specific properties
        self.mime_type = mime_type
        self.children = children or []

        # Integration-specific properties
        self.email = email
        self.company = company
        self.industry = industry
        self.domain = domain
        self.deal_stage = deal_stage
        self.deal_amount = deal_amount
        self.properties = properties or {}

        # Metadata properties
        self.delta = delta
        self.drive_id = drive_id
        self.metadata = metadata or {}
