#!/usr/bin/env python3
"""
Enhanced Professional GenAI Service Efficiency UI
- Theme 2: Service efficiency improvement for MSPs & IT Teams
- Government flavour: UIDAI / MeiTY / NIC helpdesk
- Modules: SLA Guard, L1 Self-Service, Asset Health, Patch Assistant, Onboard Bot
"""

import http.server
import socketserver
import webbrowser
import tempfile
import pathlib
import textwrap
import argparse


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Gov SLA Guard – AI Service Ops</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <link rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
  <style>
    :root {
      --bg: #0f172a;
      --panel: #111827;
      --card: #1f2937;
      --accent: #f97316;     /* aws orange */
      --accent-soft: rgba(249,115,22,0.15);
      --text: #e2e8f0;
      --muted: #94a3b8;
      --danger: #ef4444;
      --warning: #facc15;
      --success: #22c55e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      display: flex;
      height: 100vh;
      font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background: radial-gradient(circle,#0f172a 0%, #020617 60%);
      color: var(--text);
    }
    .sidebar {
      width: 250px;
      background: rgba(15,23,42,0.7);
      backdrop-filter: blur(10px);
      border-right: 1px solid rgba(148,163,184,0.12);
      display: flex;
      flex-direction: column;
      padding: 18px;
      gap: 16px;
    }
    .logo {
      font-weight: 700;
      font-size: 1.05rem;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .logo i {
      color: var(--accent);
      font-size: 1.4rem;
    }
    .menu {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .menu button {
      background: transparent;
      border: none;
      color: var(--muted);
      text-align: left;
      padding: 9px 11px;
      border-radius: 8px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      transition: 0.15s all ease-in-out;
    }
    .menu button.active,
    .menu button:hover {
      background: rgba(249,115,22,0.12);
      color: #fff;
    }
    .menu button i {
      width: 20px;
      text-align: center;
      font-size: 0.95rem;
    }
    .sidebar-footer {
      margin-top: auto;
      font-size: 0.7rem;
      color: var(--muted);
    }
    .content {
      flex: 1;
      padding: 20px 28px 20px 28px;
      overflow-y: auto;
    }
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .title-block h1 {
      margin: 0;
      font-size: 1.35rem;
    }
    .title-block p {
      margin: 2px 0 0;
      color: var(--muted);
      font-size: 0.78rem;
    }
    .kpi-row {
      display: grid;
      grid-template-columns: repeat(auto-fit,minmax(160px,1fr));
      gap: 12px;
      margin-bottom: 20px;
    }
    .kpi-card {
      background: rgba(15,23,42,0.25);
      border: 1px solid rgba(148,163,184,0.12);
      border-radius: 16px;
      padding: 14px 14px 10px;
    }
    .kpi-title {
      font-size: 0.7rem;
      color: var(--muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .kpi-value {
      font-size: 1.45rem;
      font-weight: 600;
      margin-top: 6px;
    }
    .kpi-pill {
      background: rgba(34,197,94,0.12);
      color: var(--success);
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 0.6rem;
    }
    .panel {
      background: rgba(15,23,42,0.4);
      border: 1px solid rgba(148,163,184,0.12);
      border-radius: 16px;
      padding: 14px 14px 4px;
      margin-bottom: 20px;
    }
    .panel-title {
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
    }
    .panel-title i {
      color: var(--accent);
    }
    textarea, input, select {
      background: rgba(15,23,42,0.2);
      border: 1px solid rgba(148,163,184,0.1);
      border-radius: 10px;
      padding: 8px 9px;
      color: #fff;
      width: 100%;
      font-size: 0.8rem;
    }
    textarea:focus, input:focus {
      outline: 2px solid rgba(249,115,22,0.3);
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      background: linear-gradient(120deg, #f97316 0%, #f97316 38%, #fb923c 100%);
      border: none;
      border-radius: 999px;
      color: #fff;
      padding: 8px 15px;
      cursor: pointer;
      font-size: 0.78rem;
      font-weight: 500;
    }
    .two-col {
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 14px;
    }
    table {
      width: 100%;
      border-spacing: 0;
      font-size: 0.75rem;
    }
    th, td {
      padding: 7px 6px;
    }
    th {
      text-align: left;
      color: var(--muted);
      font-weight: 500;
      border-bottom: 1px solid rgba(148,163,184,0.08);
    }
    tr:hover {
      background: rgba(15,23,42,0.2);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: rgba(249,115,22,0.16);
      color: #fff;
      padding: 2px 8px 3px;
      border-radius: 999px;
      font-size: 0.6rem;
    }
    .pill-danger { background: rgba(239,68,68,0.16); color: #fee2e2; }
    .pill-warn { background: rgba(250,204,21,0.12); color: #fef9c3; }
    .pill-ok { background: rgba(34,197,94,0.16); color: #dcfce7; }

    @media (max-width: 980px) {
      .two-col { grid-template-columns: 1fr; }
      .sidebar { position: fixed; z-index: 22; height: 100vh; }
      .content { margin-left: 250px; }
    }
  </style>
</head>
<body>
  <aside class="sidebar">
    <div class="logo">
      <i class="fa-solid fa-bolt"></i>
      <div>
        Gov SLA Guard
        <div style="font-size:0.6rem;color:var(--muted);">Theme 2 · AWS GenAI</div>
      </div>
    </div>
    <div class="menu">
      <button class="active" onclick="showView('create')">
        <i class="fa-solid fa-pen-to-square"></i> Create Ticket (NL)
      </button>
      <button onclick="showView('sla')">
        <i class="fa-solid fa-gauge-high"></i> Run SLA Scan
      </button>
      <button onclick="showView('alerts')">
        <i class="fa-solid fa-bell"></i> Alerts
      </button>
      <button onclick="showView('dashboard')">
        <i class="fa-solid fa-chart-column"></i> Dashboard
      </button>
      <div style="margin:8px 0;border-bottom:1px solid rgba(148,163,184,0.12);"></div>
      <button onclick="showView('asset')">
        <i class="fa-solid fa-desktop"></i> Asset Health
      </button>
      <button onclick="showView('patch')">
        <i class="fa-solid fa-shield-halved"></i> Patch Assistant
      </button>
      <button onclick="showView('onboard')">
        <i class="fa-solid fa-user-plus"></i> Onboard Bot
      </button>
    </div>
    <div class="sidebar-footer">
      <div>MeiTY / UIDAI Demo</div>
      <div>Powered by AWS SSO profile</div>
    </div>
  </aside>

  <main class="content" id="app">
    <!-- default view -->
    <div id="view-create">
      <div class="topbar">
        <div class="title-block">
          <h1>Create Ticket from Natural Language</h1>
          <p>Type like an officer/citizen. GenAI will extract department, priority and SLA.</p>
        </div>
      </div>

      <div class="two-col">
        <div class="panel">
          <div class="panel-title"><i class="fa-solid fa-language"></i> Input</div>
          <textarea id="nl-input" rows="5">Aadhaar authentication is failing for multiple users in Indore; please raise a high priority ticket.</textarea>
          <div style="margin-top:10px;display:flex;gap:8px;">
            <button class="btn" onclick="parseAndCreate()">🧠 Parse & Create Ticket</button>
            <small style="color:var(--muted);">Uses AWS Bedrock (or fallback rules) to structure the ticket.</small>
          </div>
        </div>
        <div class="panel">
          <div class="panel-title"><i class="fa-solid fa-square-poll-horizontal"></i> Parsed Ticket</div>
          <pre id="parsed-output" style="font-size:0.7rem;white-space:pre-wrap;">{}</pre>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-list-check"></i> Current Tickets (DynamoDB)</div>
        <table id="ticket-table">
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Dept</th>
              <th>Priority</th>
              <th>Status</th>
              <th>SLA Due</th>
            </tr>
          </thead>
          <tbody id="ticket-body">
            <!-- will be populated in JS -->
          </tbody>
        </table>
      </div>
    </div>

    <div id="view-sla" style="display:none;">
      <div class="topbar">
        <div class="title-block">
          <h1>SLA Guard – Predict & Prevent</h1>
          <p>Simulates EventBridge → Lambda → SageMaker → StepFunctions → SNS</p>
        </div>
        <button class="btn" onclick="runSlaScan()"><i class="fa-solid fa-bolt"></i> Run SLA Scan</button>
      </div>
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-title">
            At-Risk Tickets
            <span class="kpi-pill" id="kpi-risk-pill">live</span>
          </div>
          <div class="kpi-value" id="kpi-risk">0</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">SLA Compliance</div>
          <div class="kpi-value" id="kpi-sla">96%</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">Alerts Sent Today</div>
          <div class="kpi-value" id="kpi-alerts">0</div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-fire"></i> High Risk (needs escalation)</div>
        <table id="sla-high">
          <thead><tr><th>Ticket</th><th>Dept</th><th>Priority</th><th>Risk</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-circle-half-stroke"></i> Medium / Safe</div>
        <table id="sla-mid">
          <thead><tr><th>Ticket</th><th>Dept</th><th>Priority</th><th>Risk</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div id="view-alerts" style="display:none;">
      <div class="topbar">
        <div class="title-block">
          <h1>Alerts</h1>
          <p>Here we list all tickets where SLA Guard triggered an SNS/SES notification.</p>
        </div>
      </div>
      <div class="panel" id="alert-panel">
        <!-- alerts will come here -->
      </div>
    </div>

    <div id="view-dashboard" style="display:none;">
      <div class="topbar">
        <div class="title-block">
          <h1>Service Efficiency Dashboard</h1>
          <p>Theme 2 – Technician productivity · Time & SLA · Fulfillment efficiency</p>
        </div>
      </div>
      <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-title">Tech Productivity</div><div class="kpi-value">+30%</div></div>
        <div class="kpi-card"><div class="kpi-title">SLA Breach Reduction</div><div class="kpi-value">−77%</div></div>
        <div class="kpi-card"><div class="kpi-title">Fulfillment Speed</div><div class="kpi-value">+35%</div></div>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-diagram-project"></i> Flow</div>
        <p style="font-size:0.75rem;color:var(--muted);">
          Natural-language request → Bedrock (parse) → DynamoDB (ticket) → EventBridge (5m) → Lambda (orchestrate) → SageMaker (predict) → Step Functions (branch) → SNS/SES (notify) → QuickSight (view).
        </p>
      </div>
    </div>

    <div id="view-asset" style="display:none;">
      <div class="topbar">
        <div class="title-block">
          <h1>Asset Health (Proactive)</h1>
          <p>Detect failing devices and auto-create tickets → same SLA pipeline.</p>
        </div>
        <button class="btn" onclick="simulateAssetScan()"><i class="fa-solid fa-magnifying-glass-chart"></i> Run Asset Scan</button>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-desktop"></i> Assets</div>
        <table id="asset-table">
          <thead><tr><th>Asset</th><th>Location</th><th>Health</th><th>Last heartbeat</th><th>Action</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div id="view-patch" style="display:none;">
      <div class="topbar">
        <div class="title-block">
          <h1>Patch Assistant (CERT-In / NIC)</h1>
          <p>Paste advisory text → GenAI extracts CVEs → turns into P1 tickets.</p>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-shield-halved"></i> Advisory Input</div>
        <textarea id="patch-input" rows="5">CERT-In advisory: OpenSSL vulnerability in RHEL 9 nodes. Patch within 24 hours for DC and DR.</textarea>
        <div style="margin-top:10px;">
          <button class="btn" onclick="createPatchTickets()">🧠 Generate Patch Tickets</button>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-ticket"></i> Generated Patch Tickets</div>
        <ul id="patch-list" style="font-size:0.7rem;"></ul>
      </div>
    </div>

    <div id="view-onboard" style="display:none;">
      <div class="topbar">
        <div class="title-block">
          <h1>Onboard Bot (Access provisioning)</h1>
          <p>GenAI to auto-create provisioning tickets for new officers.</p>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-user-plus"></i> Onboard Request</div>
        <textarea id="onboard-input" rows="4">Create access for Rajesh Sharma (IGRS) for VPN + eOffice + Aadhaar sandbox.</textarea>
        <div style="margin-top:10px;">
          <button class="btn" onclick="createOnboardTicket()">⚙️ Create Provisioning Ticket</button>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title"><i class="fa-solid fa-list-ul"></i> Latest Onboard Tickets</div>
        <ul id="onboard-list" style="font-size:0.7rem;"></ul>
      </div>
    </div>

  </main>

  <script>
    // in-memory store (for demo); in real app call your FastAPI/Lambda
    const tickets = [
      {ticket_id:"UIDAI-P1-000001", dept:"UIDAI", prio:"P1", status:"OPEN", sla:"2025-11-02T13:00:00Z"},
      {ticket_id:"MeiTY-P2-000002", dept:"MeiTY", prio:"P2", status:"OPEN", sla:"2025-11-02T16:00:00Z"},
    ];
    const alerts = [];
    const assets = [
      {name:"Indore DC – eKYC Node 01", loc:"Indore SDC 2.0", health:"OK", hb:"1 min ago"},
      {name:"Bhopal Collectorate Printer", loc:"Bhopal", health:"WARN", hb:"32 min ago"},
      {name:"Khandwa VPN Router", loc:"Khandwa", health:"DOWN", hb:"> 60 min"},
    ];

    function showView(id) {
      const views = ["create","sla","alerts","dashboard","asset","patch","onboard"];
      views.forEach(v => {
        document.getElementById("view-"+v).style.display = (v===id) ? "block" : "none";
      });
      // toggle active button
      const btns = document.querySelectorAll(".menu button");
      btns.forEach(b => b.classList.remove("active"));
      const map = {
        "create":0,
        "sla":1,
        "alerts":2,
        "dashboard":3,
        "asset":5,
        "patch":6,
        "onboard":7
      };
      const idx = map[id];
      if (typeof idx !== "undefined") btns[idx].classList.add("active");
      if (id === "create") renderTickets();
      if (id === "asset") renderAssets();
    }

    function renderTickets() {
      const body = document.getElementById("ticket-body");
      body.innerHTML = "";
      tickets.forEach(t => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${t.ticket_id}</td>
                        <td>${t.dept}</td>
                        <td><span class="badge">${t.prio}</span></td>
                        <td>${t.status}</td>
                        <td>${t.sla}</td>`;
        body.appendChild(tr);
      });
    }

    function parseAndCreate() {
      const txt = document.getElementById("nl-input").value.trim();
      // fake GenAI extraction in UI; backend will do real Bedrock
      let dept = (txt.toLowerCase().includes("aadhaar") || txt.toLowerCase().includes("ekyc"))
                  ? "UIDAI" : "MeiTY";
      let prio = txt.toLowerCase().includes("high") ? "P1" : "P2";
      const newId = dept+"-"+prio+"-"+Math.random().toString(16).slice(2,8);
      const now = new Date();
      const sla = new Date(now.getTime() + (prio==="P1" ? 2 : 6)*60*60*1000);
      tickets.unshift({
        ticket_id:newId,
        dept:dept,
        prio:prio,
        status:"OPEN",
        sla:sla.toISOString()
      });
      document.getElementById("parsed-output").textContent = JSON.stringify({
        department: dept,
        issue: txt,
        priority: prio,
        sla_due_hours: prio==="P1" ? 2 : 6
      }, null, 2);
      renderTickets();
      alert("✅ Ticket "+newId+" created.");
    }

    function runSlaScan() {
      const highBody = document.querySelector("#sla-high tbody");
      const midBody  = document.querySelector("#sla-mid tbody");
      highBody.innerHTML = "";
      midBody.innerHTML = "";
      let highCount = 0;
      tickets.forEach(t => {
        if (t.status !== "OPEN") return;
        // fake risk: P1 = high, older than 1h = high
        const isHigh = (t.prio === "P1");
        const row = document.createElement("tr");
        row.innerHTML = `<td>${t.ticket_id}</td><td>${t.dept}</td><td>${t.prio}</td><td>${isHigh? "0.92" : "0.48"}</td>`;
        if (isHigh) {
          highBody.appendChild(row);
          highCount++;
          // create alert
          alerts.unshift({
            msg:`🚨 Ticket ${t.ticket_id} (dept ${t.dept}) is at high risk of SLA breach.`,
            ts: new Date().toLocaleTimeString()
          });
          document.getElementById("alert-panel").innerHTML =
            alerts.map(a => `<div class="panel" style="background:rgba(239,68,68,0.12);margin-bottom:8px;">${a.msg}<div style="font-size:0.6rem;color:var(--muted);">${a.ts}</div></div>`).join("");
        } else {
          midBody.appendChild(row);
        }
      });
      document.getElementById("kpi-risk").textContent = highCount;
      document.getElementById("kpi-alerts").textContent = alerts.length;
    }

    function renderAssets() {
      const body = document.querySelector("#asset-table tbody");
      body.innerHTML = "";
      assets.forEach(a => {
        const pill = a.health === "DOWN" ? "pill-danger" : (a.health==="WARN" ? "pill-warn" : "pill-ok");
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${a.name}</td>
                        <td>${a.loc}</td>
                        <td><span class="${pill}">${a.health}</span></td>
                        <td>${a.hb}</td>
                        <td><button class="btn" style="padding:4px 9px;font-size:0.65rem;" onclick="createAssetTicket('${a.name}')">Create Ticket</button></td>`;
        body.appendChild(tr);
      });
    }

    function simulateAssetScan() {
      // mark the WARN one as DOWN
      assets.forEach(a => {
        if (a.health === "WARN") a.health = "DOWN";
      });
      renderAssets();
      alert("Asset anomalies detected. Tickets can be auto-created and enter SLA Guard.");
    }

    function createAssetTicket(assetName) {
      const newId = "ASSET-P2-"+Math.random().toString(16).slice(2,8);
      const now = new Date();
      const sla = new Date(now.getTime() + 4*60*60*1000);
      tickets.unshift({
        ticket_id:newId,
        dept:"Infra",
        prio:"P2",
        status:"OPEN",
        sla:sla.toISOString()
      });
      renderTickets();
      alert("Ticket created for asset: "+assetName);
    }

    function createPatchTickets() {
      const advisory = document.getElementById("patch-input").value.trim();
      const list = document.getElementById("patch-list");
      const id = "SEC-P1-"+Math.random().toString(16).slice(2,7);
      tickets.unshift({
        ticket_id:id,
        dept:"Security",
        prio:"P1",
        status:"OPEN",
        sla:new Date(new Date().getTime() + 24*60*60*1000).toISOString()
      });
      renderTickets();
      list.innerHTML = `<li>Created P1 ticket ${id} for advisory: ${advisory}</li>` + list.innerHTML;
      alert("Security/Patch ticket created.");
    }

    function createOnboardTicket() {
      const txt = document.getElementById("onboard-input").value.trim();
      const id = "ONB-P3-"+Math.random().toString(16).slice(2,7);
      tickets.unshift({
        ticket_id:id,
        dept:"HR/IT",
        prio:"P3",
        status:"OPEN",
        sla:new Date(new Date().getTime() + 6*60*60*1000).toISOString()
      });
      renderTickets();
      document.getElementById("onboard-list").innerHTML =
        `<li>${id}: ${txt}</li>` + document.getElementById("onboard-list").innerHTML;
      alert("Onboarding ticket created.");
    }

    // init
    renderTickets();
  </script>
</body>
</html>
"""


def launch_professional_ui(port: int = 8080):
    # write HTML to temp dir
    temp_dir = tempfile.TemporaryDirectory()
    html_file = pathlib.Path(temp_dir.name) / "index.html"
    html_file.write_text(HTML_TEMPLATE, encoding="utf-8")

    # serve that dir
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=temp_dir.name, **kwargs)

    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"🚀 Launching Gov SLA Guard UI on {url}")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        finally:
            temp_dir.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Launch enhanced AWS GenAI Service Efficiency UI")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    launch_professional_ui(args.port)


if __name__ == "__main__":
    main()
