# AlgoShield AI — Backend

This is the production-ready backend for AlgoShield AI, a blockchain + AI + cybersecurity platform built on Algorand.

## Tech Stack
- **FastAPI**: Core API framework
- **SQLAlchemy & PostgreSQL**: Database and ORM
- **Algorand Python SDK**: Blockchain interaction
- **Anthropic Claude API**: AI-powered smart contract auditing
- **Scikit-Learn (Isolation Forest)**: Anomaly detection for monitoring
- **APScheduler**: Background monitoring jobs

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment variables:
   - Copy `.env` file and fill in your credentials.
   - You need a **Claude API Key** for scanning.
   - You need a **Testnet Mnemonic** for minting certificates.
   - You need a **Telegram Bot Token** and **Chat ID** for alerts.

## Running the Server

Start the FastAPI server with:
```bash
python main.py
```

The API will be available at `http://localhost:8000`.
You can view the interactive API documentation at `http://localhost:8000/docs`.

## Project Structure
- `main.py`: Entry point and background scheduler.
- `scanner.py`: Claude AI integration for security audits.
- `monitor.py`: ML-based anomaly detection logic.
- `algorand_fetcher.py`: Fetches contract TEAL from the blockchain.
- `nft_minter.py`: Mints ARC-69 security certificates on Algorand.
- `routes/`: API endpoint definitions.
- `services/`: Business logic layer.
- `models.py` & `schemas.py`: Database and data validation models.

## Security Note
- Ensure `PLATFORM_MNEMONIC` is kept secure in the `.env` file and never committed to version control.
- Ensure the database connection is secured in production.
