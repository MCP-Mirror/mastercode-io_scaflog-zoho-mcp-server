# tests/test_service.py
import pytest
from datetime import datetime

from src.service import ZohoCreatorService

@pytest.mark.asyncio
async def test_list_forms(mock_service: ZohoCreatorService):
    """Test listing forms."""
    forms = await mock_service.list_forms(force_refresh=True)
    assert len(forms) == 1
    assert forms[0].link_name == "test_form"
    assert forms[0].display_name == "Test Form"
    assert len(forms[0].fields) == 1
    assert forms[0].fields[0].api_name == "test_field"

@pytest.mark.asyncio
async def test_get_records(mock_service: ZohoCreatorService):
    """Test getting records."""
    records = await mock_service.get_records("test_form")
    assert len(records) == 1
    assert records[0].id == "123"
    assert isinstance(records[0].created_time, datetime)
    assert records[0].data["test_field"] == "test_value"

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
