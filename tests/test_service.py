# tests/test_service.py
import pytest
from datetime import datetime
import logging

# Configure logging for the test
logging.basicConfig(level=logging.INFO)

from scaflog_zoho_mcp_server.service import ZohoCreatorService

@pytest.mark.asyncio
async def test_list_forms(mock_service: ZohoCreatorService):
    """Test listing forms."""
    logging.info("Starting test_list_forms...")
    forms = await mock_service.list_forms(force_refresh=True)
    logging.info(f"Fetched forms: {[form.display_name for form in forms]}")  # Log the display names of the forms
    
    assert len(forms) > 0  # Ensure that at least one form is returned
    assert all(hasattr(form, 'link_name') for form in forms)  # Check that each form has a link_name
    assert all(hasattr(form, 'display_name') for form in forms)  # Check that each form has a display_name

@pytest.mark.asyncio
async def test_get_records(mock_service: ZohoCreatorService):
    """Test getting records."""
    logging.info("Starting test_get_records...")
    records = await mock_service.get_records("test_form")
    logging.info(f"Fetched records: {records}")  # Log the fetched records
    assert len(records) == 1
    assert records[0].id == "123"
    assert records[0].data["ID"] == "test_value"

@pytest.mark.asyncio
async def test_create_record(mock_service: ZohoCreatorService):
    """Test creating a record."""
    record = await mock_service.create_record(
        "test_form",
        {"test_field": "new_value"}
    )
    assert record.id == "123"
    assert record.form_link_name == "test_form"
    assert record.data["test_field"] == "new_value"

@pytest.mark.asyncio
async def test_update_record(mock_service: ZohoCreatorService):
    """Test updating a record."""
    record = await mock_service.update_record(
        "test_form",
        "123",
        {"test_field": "updated_value"}
    )
    assert record.id == "123"
    assert record.form_link_name == "test_form"
    assert record.data["test_field"] == "updated_value"

@pytest.mark.asyncio
async def test_fetch_data(mock_service):
    logging.info("Starting test_fetch_data...")
    data = await mock_service.fetch_data()
    logging.info(f"Fetched data: {data}")
    assert data is not None  # Example assertion

@pytest.mark.asyncio
async def test_fetch_all_records(mock_service: ZohoCreatorService):
    """Test fetching all records from the Company_Info report."""
    logging.info("Starting test_fetch_all_records...")
    
    # Fetch all records for the report "Company_All_Data_Report"
    records = await mock_service.get_records("Company_All_Data")  # Use the report link name
    
    # Log the fetched records
    logging.info(f"Fetched records: {records}")
    
    # Assertions to verify the records
    assert len(records) > 0  # Ensure that at least one record is returned
    for record in records:
        assert isinstance(record.id, str)  # Ensure each record has a valid ID
        # assert "Company_Info" in record.data  # Ensure the record contains data for the form

# You can add more tests below...
