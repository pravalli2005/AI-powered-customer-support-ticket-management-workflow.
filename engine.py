"""
Duplicate Detection & Master Incident Correlation Engine.
Handles flurry duplicate detection and grouping of mass outages.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from ..models.ticket import Ticket, TicketStatus, PriorityLevel


class DeduplicationEngine:
    def __init__(self, duplicate_window_minutes: int = 60, similarity_threshold: float = 0.70):
        self.duplicate_window = timedelta(minutes=duplicate_window_minutes)
        self.similarity_threshold = similarity_threshold
        # Stores recent tickets indexed by customer_id
        self.ticket_store: Dict[str, List[Ticket]] = {}
        # Stores master incidents
        self.incidents: Dict[str, List[str]] = {}

    def register_ticket(self, ticket: Ticket):
        cid = ticket.customer.customer_id
        if cid not in self.ticket_store:
            self.ticket_store[cid] = []
        self.ticket_store[cid].append(ticket)

    def check_duplicate(self, incoming_customer_id: str, incoming_order_id: Optional[str], incoming_text: str, current_time: datetime) -> Optional[Ticket]:
        """
        Detects if an incoming conversation is an update/duplicate of an open ticket from the same customer.
        """
        existing = self.ticket_store.get(incoming_customer_id, [])
        for candidate in reversed(existing):
            # Check if ticket is still open
            if candidate.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
                continue

            # Check time window
            if current_time - candidate.created_at > self.duplicate_window:
                continue

            # Check order ID match
            if incoming_order_id and candidate.order and candidate.order.order_id == incoming_order_id:
                return candidate

            # Check text similarity
            sim = SequenceMatcher(None, candidate.issue.raw_text.lower(), incoming_text.lower()).ratio()
            if sim >= self.similarity_threshold:
                return candidate

        return None

    def merge_duplicate(self, existing_ticket: Ticket, new_raw_text: str, current_time: datetime) -> Ticket:
        """
        Appends new customer conversation update to existing ticket without creating a duplicate.
        """
        existing_ticket.issue.raw_text += f"\n[Update {current_time.isoformat()}]: {new_raw_text}"
        existing_ticket.log_audit(
            actor="DEDUP_ENGINE",
            action="DUPLICATE_MERGED",
            from_state=existing_ticket.status.value,
            to_state=existing_ticket.status.value,
            details="Customer sent follow-up/duplicate communication. Merged into existing ticket.",
        )
        return existing_ticket

    def correlate_incident(self, incident_id: str, tickets: List[Ticket], issue_keyword: str) -> Dict[str, Any]:
        """
        Clusters widespread issues (e.g. 50 users reporting payment gateway failure)
        under a single parent Incident, bumping impact score and priority to CRITICAL.
        """
        matched = []
        for t in tickets:
            if issue_keyword.lower() in t.issue.raw_text.lower() or issue_keyword.lower() in t.issue.summary.lower():
                t.parent_incident_id = incident_id
                t.priority.factors.impact_score = 100.0  # Mass incident
                t.priority.level = PriorityLevel.CRITICAL
                t.log_audit(
                    actor="INCIDENT_CORRELATOR",
                    action="LINKED_TO_INCIDENT",
                    from_state=t.status.value,
                    to_state=t.status.value,
                    details=f"Associated with Master Incident {incident_id}. Priority elevated to CRITICAL.",
                )
                matched.append(t.ticket_id)

        self.incidents[incident_id] = matched
        return {"incident_id": incident_id, "correlated_count": len(matched), "ticket_ids": matched}
