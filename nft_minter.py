import json
import hashlib
import os
from datetime import datetime
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, AssetTransferTxn, wait_for_confirmation
from dotenv import load_dotenv

load_dotenv()

# AlgoNode free testnet settings
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN", "")
PLATFORM_MNEMONIC = os.getenv("PLATFORM_MNEMONIC")

def get_algod_client():
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, headers={"User-Agent": "AlgoShield/1.0"})

def mint_security_certificate(
    recipient_address: str,
    app_id: int,
    security_score: int,
    scan_id: str,
    contract_hash: str
) -> dict:
    """
    Mint an ARC-69 NFT Security Certificate to the developer's wallet.
    """
    client = get_algod_client()
    
    if not PLATFORM_MNEMONIC:
        raise ValueError("PLATFORM_MNEMONIC not found in environment")

    # Get platform private key from mnemonic
    private_key = mnemonic.to_private_key(PLATFORM_MNEMONIC)
    platform_address = account.address_from_private_key(private_key)
    
    # Build ARC-69 metadata
    arc69_metadata = {
        "standard": "arc69",
        "description": f"AlgoShield AI Security Certificate for App ID {app_id}",
        "external_url": f"https://algoshield.io/certificates/{scan_id}",
        "mime_type": "image/png",
        "properties": {
            "app_id": str(app_id),
            "security_score": security_score,
            "risk_level": "Safe" if security_score >= 70 else "Risky",
            "contract_hash": contract_hash,
            "audit_date": datetime.utcnow().isoformat(),
            "scan_id": scan_id,
            "audited_by": "AlgoShield AI v1.0"
        }
    }
    
    params = client.suggested_params()
    short_hash = contract_hash[:8].upper()
    
    # Create Asset (NFT)
    txn = AssetConfigTxn(
        sender=platform_address,
        sp=params,
        total=1,                    
        decimals=0,                 
        default_frozen=False,
        unit_name="SHIELD",         
        asset_name=f"AlgoShield Certificate #{short_hash}",
        manager=platform_address,
        reserve=platform_address,
        freeze=platform_address,
        clawback=platform_address,
        url="https://algoshield.io/nft/",  
        note=json.dumps(arc69_metadata).encode(),  
    )
    
    signed_txn = txn.sign(private_key)
    txn_id = client.send_transaction(signed_txn)
    confirmed_txn = wait_for_confirmation(client, txn_id, wait_rounds=4)
    asset_id = confirmed_txn["asset-index"]
    
    # Attempt transfer (recipient must have opted-in)
    # If opt-in fails, we still return the asset_id as minted
    transfer_txn_id = None
    try:
        transfer_txn_id = _transfer_nft_to_recipient(
            client, private_key, platform_address, 
            recipient_address, asset_id
        )
    except Exception as e:
        print(f"Transfer failed (likely no opt-in): {e}")
    
    return {
        "asset_id": asset_id,
        "txn_id": txn_id,
        "transfer_txn_id": transfer_txn_id,
        "explorer_url": f"https://testnet.explorer.perawallet.app/asset/{asset_id}",
        "metadata": arc69_metadata
    }

def _transfer_nft_to_recipient(client, private_key, sender, recipient, asset_id):
    params = client.suggested_params()
    txn = AssetTransferTxn(
        sender=sender,
        sp=params,
        receiver=recipient,
        amt=1,
        index=asset_id
    )
    signed_txn = txn.sign(private_key)
    txn_id = client.send_transaction(signed_txn)
    wait_for_confirmation(client, txn_id, wait_rounds=4)
    return txn_id

def compute_contract_hash(contract_code: str) -> str:
    """Create a SHA256 fingerprint of the contract code."""
    return hashlib.sha256(contract_code.encode()).hexdigest()
