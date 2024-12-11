# src_scaflog_zoho_mcp_server/models.py

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ZohoField(BaseModel):
    """Represents a field in a Zoho Creator form."""
    link_name: str = Field(..., description="The API name of the field")
    display_name: str = Field(..., description="The display name of the field")
    field_type: int = Field(..., description="The type of the field (e.g., text, number)")
    required: bool = Field(default=False, description="Indicates if the field is mandatory")
    unique: bool = Field(default=False, description="Indicates if the field must be unique")
    max_char: Optional[int] = Field(default=None, description="Maximum character length for the field")
    lookup: Optional[bool] = Field(default=None, description="Indicates if the field is a lookup field")
    choices: Optional[List[dict]] = Field(default=None, description="List of choices for the field if applicable")

class ZohoForm(BaseModel):
    """Represents a form in Zoho Creator."""
    link_name: str = Field(..., description="API link name of the form")
    display_name: str = Field(..., description="Display name of the form")
    type: int = Field(..., description="Type of the form")
    fields: List[ZohoField] = Field(default_factory=list)

class ZohoRecord(BaseModel):
    """Represents a record in a Zoho Creator form."""
    id: str
    form_link_name: str
    data: Dict[str, Any]
    # Remove created_time and modified_time if they are not in the response
    # created_time: Optional[datetime] = None
    # modified_time: Optional[datetime] = None

class ZohoReport(BaseModel):
    """Represents a report in Zoho Creator."""
    link_name: str = Field(..., description="API link name of the report")
    display_name: str = Field(..., description="Display name of the report")
    type: int = Field(..., description="Type of the reprt")

class Cache:
    """Simple cache for form metadata."""
    def __init__(self, ttl_seconds: int = 300):
        self.forms: Dict[str, ZohoForm] = {}
        self.reports: Dict[str, ZohoReport] = {}
        self.ttl = ttl_seconds
        self.last_refresh: Optional[datetime] = None

    def needs_refresh(self) -> bool:
        """Check if cache needs refreshing."""
        if not self.last_refresh:
            return True
        return (datetime.now() - self.last_refresh).total_seconds() > self.ttl

    def update_forms(self, forms: List[ZohoForm]):
        """Update cached forms."""
        self.forms = {form.link_name: form for form in forms}
        self.last_refresh = datetime.now()

    def get_form(self, link_name: str) -> Optional[ZohoForm]:
        """Get a form from cache by link name."""
        return self.forms.get(link_name)
    
    def update_reports(self, reports: List[ZohoReport]):
        """Update cached reports."""
        self.reports = {report.link_name: report for report in reports}
        self.last_refresh = datetime.now()

