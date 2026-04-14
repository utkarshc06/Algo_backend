import anthropic
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

SYSTEM_PROMPT = """
You are an expert Algorand smart contract security auditor with deep knowledge of TEAL (Transaction Execution Approval Language) and PyTEAL.

You analyze smart contracts for the following vulnerability classes (based on Trail of Bits Algorand audit findings):

1. AUTHORIZATION_MISSING — No check on Txn.sender or Global.creator_address(). Allows anyone to call privileged operations.
2. REENTRANCY_RISK — Inner transactions that call external apps before state is committed.
3. UNCHECKED_CLOSE_REMAINDER — CloseRemainderTo field not explicitly rejected (bz/bnz check missing).
4. UNCHECKED_REKEY — RekeyTo field not verified to be zero address.
5. INTEGER_OVERFLOW — Arithmetic without overflow guards (no bounding checks after add/mul).
6. HARDCODED_ADDRESS — Hardcoded creator or admin address instead of global state variable.
7. MISSING_GROUP_SIZE_CHECK — App call in a group without verifying gtxn count.
8. UNCHECKED_ASSET_RECEIVER — AssetReceiver not validated in asset transfer transactions.
9. TIMESTAMP_MANIPULATION — Logic depends on LatestTimestamp without tolerance margin.
10. LOGIC_SIG_BYPASS — Logic signature that can be exploited without proper constraints.

Severity levels: Critical, High, Medium, Low

Scoring:
- Start at 100
- Critical vulnerability: -30 points each
- High: -15 points each  
- Medium: -8 points each
- Low: -3 points each
- Minimum score: 0

Risk levels:
- 0-40: Critical
- 41-70: Risky
- 71-100: Safe

IMPORTANT: You MUST respond with ONLY valid JSON. No explanation text before or after. No markdown code blocks.

JSON format:
{
  "score": <integer 0-100>,
  "risk_level": "<Critical|Risky|Safe>",
  "vulnerabilities": [
    {
      "line": <integer>,
      "vulnerability_type": "<type from list above>",
      "issue": "<short description of the problem>",
      "severity": "<Critical|High|Medium|Low>",
      "suggestion": "<exact fix with TEAL code example if possible>"
    }
  ],
  "summary": "<2 sentence overall assessment>"
}

If the contract has no vulnerabilities, return an empty vulnerabilities array and score of 100.
"""

def scan_contract(contract_code: str) -> dict:
    """
    Analyze a TEAL or PyTEAL smart contract for security vulnerabilities.
    """
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620", # Updated to a broadly available model
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this Algorand smart contract for security vulnerabilities:\n\n```\n{contract_code}\n```"
                }
            ]
        )
        
        response_text = message.content[0].text.strip()
        
        # Strip markdown code fences if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        
        result = json.loads(response_text)
        return result
        
    except json.JSONDecodeError as e:
        return {
            "score": 0,
            "risk_level": "Critical",
            "vulnerabilities": [],
            "summary": "Analysis failed — could not parse AI response.",
            "error": str(e)
        }
    except Exception as e:
        return {
            "score": 0,
            "risk_level": "Critical", 
            "vulnerabilities": [],
            "summary": "Analysis failed.",
            "error": str(e)
        }
