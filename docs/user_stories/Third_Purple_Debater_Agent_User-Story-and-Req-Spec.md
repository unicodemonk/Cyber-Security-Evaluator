# 🗣️ Purple Debater Agent – User Story & Requirements Specification  
**Version:** 1.0.0  
**Date:** November 2025  
**Competition:** UC Berkeley AgentBeats (Phase 2 – Purple Agent Challenge)  

---

## 🧩 User Story

### **Title**
As a **Purple Debater Agent**, I want to **engage in structured, persuasive debates** on assigned topics, presenting clear arguments and counterarguments, so that I can **demonstrate critical reasoning, communication, and fairness** during AgentBeats evaluations.

---

### **Context**
The **Purple Debater** operates in the **Berkeley AgentBeats ecosystem** under the **A2A (Agent-to-Agent) protocol**, interacting with **Green Evaluator Agents** (judges) and possibly other Purple participants.  
Its purpose is to emulate **human-like debate intelligence** — balancing rhetoric, logic, evidence, and ethics.

“Purple” signifies balance between **Red (creative argumentation)** and **Blue (analytical reasoning)** — producing an articulate, grounded, and responsible AI debater.

---

### **Actors**
| Actor | Role |
|--------|------|
| **Primary:** Purple Debater Agent | The reasoning AI that generates structured arguments and rebuttals. |
| **Secondary:** Green Evaluator Agent | Judge that initiates topics, scores debates, and enforces rules. |
| **Supporting:** Orchestrator (Scenario Runner) | Handles evaluation rounds and timing. |

---

### **Goal**
To generate **coherent, evidence-supported arguments** and **logical counterpoints** within time and token constraints, displaying:
- Comprehension of the motion or issue.
- Clear structure (stance → arguments → evidence → summary).
- Respectful, reasoned engagement.

---

### **Motivation**
The Purple Debater demonstrates **deliberative intelligence** — reasoning across multiple viewpoints, balancing assertiveness and humility.  
Its mission is not to “win,” but to **persuade responsibly** and **model ethical discourse**.

---

### **Functional Requirements**

| ID | Requirement | Description |
|----|--------------|-------------|
| FR-1 | **A2A Input Handling** | Accept debate prompts via A2A JSON requests with fields like `topic`, `stance`, and `round`. |
| FR-2 | **Argument Generation** | Formulate persuasive arguments with supporting evidence or analogies. |
| FR-3 | **Counterargument Handling** | Process opposing claims and generate rebuttals. |
| FR-4 | **Structure Enforcement** | Maintain 4-part structure: Position → 3 Points → Evidence → Takeaway. |
| FR-5 | **Evidence Attribution** | Include generalized references (e.g., “UN Report 2024”) rather than fabricated sources. |
| FR-6 | **Streaming Output** | Deliver content progressively (intro → points → conclusion). |
| FR-7 | **Skill Declaration** | Register `debate.argue` and `debate.rebut` in the AgentCard. |
| FR-8 | **Card Endpoint** | Publish metadata at `/.well-known/agent-card.json`. |
| FR-9 | **Error Handling** | Return structured A2A error messages for missing or invalid topics. |
| FR-10 | **Cancellation Support** | Gracefully terminate on A2A `cancel_request`. |

---

### **Non-Functional Requirements**

| ID | Requirement | Description |
|----|--------------|-------------|
| NFR-1 | **Latency** | Initial message < 3s; complete argument < 12s. |
| NFR-2 | **Consistency** | Deterministic outputs given same topic and stance. |
| NFR-3 | **Ethical Compliance** | No inflammatory or unverifiable claims. |
| NFR-4 | **Tone** | Neutral, articulate, and respectful. |
| NFR-5 | **Explainability** | Every argument point must include reasoning tags (“because”, “due to”, “as supported by”). |
| NFR-6 | **Protocol Compliance** | Fully A2A-compliant JSON messages. |
| NFR-7 | **Reproducibility** | Identical outputs under fixed seed. |

---

### **Acceptance Criteria**

✅ **Given:**  
```json
{
  "topic": "AI agents should be open source by default.",
  "stance": "Pro"
}
```

✅ **When:** The Purple Debater Agent receives it via A2A,  

✅ **Then:** It streams:  
```
**Position (Pro):**  
Open-sourcing AI agents promotes accountability and collaboration.

1. Transparency fosters trust — Open code enables public auditing of safety measures.  
2. Innovation accelerates — Shared research shortens development cycles.  
3. Risk mitigation — Collective oversight prevents monopolistic misuse.

Takeaway: Responsible openness improves progress and safety when paired with governance.
```

