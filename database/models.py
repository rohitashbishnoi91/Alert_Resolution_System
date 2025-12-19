"""
SQLAlchemy Database Models
Persistent storage for alerts, customers, transactions, and resolutions
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Customer(Base):
    """Customer KYC Profile"""
    __tablename__ = "customers"
    
    id = Column(String(50), primary_key=True)  # e.g., CUST-101
    customer_id = Column(String(50))  # Alias for compatibility
    name = Column(String(200), nullable=False)
    occupation = Column(String(100))
    declared_income = Column(Float)
    source_of_funds = Column(String(200))
    risk_rating = Column(String(20))  # LOW, MEDIUM, HIGH
    account_opened = Column(String(50))
    account_open_date = Column(String(50))  # Additional field
    enhanced_due_diligence = Column(Boolean, default=False)
    kyc_verified = Column(Boolean, default=True)
    employer = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="customer")
    alerts = relationship("Alert", back_populates="customer")
    
    def to_dict(self):
        return {
            "customer_id": self.id,
            "name": self.name,
            "occupation": self.occupation,
            "declared_income": self.declared_income,
            "source_of_funds": self.source_of_funds,
            "risk_rating": self.risk_rating,
            "account_opened": self.account_opened,
            "enhanced_due_diligence": self.enhanced_due_diligence,
        }


class Transaction(Base):
    """Transaction History"""
    __tablename__ = "transactions"
    
    id = Column(String(50), primary_key=True)  # e.g., T-001
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)  # DEBIT, CREDIT, WIRE_IN, WIRE_OUT, etc.
    date = Column(DateTime, nullable=False)
    counterparty = Column(String(200))
    jurisdiction = Column(String(100))
    branch = Column(String(100))
    mcc = Column(String(20))  # Merchant Category Code
    location = Column(String(200))
    origin = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    
    def to_dict(self):
        return {
            "txn_id": self.id, 
            "customer_id": self.customer_id,
            "amount": self.amount,
            "type": self.type,
            "date": self.date.isoformat() if self.date else None,
            "counterparty": self.counterparty,
            "jurisdiction": self.jurisdiction,
            "branch": self.branch,
            "mcc": self.mcc,
            "location": self.location,
            "origin": self.origin,
        }


class LinkedAccount(Base):
    """Linked Accounts for Aggregation"""
    __tablename__ = "linked_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False)
    linked_account_id = Column(String(50), nullable=False)
    relationship_type = Column(String(100))
    aggregate_deposits_7d = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SanctionsEntity(Base):
    """Sanctions Watchlist"""
    __tablename__ = "sanctions_entities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    entity_type = Column(String(50))  # INDIVIDUAL, ENTITY
    sanctioned = Column(Boolean, default=True)
    jurisdiction = Column(String(100))
    program = Column(String(100))  # OFAC-SDN, EU, UN, etc.
    common_name = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "sanctioned": self.sanctioned,
            "jurisdiction": self.jurisdiction,
            "program": self.program,
            "common_name": self.common_name,
        }


class Alert(Base):
    """Alert Records"""
    __tablename__ = "alerts"
    
    id = Column(String(50), primary_key=True)  # e.g., A-001
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False)
    scenario_code = Column(String(50), nullable=False)
    scenario_name = Column(String(200))
    description = Column(Text)
    trigger_details = Column(Text)
    status = Column(String(20), default="PENDING")  # PENDING, IN_PROGRESS, RESOLVED, CLOSED
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="alerts")
    resolution = relationship("AlertResolution", back_populates="alert", uselist=False)
    
    def to_dict(self):
        return {
            "alert_id": self.id,
            "customer_id": self.customer_id,
            "scenario_code": self.scenario_code,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AlertResolution(Base):
    """Alert Resolution Records"""
    __tablename__ = "alert_resolutions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(50), ForeignKey("alerts.id"), nullable=False)
    decision = Column(String(50), nullable=False)
    rationale = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    action_executed = Column(String(50))
    investigation_facts = Column(JSON)
    context_data = Column(JSON)
    resolved_at = Column(DateTime, default=datetime.utcnow)
    resolved_by = Column(String(100), default="AARS_SYSTEM")
    
    # Relationships
    alert = relationship("Alert", back_populates="resolution")
    
    def to_dict(self):
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "decision": self.decision,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "action_executed": self.action_executed,
            "investigation_facts": self.investigation_facts,
            "context_data": self.context_data,
            "resolved_at": self.resolved_at.isoformat(),
            "resolved_by": self.resolved_by,
        }

