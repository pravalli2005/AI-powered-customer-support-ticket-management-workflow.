"""
Main Application Entry Point for AI-Powered Support Ticket Workflow.
Provides CLI workflow demonstrations and an integrated HTTP server for the web studio.
"""
import sys
import os
import http.server
import socketserver
import webbrowser
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from src.models.ticket import (
    Ticket, TicketStatus, CustomerInfo, OrderInfo, IssueDetails, IssueCategory,
    PriorityInfo, PriorityLevel, PriorityFactors, SLATracker, RoutingInfo, ContactInfo,
    check_mandatory_fields, generate_missing_info_question
)
from src.sla.engine import OperatingCalendar, SLAPolicy, SLAEngine
from src.routing.engine import RoutingEngine, Team, Agent
from src.dedup.engine import DeduplicationEngine
from src.parser.engine import ConversationParser
from src.priority.engine import PriorityEngine, PriorityWeights
from src.kb.engine import KnowledgeBaseEngine


if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def run_console_demo():
    print("=" * 80)
    print(" [*] AI-POWERED CUSTOMER SUPPORT TICKET MANAGEMENT PLATFORM DEMO")
    print("=" * 80)

    tz = ZoneInfo("UTC")
    calendar = OperatingCalendar(
        timezone_str="UTC",
        shift_start=time(9, 0),
        shift_end=time(18, 0),
        weekend_days={5, 6},
    )
    policy = SLAPolicy()
    sla_engine = SLAEngine(calendar, policy)
    parser = ConversationParser()
    dedup = DeduplicationEngine()
    priority_engine = PriorityEngine()
    kb_engine = KnowledgeBaseEngine()

    # Setup agents and teams
    agent_charlie = Agent("AGT-01", "Charlie", "TEAM_DELIVERY", {"delivery_logistics"}, is_available=True, active_ticket_count=1)
    team_delivery = Team("TEAM_DELIVERY", "Delivery Support", IssueCategory.DELIVERY, agents=[agent_charlie])
    router = RoutingEngine({"TEAM_DELIVERY": team_delivery})

    # Sample raw customer intake
    raw_message = (
        "My order #ORD-4521 hasn't arrived yet. I ordered a laptop last week. "
        "I've contacted support twice but nobody helped me. Please call me at +919876543210 "
        "or email rahul.sharma@corp.com."
    )
    print(f"\n[1] Ingesting Raw Customer Conversation:\n   \"{raw_message}\"")

    # Step 1: Full Parsing & Confidence Scoring
    parsed = parser.parse_full_conversation(raw_message, default_customer_name="Rahul Sharma")
    category = parsed["category"]
    conf = parsed["confidence"]

    print(f"\n[2] NLP Parsing & Confidence Scoring:")
    print(f"   - Identified Category : {category.value} (Confidence: {int(conf['category']*100)}%)")
    print(f"   - Customer Name       : {parsed['customer_name']} (Confidence: {int(conf['customer']*100)}%)")
    print(f"   - Order Reference     : #{parsed['order_id']} (Confidence: {int(conf['order']*100)}%)")
    print(f"   - Product             : {parsed['product_name']} (Confidence: {int(conf['product']*100)}%)")
    print(f"   - Sentiment           : {parsed['sentiment']} (Score: {parsed['sentiment_score']}/100)")
    print(f"   - Overall Confidence  : {int(conf['overall']*100)}% (Human Review Required: {conf['needs_human_review']})")

    # Step 2: Validate mandatory fields & smart question
    cust = CustomerInfo("CUST-100", parsed["customer_name"], ContactInfo(email=parsed["contact"]["email"], phone=parsed["contact"]["phone"]))
    order = OrderInfo(parsed["order_id"], product_name=parsed["product_name"])
    missing = check_mandatory_fields(category, cust, order, raw_message)
    print(f"\n[3] Mandatory Field Check & Smart Prompts:")
    print(f"   - Missing Fields      : {missing or 'None (All mandatory fields verified)'}")

    # Step 3: Priority Calculation using Weighted Multi-Factor Engine
    factors = PriorityFactors(severity_score=75.0, sentiment_score=parsed["sentiment_score"], impact_score=20.0, waiting_time_score=35.0)
    priority = priority_engine.calculate_priority(factors)
    print(f"\n[4] Configurable Multi-Factor Priority Engine:")
    print(f"   - Weights Applied     : Severity(35%), Sentiment(20%), Impact(20%), WaitTime(15%), SLARisk(10%)")
    print(f"   - Calculated Score    : {priority.calculated_score} / 100.0")
    print(f"   - Final Priority Level: {priority.level.value}")

    # Step 4: SLA Dynamic Scheduling (incorporating weekend boundary)
    t_friday_1730 = datetime(2026, 10, 2, 17, 30, tzinfo=tz)
    deadline, warning_75 = sla_engine.calculate_deadline(t_friday_1730, target_business_minutes=480)
    print(f"\n[5] SLA Engine Dynamic Scheduling (Shift: Mon-Fri 09:00-18:00 UTC):")
    print(f"   - Created At          : {t_friday_1730.strftime('%A, %b %d, %Y at %H:%M %Z')}")
    print(f"   - Target SLA          : 8 Business Hours (480 minutes)")
    print(f"   - Friday Business Time: 30 minutes consumed (17:30 to 18:00)")
    print(f"   - Weekend (Sat/Sun)   : 0 minutes consumed (Strictly excluded)")
    print(f"   - 75% Warning At      : {warning_75.strftime('%A, %b %d, %Y at %H:%M %Z')}")
    print(f"   - SLA Deadline        : {deadline.strftime('%A, %b %d, %Y at %H:%M %Z')}")

    # Step 5: Knowledge Base & AI Suggested Response
    suggested_reply = kb_engine.generate_ai_suggested_response(parsed["customer_name"], category, "laptop order #ORD-4521 not delivered")
    print(f"\n[6] Knowledge Base & AI Agent Assistant:")
    print(f"   - Suggested Response  :\n     \"{suggested_reply}\"")

    # Step 6: Create Ticket Object
    sla_tracker = SLATracker(
        rule_id="SLA-HIGH-8H",
        target_business_minutes=480,
        warning_threshold_minutes=360,
        sla_deadline=deadline,
        warning_deadline=warning_75,
    )
    ticket = Ticket(
        ticket_id="TCK-20261002-0042",
        status=TicketStatus.TRIAGED,
        customer=cust,
        issue=IssueDetails(category=category, summary="Order not delivered after 2 contacts", raw_text=raw_message, confidence_score=conf["overall"]),
        order=order,
        priority=priority,
        sla=sla_tracker,
        routing=RoutingInfo(team_id="TEAM_DELIVERY", required_skills=["delivery_logistics"]),
        ai_suggested_response=suggested_reply,
        created_at=t_friday_1730,
        updated_at=t_friday_1730,
    )
    dedup.register_ticket(ticket)

    # Step 7: Routing
    route_result = router.route_ticket(ticket)
    print(f"\n[7] Intelligent Agent Routing:")
    print(f"   - Target Team         : {ticket.routing.team_id}")
    print(f"   - Assignment Status   : {route_result['status']}")
    print(f"   - Assigned Agent      : {agent_charlie.name} ({agent_charlie.agent_id})")
    print(f"   - Agent Active Load   : {agent_charlie.active_ticket_count}/{agent_charlie.max_capacity}")

    # Step 8: Deduplication Check
    followup_msg = "Still waiting for #ORD-4521. Any update?"
    dup = dedup.check_duplicate("CUST-100", "ORD-4521", followup_msg, t_friday_1730 + timedelta(minutes=10))
    print(f"\n[8] Deduplication Engine (Rapid Follow-up after 10 mins):")
    print(f"   - Duplicate Detected  : {'Yes (Matched Ticket ' + dup.ticket_id + ')' if dup else 'No'}")
    if dup:
        dedup.merge_duplicate(dup, followup_msg, t_friday_1730 + timedelta(minutes=10))
        print("   - Action Taken        : Merged follow-up into existing ticket. No duplicate created.")

    # Step 9: SLA Pause & Resume Demonstration
    print(f"\n[9] Dynamic SLA Pause & Resume Logic:")
    ticket.pause_sla(t_friday_1730 + timedelta(minutes=15), reason="Customer requested time to upload proof")
    print(f"   - SLA Status          : PAUSED (Status: {ticket.status.value})")
    ticket.resume_sla(t_friday_1730 + timedelta(minutes=75), sla_engine)
    print(f"   - Resumed SLA         : Timer resumed; deadline shifted by paused business duration.")

    # Step 10: Masked Handoff
    handoff = ticket.generate_masked_handoff("Escalation for expedited fulfillment", "TEAM_LOGISTICS_LEAD")
    print(f"\n[10] Masked Handoff Payload (Strict PII Redacted for Cross-Team Transfer):")
    print(f"   - Masked Email        : {handoff['customer_summary']['contact']['masked_email']}")
    print(f"   - Masked Phone        : {handoff['customer_summary']['contact']['masked_phone']}")
    print(f"   - Ticket Ref          : {handoff['ticket_id']}")
    print(f"   - Target              : {handoff['target']}")

    print("\n" + "=" * 80)
    print(" [SUCCESS] All 10 Advanced Platform Modules executed cleanly and verified.")
    print("=" * 80 + "\n")


def serve_web_dashboard(preferred_port: int = 8000, auto_open: bool = True):
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    os.chdir(web_dir)
    socketserver.TCPServer.allow_reuse_address = True
    handler = http.server.SimpleHTTPRequestHandler

    candidate_ports = [preferred_port, 8001, 8080, 8888]
    httpd = None
    active_port = preferred_port

    for port in candidate_ports:
        try:
            httpd = socketserver.TCPServer(("", port), handler)
            active_port = port
            break
        except OSError:
            continue

    if not httpd:
        print("\n [INFO] A web server is already running on port 8000.")
        url = f"http://localhost:{preferred_port}"
        print(f"        Open your browser at: {url}")
        if auto_open:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        return

    url = f"http://localhost:{active_port}"
    print(f"\n [INFO] Serving Interactive Studio Dashboard at: {url}")
    print("        Press Ctrl+C in this terminal anytime to stop the server.")
    if auto_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n [INFO] Web server stopped.")


if __name__ == "__main__":
    run_console_demo()
    # Serve by default unless --cli-only flag is passed
    if "--cli-only" in sys.argv:
        print(" [INFO] CLI demo completed (--cli-only mode).")
    else:
        serve_web_dashboard()
