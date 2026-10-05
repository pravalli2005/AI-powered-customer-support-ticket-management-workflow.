"""
Data models for AI-Powered Customer Support Ticket Management Workflow.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
import re
import uuid


class TicketStatus(str, Enum):
    DRAFT = "DRAFT"
    NEEDS_REVIEW = "NEEDS_REVIEW"  # Human-in-the-loop when AI confidence < 70%
    WAITING_FOR_CUSTOMER = "WAITING_FOR_CUSTOMER"
    TRIAGED = "TRIAGED"
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED_L1 = "ESCALATED_L1"
    ESCALATED_L2 = "ESCALATED_L2"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    MERGED = "MERGED"


class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IssueCategory(str, Enum):
    DELIVERY = "DELIVERY"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    DAMAGED_PRODUCT = "DAMAGED_PRODUCT"
    WRONG_PRODUCT = "WRONG_PRODUCT"
    AUTHENTICATION = "AUTHENTICATION"
    TECHNICAL_DEFECT = "TECHNICAL_DEFECT"
    CANCELLATION = "CANCELLATION"
    ACCOUNT_MANAGEMENT = "ACCOUNT_MANAGEMENT"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"


class ContactChannel(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CHAT = "CHAT"
    WHATSAPP = "WHATSAPP"


class CustomerTier(str, Enum):
    STANDARD = "STANDARD"
    SILVER = "SILVER"
    GOLD = "GOLD"
    ENTERPRISE = "ENTERPRISE"


@dataclass
class ContactInfo:
    preferred_channel: ContactChannel = ContactChannel.EMAIL
    email: Optional[str] = None
    phone: Optional[str] = None

    def masked_email(self) -> Optional[str]:
        if not self.email or "@" not in self.email:
            return self.email
        user, domain = self.email.split("@", 1)
        if len(user) <= 2:
            masked_user = user[0] + "*"
        else:
            masked_user = user[0] + ("*" * (len(user) - 2)) + user[-1]
        return f"{masked_user}@{domain}"

    def masked_phone(self) -> Optional[str]:
        if not self.phone:
            return None
        cleaned = re.sub(r"[^\d]", "", self.phone)
        if len(cleaned) <= 4:
            return "****"
        return "*" * (len(cleaned) - 4) + cleaned[-4:]


@dataclass
class CustomerInfo:
    customer_id: str
    name: str
    contact: ContactInfo
    tier: CustomerTier = CustomerTier.STANDARD


@dataclass
class OrderInfo:
    order_id: str
    product_name: Optional[str] = None
    product_id: Optional[str] = None
    purchase_date: Optional[datetime] = None
    delivery_status: Optional[str] = None
    order_value: float = 0.0
    currency: str = "USD"


@dataclass
class EvidenceItem:
    evidence_type: str  # PHOTO, RECEIPT, SCREENSHOT, PREVIOUS_TICKET, CHAT_LOG
    reference: str
    verified: bool = False


@dataclass
class IssueDetails:
    category: IssueCategory
    summary: str
    raw_text: str
    subcategory: Optional[str] = None
    confidence_score: float = 0.95  # AI Extraction Confidence (0.0 to 1.0)
    intent: Optional[str] = None
    language: str = "en"
    urgency: str = "NORMAL"
    evidence: List[EvidenceItem] = field(default_factory=list)
    missing_mandatory_fields: List[str] = field(default_factory=list)
    smart_missing_question: Optional[str] = None
    extracted_entities: Dict[str, str] = field(default_factory=dict)


@dataclass
class PriorityFactors:
    severity_score: float  # 0 to 100
    sentiment_score: float  # 0 (positive) to 100 (extreme frustration)
    waiting_time_score: float  # 0 to 100
    impact_score: float  # 0 (single user) to 100 (platform outage)


@dataclass
class PriorityInfo:
    level: PriorityLevel
    calculated_score: float
    factors: PriorityFactors
    manual_override: bool = False


@dataclass
class SLATracker:
    rule_id: str
    target_business_minutes: int
    warning_threshold_minutes: int
    sla_deadline: datetime
    warning_deadline: datetime
    consumed_business_minutes: int = 0
    remaining_business_minutes: int = 0
    warning_triggered: bool = False
    breached: bool = False
    escalation_level: int = 0
    is_paused: bool = False
    paused_at: Optional[datetime] = None
    total_paused_minutes: int = 0
    last_recalculated_at: Optional[datetime] = None


@dataclass
class RoutingInfo:
    team_id: str
    required_skills: List[str]
    assigned_agent_id: Optional[str] = None
    routing_strategy: str = "SKILL_LOAD_BALANCED"
    assignment_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AuditEntry:
    timestamp: datetime
    actor: str
    action: str
    from_state: Optional[str]
    to_state: Optional[str]
    details: str


@dataclass
class Ticket:
    ticket_id: str
    status: TicketStatus
    customer: CustomerInfo
    issue: IssueDetails
    priority: PriorityInfo
    sla: SLATracker
    routing: RoutingInfo
    created_at: datetime
    updated_at: datetime
    order: Optional[OrderInfo] = None
    parent_incident_id: Optional[str] = None
    duplicate_of_ticket_id: Optional[str] = None
    split_from_ticket_id: Optional[str] = None
    child_ticket_ids: List[str] = field(default_factory=list)
    ai_suggested_response: Optional[str] = None
    csat_rating: Optional[int] = None  # 1 to 5 stars
    csat_feedback: Optional[str] = None
    audit_trail: List[AuditEntry] = field(default_factory=list)

    def log_audit(self, actor: str, action: str, from_state: Optional[str], to_state: Optional[str], details: str):
        self.audit_trail.append(
            AuditEntry(
                timestamp=datetime.now(),
                actor=actor,
                action=action,
                from_state=from_state,
                to_state=to_state,
                details=details,
            )
        )
        self.updated_at = datetime.now()

    def pause_sla(self, current_time: datetime, reason: str = "Waiting for customer input"):
        """Pauses SLA timer while waiting for customer, halting consumed time calculation."""
        if not self.sla.is_paused:
            self.sla.is_paused = True
            self.sla.paused_at = current_time
            old_status = self.status.value
            self.status = TicketStatus.WAITING_FOR_CUSTOMER
            self.log_audit(
                actor="SLA_ENGINE",
                action="SLA_PAUSED",
                from_state=old_status,
                to_state=self.status.value,
                details=f"SLA paused: {reason}.",
            )

    def resume_sla(self, current_time: datetime, sla_engine) -> None:
        """Resumes SLA timer when customer responds, extending deadline by the paused business time."""
        if self.sla.is_paused and self.sla.paused_at:
            paused_minutes = sla_engine.calculate_consumed_business_minutes(self.sla.paused_at, current_time)
            self.sla.total_paused_minutes += paused_minutes
            self.sla.is_paused = False
            self.sla.paused_at = None
            old_status = self.status.value
            self.status = TicketStatus.TRIAGED

            # Extend deadlines by the business time paused
            if paused_minutes > 0:
                self.sla.sla_deadline = sla_engine._add_business_minutes(self.sla.sla_deadline, paused_minutes)
                self.sla.warning_deadline = sla_engine._add_business_minutes(self.sla.warning_deadline, paused_minutes)

            self.log_audit(
                actor="SLA_ENGINE",
                action="SLA_RESUMED",
                from_state=old_status,
                to_state=self.status.value,
                details=f"SLA resumed. Shifted deadline by {paused_minutes}m of elapsed business time.",
            )

    def generate_masked_handoff(self, reason: str, target_team_or_agent: str) -> Dict[str, Any]:
        """
        Generates safe handoff notes masking sensitive PII (credit cards, phone, email).
        """
        masked_email = self.customer.contact.masked_email()
        masked_phone = self.customer.contact.masked_phone()

        # Mask credit cards in raw text or extracted entities
        sanitized_summary = re.sub(r"\b(?:\d[ -]*?){13,16}\b", lambda m: "****-****-****-" + m.group(0).replace(" ", "").replace("-", "")[-4:], self.issue.summary)

        return {
            "ticket_id": self.ticket_id,
            "target": target_team_or_agent,
            "handoff_reason": reason,
            "customer_summary": {
                "name": self.customer.name,
                "tier": self.customer.tier.value,
                "contact": {
                    "masked_email": masked_email,
                    "masked_phone": masked_phone,
                    "preferred_channel": self.customer.contact.preferred_channel.value,
                },
            },
            "order_reference": self.order.order_id if self.order else None,
            "issue_category": self.issue.category.value,
            "sanitized_summary": sanitized_summary,
            "current_priority": self.priority.level.value,
            "sla_status": {
                "consumed_minutes": self.sla.consumed_business_minutes,
                "remaining_minutes": self.sla.remaining_business_minutes,
                "breached": self.sla.breached,
                "warning_triggered": self.sla.warning_triggered,
                "deadline_iso": self.sla.sla_deadline.isoformat(),
            },
            "timestamp": datetime.now().isoformat(),
        }


def check_mandatory_fields(category: IssueCategory, customer: CustomerInfo, order: Optional[OrderInfo], issue_raw: str) -> List[str]:
    """
    Evaluates mandatory fields based on business policy.
    Orders require order_id for delivery, refund, damaged, wrong product, cancellation.
    """
    missing: List[str] = []
    if not customer.name or customer.name.strip() == "":
        missing.append("customer_name")
    if not customer.contact.email and not customer.contact.phone:
        missing.append("contact_channel")

    order_dependent_categories = {
        IssueCategory.DELIVERY,
        IssueCategory.REFUND,
        IssueCategory.DAMAGED_PRODUCT,
        IssueCategory.WRONG_PRODUCT,
        IssueCategory.CANCELLATION,
    }

    if category in order_dependent_categories:
        if not order or not order.order_id:
            # Check if order number can be found in raw text
            order_match = re.search(r"#?([A-Z0-9]{5,12})", issue_raw)
            if not order_match:
                missing.append("order_id")

    return missing


def generate_missing_info_question(missing_fields: List[str], category: IssueCategory) -> str:
    """Generates context-aware customer prompts for missing required fields."""
    if not missing_fields:
        return ""
    field_names = [f.replace("_", " ").title() for f in missing_fields]
    fields_str = " and ".join(field_names)

    if "order_id" in missing_fields:
        if category == IssueCategory.REFUND:
            return f"To process your refund, could you please provide your {fields_str} and payment transaction reference?"
        elif category == IssueCategory.DAMAGED_PRODUCT:
            return f"We're sorry your item arrived damaged. Could you please share your {fields_str} and a quick photo of the package?"
        elif category == IssueCategory.DELIVERY:
            return f"To track your delivery status with our logistics partner, please provide your {fields_str}."

    return f"To assist you as quickly as possible, could you please provide your {fields_str}?"
