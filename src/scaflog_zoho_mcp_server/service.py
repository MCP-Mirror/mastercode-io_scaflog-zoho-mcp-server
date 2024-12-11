# src_scaflog_zoho_mcp_server/service.py

from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime
import logging

from .models import ZohoForm, ZohoReport, ZohoField, ZohoRecord, Cache
from .auth import ZohoAuth
from .config import API_BASE_URL

# Configure logging to write to a file
logging.basicConfig(
    filename='app.log',  # Specify the log file name
    filemode='a',        # Append mode
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO   # Set the logging level
)

class ZohoCreatorService:
    """Service for interacting with Zoho Creator API."""
    
    def __init__(self, auth: ZohoAuth):
        self.auth = auth
        self.cache = Cache()
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        self.base_url = API_BASE_URL[auth.config.environment]

    async def list_forms(self, force_refresh: bool = False) -> List[ZohoForm]:
        """Get all available forms."""
        if not force_refresh and not self.cache.needs_refresh():
            return list(self.cache.forms.values())

        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/forms"
        
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Response from list_forms: {data}")  # Log the entire response

        forms = []
        for form_data in data['forms'][:10]:
            logging.info(f"Processing form: {form_data['link_name']}")  # Log the link_name
            fields = await self._get_form_fields(form_data['link_name'], headers)
            form = ZohoForm(
                link_name=form_data['link_name'],
                display_name=form_data['display_name'],
                fields=fields,
                type=form_data['type']
            )
            forms.append(form)

        self.cache.update_forms(forms)
        return forms

    async def _get_form_fields(self, form_link_name: str, headers: dict) -> List[ZohoField]:
        """Get fields for a specific form."""
        url = f"{self.base_url}/form/{form_link_name}/fields"
        
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # logging.info(f"Response from _get_form_fields: {data}")  # Log the entire response

        return [
            ZohoField(
                link_name=field['link_name'],
                display_name=field['display_name'],
                field_type=field['type'],
                required=field['mandatory'],
                unique=field['unique'],
                max_char=field.get('max_char'),
                lookup=field.get('is_lookup_field'),
                choices=field.get('choices')
            )
            for field in data['fields']
        ]

    async def list_reports(self, force_refresh: bool = False) -> List[ZohoReport]:
        """Get all available reports."""
        if not force_refresh and not self.cache.needs_refresh():
            return list(self.cache.reports.values())

        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/reports"
        
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Response from list_reports: {data}")  # Log the entire response

        reports = []
        for form_data in data['reports'][:10]:
            logging.info(f"Processing reporrt: {form_data['link_name']}")  # Log the link_name
            form = ZohoReport(
                link_name=form_data['link_name'],
                display_name=form_data['display_name'],
                type=form_data['type']
            )
            reports.append(form)

        self.cache.update_reports(reports)
        return reports

    async def get_records(
        self,
        report_link_name: str,
        criteria: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ZohoRecord]:
        """Get records from a specific report."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/report/{report_link_name}"
        
        params = {}
        if criteria:
            params['criteria'] = criteria
        if limit:
            params['limit'] = limit

        async with self._client as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            return [
                ZohoRecord(
                    id=record['ID'],
                    form_link_name=report_link_name,
                    data=record
                )
                for record in data['data']
            ]

    async def get_record(
        self,
        report_link_name: str,
        record_id: str
    ) -> ZohoRecord:
        """Get a specific record by ID."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/report/{report_link_name}/{record_id}"
        
        async with self._client as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()

            return ZohoRecord(
                id=record_id,
                form_link_name=report_link_name,
                data=result['data']
            )

    async def create_record(
        self,
        form_link_name: str,
        data: Dict[str, Any]
    ) -> ZohoRecord:
        """Create a new record in a form."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/form/{form_link_name}"
        
        async with self._client as client:
            response = await client.post(
                url,
                headers=headers,
                json={"data": data}
            )
            response.raise_for_status()
            result = response.json()

            return ZohoRecord(
                id=result['record']['ID'],
                form_link_name=form_link_name,
                data=data
            )

    async def update_record(
        self,
        report_link_name: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> ZohoRecord:
        """Update an existing record in a form."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/report/{report_link_name}/{record_id}"
        
        async with self._client as client:
            response = await client.patch(
                url,
                headers=headers,
                json={"data": data}
            )
            response.raise_for_status()
            result = response.json()

            return ZohoRecord(
                id=record_id,
                form_link_name=report_link_name,
                data=data
            )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def fetch_data(self):
        logging.info("Fetching data from the API...")
        try:
            response = await self._client.get("your_api_endpoint")
            response.raise_for_status()  # Raise an error for bad responses
            logging.info(f"Fetched data: {response.json()}")
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            return None
        