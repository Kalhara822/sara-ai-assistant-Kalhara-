"""
Pydantic Schemas for AI Intent Parsing & Structured Tool Outputs
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class IntentResponse(BaseModel):
    """Structured response model parsed from LLM JSON output."""
    action: str = Field(description="Action key, e.g., 'open_application', 'set_volume', 'unknown'")
    application: Optional[str] = Field(default=None, description="Target app name if applicable")
    value: Optional[Any] = Field(default=None, description="Numeric or string value (e.g. 50 for volume)")
    query: Optional[str] = Field(default=None, description="Search term or prompt")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata parameters")
    speech_response: Optional[str] = Field(default=None, description="Response spoken back to the user")
    requires_confirmation: bool = Field(default=False, description="Whether user confirmation is mandatory")