✅ **And:** Returns structured metadata:
```json
{
  "stance": "Pro",
  "confidence": 0.87,
  "sources": ["Nature AI Ethics 2025", "OECD Report 2024"]
}
```

✅ **And:** The Green Evaluator Agent parses it successfully and assigns debate scores.

---

### **Success Metrics**
- **A2A validation rate:** ≥ 95%  
- **Coherence score:** ≥ 85%  
- **Safety/ethics compliance:** 100%  
- **Response completeness:** ≥ 95% structured messages delivered  
- **Latency:** ≤ 12s for complete argument  

---

## ⚙️ Requirements Specification

### 1. **Architecture Overview**

**Components**
- `AgentExecutor` → Argument and rebuttal generator  
- `EventQueue` → Streams debate messages  
- `AgentCard` → Describes agent capabilities  
- `Uvicorn Server` → Serves A2A endpoints  
- `Safety Filter` → Blocks disallowed content  
- `Config / Seed` → Maintains determinism  

**Primary Endpoint**
```
http://localhost:7001/
```

---

### 2. **AgentCard (JSON Example)**
```json
{
  "name": "Purple Debater",
  "description": "Structured debate agent balancing analytical and creative reasoning.",
  "url": "http://localhost:7001/",
  "version": "1.0.0",
  "default_input_modes": ["text"],
  "default_output_modes": ["text"],
  "capabilities": { "streaming": true },
  "skills": [
    {
      "id": "debate.argue",
      "name": "Debate Argumentation",
      "description": "Formulates a structured argument for or against a motion.",
      "tags": ["debate", "reasoning", "persuasion"],
      "examples": [
        "Topic: 'Automation improves job quality' — stance: 'Con'."
      ]
    },
    {
      "id": "debate.rebut",
      "name": "Counterargument",
      "description": "Responds to opposing arguments with evidence and reasoning.",
      "tags": ["rebuttal", "critical-thinking"]
    }
  ],
  "supports_authenticated_extended_card": false
}
```

---

### 3. **A2A Request Example**
```json
{
  "request_id": "debate-2025-007",
  "sender": "green-evaluator-agent",
  "message": {
    "text": "Debate topic: 'AI should replace human drivers.'",
    "stance": "Con"
  },
  "skill": "debate.argue"
}
```

---

### 4. **Streaming Response Example**
```json
{
  "type": "agent_text_message",
  "timestamp": "2025-11-16T12:00:00Z",
  "message": {
    "text": "**Position (Con):** AI should not fully replace human drivers yet.\n1. Ethical readiness — humans remain accountable for safety-critical decisions.\n2. Edge cases — sensor systems fail in unpredictable real-world conditions.\n3. Regulation — legal frameworks still evolving.\nTakeaway: Coexistence before replacement ensures responsible innovation."
  }
}
```

---

### 5. **Error Response**
```json
{
  "type": "error",
  "message": "Invalid input: missing debate topic or stance."
}
```

---

### 6. **Deployment Requirements**

| Component | Specification |
|------------|----------------|
| **Runtime** | Python ≥ 3.10 |
| **Libraries** | `a2a-sdk`, `uvicorn`, `pydantic`, `asyncio` |
| **Port** | 7001 |
| **Deployment** | Docker or Uvicorn local service |
| **Logging** | JSON structured logs with timestamps |
| **Metrics** | Optional Prometheus endpoint `/metrics` |

---

