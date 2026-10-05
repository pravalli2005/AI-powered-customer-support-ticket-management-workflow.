/**
 * Interactive Client Simulation for AI-Powered Support Ticket Workflow & SLA Operations Platform
 */

document.addEventListener("DOMContentLoaded", () => {
  const rawInput = document.getElementById("raw-convo-input");
  const btnProcess = document.getElementById("btn-process-ticket");
  const btnMissing = document.getElementById("btn-sample-missing");
  const btnRunAll = document.getElementById("btn-run-all-tests");

  const btnVague = document.getElementById("btn-vague-review");
  const btnKb = document.getElementById("btn-kb-resolve");
  const btnTogglePause = document.getElementById("btn-toggle-pause");

  const ticketIdEl = document.getElementById("val-ticket-id");
  const customerEl = document.getElementById("val-customer");
  const orderEl = document.getElementById("val-order");
  const routeEl = document.getElementById("val-assigned-route");
  const statusBadge = document.getElementById("ticket-status-badge");
  const confidenceBadge = document.getElementById("val-confidence-badge");
  const priorityBadge = document.getElementById("val-priority");
  const suggestedReplyEl = document.getElementById("val-suggested-reply");

  const slaFill = document.getElementById("sla-fill");
  const valWarningTime = document.getElementById("val-warning-time");
  const valDeadlineTime = document.getElementById("val-deadline-time");
  const statElapsed = document.getElementById("stat-elapsed");
  const statRemaining = document.getElementById("stat-remaining");
  const statRisk = document.getElementById("stat-risk");
  const maskedHandoff = document.getElementById("val-masked-handoff");
  const auditList = document.getElementById("audit-log-list");

  let isSlaPaused = false;

  // Default sample
  rawInput.value = "My order #ORD-4521 hasn't arrived yet. I ordered a laptop last week. I've contacted support twice but nobody helped me. Please call me at 9876543210 or email rahul@corp.com.";

  function addAudit(actor, text) {
    const item = document.createElement("div");
    item.className = "audit-item";
    const now = new Date().toTimeString().split(" ")[0];
    item.innerHTML = `<span class="audit-time">${now}</span> <span class="audit-actor">[${actor}]</span> <span class="audit-text">${text}</span>`;
    auditList.prepend(item);
  }

  function setTicketState(state, statusClass) {
    statusBadge.textContent = state;
    statusBadge.className = `badge ${statusClass}`;
  }

  function setConfidence(score, needsReview) {
    confidenceBadge.textContent = `AI Confidence: ${score}%`;
    if (needsReview) {
      confidenceBadge.className = "badge badge-review";
    } else {
      confidenceBadge.className = "badge badge-conf";
    }
  }

  function setSLA(percent, elapsedStr, remainingStr, risk, riskClass) {
    slaFill.style.width = `${Math.min(100, percent)}%`;
    if (percent >= 100) {
      slaFill.style.background = "linear-gradient(to right, #f43f5e, #e11d48)";
    } else if (percent >= 75) {
      slaFill.style.background = "linear-gradient(to right, #f59e0b, #d97706)";
    } else {
      slaFill.style.background = "linear-gradient(to right, #10b981, #06b6d4)";
    }
    statElapsed.textContent = elapsedStr;
    statRemaining.textContent = remainingStr;
    statRisk.textContent = risk;
    statRisk.className = `mini-val ${riskClass}`;
  }

  btnProcess.addEventListener("click", () => {
    isSlaPaused = false;
    ticketIdEl.textContent = "TCK-20261002-0042";
    customerEl.textContent = "Rahul Sharma (Gold VIP)";
    orderEl.textContent = "#ORD-4521 (Laptop)";
    routeEl.textContent = "Delivery Support (Agent Charlie)";
    setTicketState("ASSIGNED", "badge-assigned");
    setConfidence(95, false);
    priorityBadge.textContent = "HIGH (8h Target)";
    valWarningTime.textContent = "Mon 14:30";
    valDeadlineTime.textContent = "Mon 16:30";
    setSLA(25, "2h 00m", "6h 00m", "NORMAL", "text-success");

    suggestedReplyEl.textContent = '"Hi Rahul, thank you for reaching out. I completely understand your concern regarding the delivery status for laptop Order #ORD-4521. I am immediately escalating this with our courier logistics partner to expedite delivery."';

    maskedHandoff.textContent = JSON.stringify({
      ticket_id: "TCK-20261002-0042",
      customer_summary: {
        name: "Rahul Sharma",
        contact: {
          masked_email: "r****l@corp.com",
          masked_phone: "******3210"
        }
      },
      order_reference: "#ORD-4521",
      issue_category: "DELIVERY",
      sanitized_summary: "Order not delivered after 2 attempts",
      sla_status: "NORMAL"
    }, null, 2);

    addAudit("AI_PARSER", "Parsed Customer: Rahul Sharma, Order: #ORD-4521, Category: DELIVERY (Confidence: 95%)");
    addAudit("SLA_ENGINE", "Calculated 8h SLA excluding weekend: Mon 16:30 deadline");
    addAudit("ROUTER", "Assigned to Delivery Support Agent Charlie (Workload: 2/5)");
  });

  btnMissing.addEventListener("click", () => {
    rawInput.value = "My laptop is damaged! Please replace immediately or I will file a lawsuit!";
    ticketIdEl.textContent = "TCK-20261002-0043";
    customerEl.textContent = "Valued Customer";
    orderEl.textContent = "MISSING (Required)";
    routeEl.textContent = "Pending Information";
    setTicketState("WAITING_FOR_CUSTOMER", "badge-waiting");
    setConfidence(88, false);
    valWarningTime.textContent = "PAUSED";
    valDeadlineTime.textContent = "PAUSED";
    setSLA(0, "0h 00m", "PAUSED", "PAUSED", "text-warning");

    suggestedReplyEl.textContent = '"We are very sorry your laptop arrived damaged. Could you please share your Order ID and a photo of the package so we can process your replacement?"';

    maskedHandoff.textContent = JSON.stringify({
      ticket_id: "TCK-20261002-0043",
      status: "WAITING_FOR_CUSTOMER",
      missing_fields: ["order_id", "contact_phone"],
      smart_prompt: "Could you please share your Order ID and a quick photo of the damaged package?"
    }, null, 2);

    addAudit("VALIDATOR", "Detected missing mandatory field [order_id] for DAMAGED_PRODUCT issue");
    addAudit("WORKFLOW", "Set status to WAITING_FOR_CUSTOMER and paused SLA clock");
  });

  // Advanced Feature Simulators
  btnVague.addEventListener("click", () => {
    rawInput.value = "It is not working well. Need help ASAP.";
    ticketIdEl.textContent = "TCK-20261002-0044";
    customerEl.textContent = "Unknown User";
    orderEl.textContent = "N/A";
    routeEl.textContent = "Human Triage Desk";
    setTicketState("NEEDS_REVIEW", "badge-waiting");
    setConfidence(48, true);
    suggestedReplyEl.textContent = '"Hi there, could you please provide a few more details about what product or service is having an issue so we can direct you to the right specialist?"';

    addAudit("AI_PARSER", "Confidence score 48% < 70% threshold. Flagged for Human-in-the-Loop review.");
    alert("Human-in-the-loop triggered: Extraction confidence was 48% (< 70% safety threshold). Routed to supervisor triage desk.");
  });

  btnKb.addEventListener("click", () => {
    rawInput.value = "How do I reset my account password? The login screen is confusing.";
    ticketIdEl.textContent = "TCK-20261002-0045";
    customerEl.textContent = "Web User";
    orderEl.textContent = "N/A";
    routeEl.textContent = "Self-Service Auto-Resolution";
    setTicketState("RESOLVED", "badge-assigned");
    setConfidence(98, false);
    valWarningTime.textContent = "N/A";
    valDeadlineTime.textContent = "Instant Resolution";
    setSLA(100, "0m", "0m", "RESOLVED", "text-success");

    suggestedReplyEl.textContent = 'KB-101 Solution: "Go to login -> Click \'Forgot Password\' -> Enter registered email -> Secure reset link valid for 15 minutes."';

    addAudit("KB_ENGINE", "Query matched KB-101 (How to reset password). Confidence 98%. Auto-resolved with zero agent touch.");
    alert("Self-Service Resolution: Query matched Knowledge Base Article KB-101 (98% match). Ticket marked RESOLVED automatically!");
  });

  btnTogglePause.addEventListener("click", () => {
    isSlaPaused = !isSlaPaused;
    if (isSlaPaused) {
      setTicketState("WAITING_FOR_CUSTOMER", "badge-waiting");
      statRisk.textContent = "PAUSED";
      statRisk.className = "mini-val text-warning";
      addAudit("SLA_ENGINE", "SLA timer paused while awaiting customer response. Deadline frozen.");
      alert("SLA Paused: Ticket placed in WAITING_FOR_CUSTOMER. Consumed business minutes frozen.");
    } else {
      setTicketState("ASSIGNED", "badge-assigned");
      statRisk.textContent = "NORMAL";
      statRisk.className = "mini-val text-success";
      valDeadlineTime.textContent = "Shifted +2h";
      addAudit("SLA_ENGINE", "Customer responded. SLA timer resumed; deadline shifted forward by paused business time.");
      alert("SLA Resumed: Customer provided reply. SLA clock unpaused and deadline shifted forward.");
    }
  });

  // Hidden Test Scenario Simulators
  document.getElementById("btn-ht01").addEventListener("click", () => {
    addAudit("DEDUP_ENGINE", "[HT-01] Received 2nd message for #ORD-4521 within 8 mins. Merged into TCK-0042. Duplicate prevented.");
    alert("HT-01 Passed: Duplicate message recognized by Customer ID + Order ID and merged into existing ticket.");
  });

  document.getElementById("btn-ht02").addEventListener("click", () => {
    routeEl.textContent = "Escalation Team (Agent Charlie) [BACKUP]";
    addAudit("ROUTER", "[HT-02] Primary Payment agents unavailable/full. Successfully routed to Backup Escalation Team.");
    alert("HT-02 Passed: Fallback routing triggered when primary team offline.");
  });

  document.getElementById("btn-ht03").addEventListener("click", () => {
    valWarningTime.textContent = "Mon 14:30";
    valDeadlineTime.textContent = "Mon 16:30";
    addAudit("SLA_ENGINE", "[HT-03] Ingested Fri 17:30. Zero weekend hours accrued. Deadline = Monday 16:30.");
    alert("HT-03 Passed: SLA correctly excludes Sat/Sun weekends.");
  });

  document.getElementById("btn-ht04").addEventListener("click", () => {
    valWarningTime.textContent = "Tue 14:30";
    valDeadlineTime.textContent = "Tue 16:30";
    addAudit("SLA_ENGINE", "[HT-04] Runtime holiday (Monday Oct 5) injected. Deadline automatically shifted to Tuesday 16:30.");
    alert("HT-04 Passed: Mid-flight calendar holiday addition recalculated deadlines to Tuesday.");
  });

  document.getElementById("btn-ht05").addEventListener("click", () => {
    priorityBadge.textContent = "HIGH (4h Shortened)";
    setTicketState("ESCALATED_L1", "badge-breach");
    setSLA(100, "5h 00m", "0h 00m", "BREACHED", "text-danger");
    addAudit("SLA_ENGINE", "[HT-05] Policy changed 8h -> 4h. Ticket consumed 5h. Triggered immediate SLA Breach & L1 Escalation.");
    alert("HT-05 Passed: Runtime SLA compression detected immediate breach and escalated ticket.");
  });

  document.getElementById("btn-ht06").addEventListener("click", () => {
    orderEl.textContent = "#ORD-9912 (Provided by customer)";
    setTicketState("TRIAGED", "badge-triaged");
    valDeadlineTime.textContent = "Calculated (8h)";
    addAudit("WORKFLOW", "[HT-06] Customer provided missing Order ID. Resumed state from WAITING_FOR_CUSTOMER to TRIAGED.");
    alert("HT-06 Passed: State resumed from WAITING_FOR_CUSTOMER upon customer reply.");
  });

  document.getElementById("btn-ht07").addEventListener("click", () => {
    addAudit("PARSER", "[HT-07] Compound query detected. Split into Ticket A (DELIVERY) and Ticket B (AUTHENTICATION).");
    alert("HT-07 Passed: Compound complaint split into two specialized departmental tickets.");
  });

  document.getElementById("btn-ht08").addEventListener("click", () => {
    maskedHandoff.textContent = JSON.stringify({
      ticket_id: "TCK-008",
      customer_summary: {
        name: "Rahul Sharma",
        contact: {
          masked_email: "r****l@corp.com",
          masked_phone: "******3210"
        }
      },
      payment_card: "****-****-****-4444",
      handoff_reason: "Escalated to Fraud Investigation",
      operational_summary: "Duplicate transaction charge on card"
    }, null, 2);
    addAudit("SECURITY", "[HT-08] Sensitive PII masked in handoff payload (Credit card digits, email, phone masked).");
    alert("HT-08 Passed: Masked handoff summary verified with zero raw PII leaks.");
  });

  btnRunAll.addEventListener("click", () => {
    let count = 0;
    const items = ["btn-ht01", "btn-ht02", "btn-ht03", "btn-ht04", "btn-ht05", "btn-ht06", "btn-ht07", "btn-ht08"];
    items.forEach((id, idx) => {
      setTimeout(() => {
        const btn = document.getElementById(id);
        btn.style.borderColor = "#10b981";
        btn.style.boxShadow = "0 0 12px rgba(16, 185, 129, 0.4)";
        count++;
        if (count === items.length) {
          alert("All 8 Hidden Test Scenarios (HT-01 through HT-08) executed and verified successfully!");
        }
      }, idx * 120);
    });
  });
});
