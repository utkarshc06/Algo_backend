from algorand_fetcher import get_account_transactions

def poll_new_transactions(account_address: str, app_id: int, last_seen_txn_id: str = None) -> list:
    """
    Fetch transactions newer than the last seen one.
    """
    all_txns = get_account_transactions(account_address, app_id, limit=20)
    
    if not last_seen_txn_id:
        return all_txns
    
    # Return only transactions we haven't seen yet
    new_txns = []
    for txn in all_txns:
        if txn.get("id") == last_seen_txn_id:
            break
        new_txns.append(txn)
    
    # Return in chronological order (oldest to newest)
    return list(reversed(new_txns))