### 7. **Dockerfile Example**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir a2a-sdk uvicorn pydantic
EXPOSE 7001
CMD ["python", "-m", "purple_debater"]
```

---

### 8. **Future Enhancements**
- Add **multi-round debates** (support for rebuttal chains).  
- Implement **argument confidence scoring**.  
- Support **speech timing controls** (short vs extended format).  
- Introduce **ethics classifier** to verify argument safety.  
- Enable **multi-agent team debates** (Purple vs Purple).  

---

## **Security Vulnerabilities Analysis**

The **Purple Debater Agent** described in the user story and specification for the UC Berkeley AgentBeats competition presents several security vulnerabilities and risks, mostly associated with its architecture, data flow, protocol exposure, and the nature of AI-driven debate systems. Here’s an organized breakdown of potential security vulnerabilities relevant to this use case:

---

## 1. **Input Handling and Injection Risks**
- **A2A JSON Input Handling**: If user-supplied debate inputs are not rigorously validated and sanitized, there’s risk of:
  - **Injection Attacks:** Maliciously crafted JSON could exploit parsing vulnerabilities (e.g., prototype pollution, code or command injection in underlying frameworks).
  - **Denial of Service (DoS):** Large, malformed, or recursive payloads could degrade service or cause application failure.
  - **Prompt Injection:** Debater models can be manipulated by cleverly worded prompts to output undesirable or unsafe content.

---

## 2. **Streaming & Output Risks**
- **Progressive/Streaming Output**: If message chunks are not validated before release:
  - **Information Leakage:** Partial responses might inadvertently expose internal states, error traces, or debugging data.
  - **Revealing Sensitive Metadata:** Structuring responses with source lists or confidence scores can be abused to infer agent operation, enabling model exploitation or adversarial probing.

---

## 3. **AgentCard Endpoint Exposure**
- **Public Metadata (`/.well-known/agent-card.json`)**:
  - **Reconnaissance Vector:** Discloses agent capabilities and skills, aiding attackers in crafting targeted payloads or social engineering attacks.
  - **Potential Disclosure of Operating URLs:** Reveals internal network architecture or endpoints if not properly limited.

---

## 4. **Error Reporting**
- **Structured Error Messages**: Overly detailed errors (stack traces, config values, etc.) could:
  - **Facilitate Exploitation:** Give clues to attackers about internal logic or software versions.
  - **Expose Private Data:** If error handling isn’t strictly controlled, sensitive request fields may leak.

---

## 5. **AI Model Toxicity, Safety and Ethics**
- **Malicious Argument Generation**:
  - **Unverifiable Claims & Misinformation:** Despite NFR-3, adversarial inputs may trick the agent into generating unethical or unsafe content.
  - **Prompt Leaking:** Generated responses could include sensitive instructions if the model is not fully controlled.
- **Safety Filter Failure**:
  - If the safety filter is bypassed or malfunctioning, the agent could output inflammatory, toxic, or non-compliant content.

---

## 6. **Authentication & Protocol Risks**
- **A2A Protocol Abuse**:
  - **Spoofed Requests:** Without request attribution and verification, attackers may impersonate legitimate agents (e.g., the Green Evaluator).
  - **Replay Attacks:** Previously valid debate requests could be resent, causing repeated, possibly undesirable argument generation.
  - **DoS via Protocol:** Excessive requests, cancels, or invalid operations could disrupt agent operation.

---

## 7. **Deployment & Runtime Risks**
- **Exposed Port (7001)**:
  - **Open Attack Surface:** If deployed without proper firewalls or authentication, may be subject to external probing, port scanning, or exploitation.
- **Dependencies**:
  - **Unpatched Libraries:** Vulnerabilities in `a2a-sdk`, `uvicorn`, `pydantic` or system Python can be exploited if not regularly updated.
- **Docker Image Risks**:
  - **Privileged Containers:** If container security best practices aren’t followed, attackers could escalate privileges or escape the container.

---

## 8. **Logging and Metrics**
- **Sensitive Data in Logs**:
  - If JSON logs include debate topics, stances, arguments, or internal metrics, attackers with log access could glean sensitive info.
- **Metrics Endpoint (`/metrics`)**:
  - Exposing internal performance, usage, or error rates publicly can aid attackers in timing or load-based exploits.

---

## 9. **Reproducibility and Determinism**
- **Seed Disclosure**:
  - Deterministic output seeds, if visible or guessable, may allow attackers to reliably predict or manipulate agent responses.

---

## 10. **Future Enhancements**
- **Multi-Agent Interactions:** Team debates and rebuttal chains expand trust boundaries and protocol complexity, introducing new surface for spoofing, Sybil attacks, or unauthorized coordination.

---

# **Mitigation Suggestions**
- Strict input/output validation (reject oversized or malformed JSON).
- Limit information in error messages and logs.
- Authenticate and authorize all protocol endpoints; implement strict sender verification.
- Monitor and rate-limit requests to mitigate DoS.
- Keep dependencies updated and monitor for CVEs.
- Harden container, restrict network access, implement firewall rules.
- Regularly audit AI model outputs and retrain safety filter.
- Ensure reproducibility seed is kept secret or regularly changed.
- Secure metrics and logging endpoints; don’t expose public data.

---

**Summary:**  
The Purple Debater Agent’s use case is exposed to security vulnerabilities typical of API-based AI systems: injection attacks, output validation failures, protocol spoofing, information leakage, unfiltered AI output, endpoint exposure, and unsafe container or dependency management. Security hardening is essential at every layer—from input, output, and protocol design, to runtime deployment and logging.


**© 2025 Purple Agent Initiative — UC Berkeley AgentBeats Entry**
