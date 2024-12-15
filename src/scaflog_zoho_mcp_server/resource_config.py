# src_scaflog_zoho_mcp_server/resource_config.py

from typing import Dict, List, Optional
from pydantic import BaseModel

class FieldConfig(BaseModel):
    """Configuration for a whitelisted field."""
    display_name: str
    description: Optional[str] = None
    required: bool = False

class FormConfig(BaseModel):
    """Configuration for a whitelisted form."""
    link_name: str
    display_name: str
    description: Optional[str] = None
    fields: Dict[str, FieldConfig]

class ReportConfig(BaseModel):
    """Configuration for a whitelisted report."""
    link_name: str
    display_name: str
    description: Optional[str] = None
    fields: Dict[str, FieldConfig]

# Define the whitelisted resources
WHITELISTED_RESOURCES = {
    "forms": {
        "Company_Info": FormConfig(
            link_name="Company_Info",
            display_name="Company Information",
            description="Core company details and profile",
            fields={
                "Company_Name": FieldConfig(
                    display_name="Company Name",
                    description="Legal name of the company",
                    required=True
                ),
                "Phone": FieldConfig(
                    display_name="Phone Number",
                    description="Primary contact number"
                ),
                "Email": FieldConfig(
                    display_name="Email",
                    description="Primary contact email"
                ),
                "Industry": FieldConfig(
                    display_name="Industry",
                    description="Company's primary industry"
                )
            }
        ),
        # Add more forms as needed
    },
    "reports": {
        "Company_All_Data": ReportConfig(
            link_name="Company_All_Data",
            display_name="Company Overview",
            description="Comprehensive view of company information",
            fields={
                "Company_Name": FieldConfig(
                    display_name="Company Name",
                    description="Legal name of the company"
                ),
                "Industry": FieldConfig(
                    display_name="Industry",
                    description="Company's primary industry"
                ),
                "Status": FieldConfig(
                    display_name="Status",
                    description="Current company status"
                )
            }
        ),
        # Add more reports as needed
    }
}
