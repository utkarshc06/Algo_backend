from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String, index=True)
    app_id = Column(Integer, nullable=True)
    contract_code = Column(String)
    score = Column(Integer)
    risk_level = Column(String)
    vulnerabilities = Column(JSON) # Storing as JSON
    summary = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    wallet_address = Column(String, index=True)
    app_id = Column(Integer)
    asset_id = Column(Integer)
    txn_id = Column(String)
    explorer_url = Column(String)
    minted_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan")

class MonitorJob(Base):
    __tablename__ = "monitor_jobs"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, index=True)
    account_address = Column(String)
    wallet_address = Column(String)
    is_active = Column(Boolean, default=True)
    last_seen_txn_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("monitor_jobs.id"))
    app_id = Column(Integer)
    severity = Column(String)
    description = Column(String)
    txn_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    job = relationship("MonitorJob")
