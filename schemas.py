from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class Vulnerability(BaseModel):
    line: int
    vulnerability_type: str
    issue: str
    severity: str
    suggestion: str

class ScanCreate(BaseModel):
    app_id: Optional[int] = None
    wallet_address: str

class ScanResponse(BaseModel):
    id: int
    score: int
    risk_level: str
    vulnerabilities: List[Vulnerability]
    summary: str
    contract_code: Optional[str]
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

class CertificateCreate(BaseModel):
    scan_id: int
    wallet_address: str
    recipient_address: str

class CertificateResponse(BaseModel):
    id: int
    asset_id: int
    txn_id: str
    explorer_url: str
    minted_at: datetime
    
    model_config = {
        "from_attributes": True
    }

class MonitorStartRequest(BaseModel):
    app_id: int
    account_address: str
    wallet_address: str

class AlertResponse(BaseModel):
    id: int
    app_id: int
    severity: str
    description: str
    timestamp: datetime
    txn_id: Optional[str]
    
    model_config = {
        "from_attributes": True
    }

class ContractFetchResponse(BaseModel):
    app_id: int
    approval_program: str
    clear_program: str
    creator: str
