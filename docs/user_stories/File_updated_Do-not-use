# 🧳 Purple Travel Agent – User Story & Requirements Specification  
**Version:** 1.0.0  
**Date:** November 2025  
**Competition:** UC Berkeley AgentBeats (Phase 2 – Purple Agent Challenge)  

---

## 🧩 User Story

### **Title**
As a **Purple Travel Agent**, I want to **help users design optimized and personalized travel itineraries** that balance **budget, experience, and safety**, so that I can **demonstrate intelligent reasoning, empathy, and structured planning** within the AgentBeats competition.

---

### **Context**
The **Purple Travel Agent** operates within the **AgentBeats A2A ecosystem** as a reasoning-based AI assistant.  
It interacts with **Green Evaluator Agents** or multi-agent systems via the **A2A (Agent-to-Agent) protocol** to generate, explain, and justify travel plans under specific constraints.

“Purple” symbolizes **rational creativity** — blending analytical planning (blue) and imaginative experience design (red).

---

### **Actors**
| Actor | Role |
|--------|------|
| **Primary:** Purple Travel Agent | The autonomous travel planner generating itineraries and reasoning. |
| **Secondary:** Green Evaluator Agent | Judge that sends prompts and scores performance. |
| **Supporting:** Scenario Runner / Orchestrator | Controls competition execution and evaluation. |
| **End User (Simulated)** | Represents the traveler’s preferences and constraints. |

---

### **Goal**
To produce **structured, well-reasoned travel itineraries** that:
- Align with traveler preferences (budget, theme, duration).  
- Reflect realistic constraints (geography, logistics, cultural factors).  
- Explain *why* each recommendation was made.

---

### **Motivation**
This agent showcases how AI can perform **practical reasoning**: synthesizing real-world context, empathy, and optimization.  
It models **autonomous task planning** — balancing user delight with logistics and ethics.

---

### **Functional Requirements**

| ID | Requirement | Description |
|----|--------------|-------------|
| FR-1 | **A2A Input Handling** | Accept A2A JSON requests with `destination`, `dates`, `budget`, `preferences`. |
| FR-2 | **Intent Understanding** | Detect the trip type (leisure, business, family, adventure). |
| FR-3 | **Itinerary Generation** | Produce multi-day itineraries with “Day-by-Day” structure. |
| FR-4 | **Reasoning Explanation** | Provide justification for each recommendation. |
| FR-5 | **Budget Adaptation** | Categorize recommendations as economy, moderate, or luxury. |
| FR-6 | **Safety Filters** | Exclude unsafe or restricted suggestions; flag uncertainty. |
| FR-7 | **Streaming** | Stream messages progressively (overview → daily plan → summary). |
| FR-8 | **Skill Declaration** | Register `travel.plan` and optionally `travel.budget`, `travel.optimize`. |
| FR-9 | **Card Endpoint** | Publish metadata at `/.well-known/agent-card.json`. |
| FR-10 | **Error Handling** | Return structured errors for invalid input. |

---

### **Non-Functional Requirements**

| ID | Requirement | Description |
|----|--------------|-------------|
| NFR-1 | **Latency** | Initial response within 5s; complete plan ≤ 20s. |
| NFR-2 | **Reproducibility** | Deterministic output under fixed seed. |
| NFR-3 | **Explainability** | Include rationale for each day’s plan. |
| NFR-4 | **Cultural Sensitivity** | Neutral, inclusive, respectful language. |
| NFR-5 | **Protocol Compliance** | Fully conform to A2A schema and endpoints. |
| NFR-6 | **Tone** | Warm, professional, human-like. |
| NFR-7 | **Portability** | Deploy via Docker or Uvicorn. |
| NFR-8 | **Safety** | No speculative or fabricated data. |

---



✅ When: the Purple Travel Agent receives it via A2A,

✅ Then: it streams:

**Day 1 – Tokyo Arrival**
Stay near Ueno for access to museums and markets.
Reasoning: Walking distance to attractions reduces local transport costs.

**Day 2 – Technology & Design**
TeamLab Planets, Akihabara, and Odaiba.
Reasoning: Combines tech focus with cultural immersion.


✅ And: includes a cost summary, assumptions, and reasoning tags in JSON metadata.

✅ And: Green Evaluator scores it on coherence, structure, and safety without protocol errors.

Success Metrics

Protocol compliance: ≥ 95%

Coherence & structure score: ≥ 80%

Cultural/safety compliance: 100%

Reproducibility: deterministic outputs

Evaluator satisfaction: ≥ 4/5

⚙️ Requirements Specification
1. Architecture Overview

Components

AgentExecutor → core reasoning and itinerary generation logic

EventQueue → streams responses

AgentCard → exposes metadata and skills

Uvicorn Server → handles A2A HTTP endpoints

Config / Seed → deterministic control

Safety Layer → filters unsafe or speculative content

Primary endpoint

http://localhost:7004/

2. AgentCard (JSON Example)
{
  "name": "Purple Travel Agent",
  "description": "Generates structured and explainable travel itineraries using reasoning and empathy.",
  "url": "http://localhost:7004/",
  "version": "1.0.0",
  "default_input_modes": ["text"],
  "default_output_modes": ["text"],
  "capabilities": { "streaming": true },
  "skills": [
    {
      "id": "travel.plan",
      "name": "Travel Planning",
      "description": "Creates personalized multi-day travel itineraries based on budget and interests.",
      "tags": ["travel", "planning", "itinerary", "reasoning"],
      "examples": [
        "Plan a 7-day food and culture trip to Japan.",
        "Design a 3-day weekend trip to Amsterdam under $1000."
      ]
    }
  ],
  "supports_authenticated_extended_card": false
}

3. A2A Request Example
{
  "request_id": "travel-2025-001",
  "sender": "green-evaluator-agent",
  "message": {
    "text": "Create a sustainable 5-day trip through Portugal focusing on culture and food."
  },
  "skill": "travel.plan"
}

4. Streaming Response Example
{
  "type": "agent_text_message",
  "timestamp": "2025-11-16T10:10:00Z",
  "message": {
    "text": "**Day 1 – Lisbon Arrival**\nStay in Alfama. Tram city tour.\nReasoning: Compact area reduces emissions and costs."
  }
}

5. Error Response
{
  "type": "error",
  "message": "Invalid request: missing destination field."
}

6. Deployment Requirements
Component	Specification
Runtime	Python ≥ 3.10
Libraries	a2a-sdk, uvicorn, pydantic, asyncio
Port	7004
Deployment	Docker or local host
Logging	JSON structured logs
Metrics	/metrics (optional Prometheus endpoint)
7. Dockerfile Example
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir a2a-sdk uvicorn pydantic
EXPOSE 7004
CMD ["python", "-m", "purple_travel_agent"]

8. Future Enhancements

Integrate real-time API data (weather, transport, safety).

Add multi-destination route optimization.

Include sustainability score and carbon estimate.

Support multilingual generation (English, German, Japanese).
