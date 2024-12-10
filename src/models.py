# src_scaflog_zoho_mcp_server/models.py

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ZohoField(BaseModel):
    """Represents a field in a Zoho Creator form."""
    api_name: str = Field(..., description="API name of the field")
    display_name: str = Field(..., description="Display name of the field")
    field_type: str = Field(..., description="Data type of the field")
    max_length: Optional[int] = Field(None, description="Maximum length for text fields")
    required: bool = Field(False, description="Whether the field is required")
    lookup: Optional[dict] = Field(None, description="Lookup field configuration")
    choices: Optional[List[str]] = Field(None, description="Available choices for dropdown/radio fields")

class ZohoForm(BaseModel):
    """Represents a form in Zoho Creator."""
    link_name: str = Field(..., description="API link name of the form")
    display_name: str = Field(..., description="Display name of the form")
    fields: List[ZohoField] = Field(default_factory=list)
    access_type: str = Field(default="read", description="Access level (read/write/all)")
    last_modified: datetime = Field(default_factory=datetime.now)

class ZohoRecord(BaseModel):
    """Represents a record in a Zoho Creator form."""
    id: str
    form_link_name: str
    created_time: datetime
    modified_time: datetime
    data: Dict[str, Any]

class Cache:
    """Simple cache for form metadata."""
    def __init__(self, ttl_seconds: int = 300):
        self.forms: Dict[str, ZohoForm] = {}
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
    