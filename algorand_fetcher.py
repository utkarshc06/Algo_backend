import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Use env vars or defaults
TESTNET_INDEXER = os.getenv("INDEXER_ADDRESS", "https://testnet-idx.algonode.cloud")
MAINNET_INDEXER = "https://mainnet-idx.algonode.cloud"
ALGOD_URL = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")

def fetch_contract_by_app_id(app_id: int, use_mainnet: bool = False) -> dict:
    """
    Fetch a deployed Algorand smart contract's TEAL code by its App ID.
    """
    base_url = MAINNET_INDEXER if use_mainnet else TESTNET_INDEXER
    url = f"{base_url}/v2/applications/{app_id}"
    
    response = requests.get(url, timeout=10)
    
    if response.status_code == 404:
        raise ValueError(f"App ID {app_id} not found on {'mainnet' if use_mainnet else 'testnet'}")
    
    if response.status_code != 200:
        raise ConnectionError(f"Indexer returned status {response.status_code}")
    
    data = response.json()
    app = data.get("application", {})
    params = app.get("params", {})
    
    approval_b64 = params.get("approval-program", "")
    clear_b64 = params.get("clear-state-program", "")
    
    approval_bytes = base64.b64decode(approval_b64) if approval_b64 else b""
    clear_bytes = base64.b64decode(clear_b64) if clear_b64 else b""
    
    approval_teal = disassemble_teal(approval_bytes)
    clear_teal = disassemble_teal(clear_bytes)
    
    return {
        "app_id": app_id,
        "creator": params.get("creator", ""),
        "approval_program": approval_teal,
        "clear_program": clear_teal,
        "global_state": params.get("global-state", []),
        "schema": {
            "global_ints": params.get("global-state-schema", {}).get("num-uint", 0),
            "global_bytes": params.get("global-state-schema", {}).get("num-byte-slice", 0),
        }
    }

def disassemble_teal(bytecode: bytes) -> str:
    """Disassemble TEAL bytecode back to human-readable TEAL source."""
    if not bytecode:
        return ""
    
    try:
        response = requests.post(
            f"{ALGOD_URL}/v2/teal/disassemble",
            data=bytecode,
            headers={"Content-Type": "application/x-binary"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get("result", "")
    except Exception:
        pass
    
    return f"; Could not disassemble bytecode\n; Raw bytes: {bytecode.hex()[:200]}..."

def get_account_transactions(account_address: str, app_id: int = None, limit: int = 50) -> list:
    """Fetch recent transactions for an account, filtered by app ID."""
    url = f"{TESTNET_INDEXER}/v2/accounts/{account_address}/transactions"
    
    params = {"limit": limit}
    if app_id:
        params["application-id"] = app_id
    
    response = requests.get(url, params=params, timeout=15)
    
    if response.status_code != 200:
        return []
    
    return response.json().get("transactions", [])
