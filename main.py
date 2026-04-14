import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
import requests
import os
import models
from database import engine, SessionLocal
from routes import scan, certificates, monitor, contracts
from poller import poll_new_transactions
from monitor import get_monitor
from dotenv import load_dotenv

load_dotenv()

# Initialize Database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AlgoShield AI Backend", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(scan.router)
app.include_router(certificates.router)
app.include_router(monitor.router)
app.include_router(contracts.router)

@app.get("/")
async def health_check():
    return {"status": "online", "service": "AlgoShield AI"}

# Telegram Alert System
def send_telegram_alert(app_id, severity, description):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
        
    explorer_url = f"https://testnet.explorer.perawallet.app/application/{app_id}"
    message = (
        f"🚨 *AlgoShield AI Security Alert*\n\n"
        f"*App ID:* {app_id}\n"
        f"*Severity:* {severity}\n"
        f"*Description:* {description}\n\n"
        f"[View on Explorer]({explorer_url})"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

# Background Scheduler Job
def monitoring_job():
    db = SessionLocal()
    try:
        jobs = db.query(models.MonitorJob).filter(models.MonitorJob.is_active == True).all()
        for job in jobs:
            try:
                # Fetch new transactions
                new_txns = poll_new_transactions(job.account_address, job.app_id, job.last_seen_txn_id)
                if not new_txns:
                    continue
                
                monitor_instance = get_monitor(str(job.app_id))
                
                for txn in new_txns:
                    # Update monitor's training data if needed
                    monitor_instance.add_transactions([txn])
                    
                    # Check for anomalies
                    result = monitor_instance.check_transaction(txn)
                    
                    if result["is_anomaly"]:
                        # Save alert
                        alert = models.Alert(
                            job_id=job.id,
                            app_id=job.app_id,
                            severity=result["severity"],
                            description=result["description"],
                            txn_id=txn.get("id")
                        )
                        db.add(alert)
                        
                        # Send Telegram alert
                        send_telegram_alert(job.app_id, result["severity"], result["description"])
                
                # Update last seen txn id
                job.last_seen_txn_id = new_txns[-1].get("id")
                db.commit()
                
            except Exception as e:
                print(f"Error processing monitoring job for App {job.app_id}: {e}")
                db.rollback()
    finally:
        db.close()

# Start Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(monitoring_job, 'interval', seconds=30)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
