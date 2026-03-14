# Hackathon Use Case Catalogue

> **Source:** Microsoft Global Partner Hackathon — Capgemini portal  
> **Purpose:** Reference catalogue of standout use cases for future development  
> **Last updated:** 2026-03-14

---

## Quick Reference

| # | Domain | Title | Tech Highlighted |
|---|--------|-------|-----------------|
| 1 | Healthcare | Multi-agent patient triage system | Azure Agent Framework (code-first) |
| 2 | Healthcare | M365 Copilot clinical documentation | M365 Copilot, Copilot Studio, Power Platform |
| 3 | Sales & Marketing | Fine-tuned brand content model | Mistral AI fine-tuning on Azure |
| 4 | Human Resources | Closed-loop recruiting automation | Copilot + Dynamics 365 HR |
| 5 | Technology / IT | AI project management & IT ticketing | Copilot, D365, Azure DevOps |
| 6 | Technology / IT | Private codebase assistant (custom LLM) | Mistral fine-tuning on Azure |
| 7 | Agentic DevOps | Agentic DevOps automation | Azure + GitHub agentic AI |
| 8 | Employee Experience | Multimodal Learn Knowledge Agent | Copilot Studio / Foundry, Teams, MCP |
| 9 | Employee Experience | Role-based onboarding agent | Agentic Contract, Copilot Studio / Foundry |

---

## Healthcare

### 1. Multi-agent patient triage system

**Problem Statement**

Overburdened medical staff and heavy paperwork lead to slower patient service and clinician burnout. Automated assistants (like triage bots and documentation aides) can handle routine tasks, schedule appointments, and support clinical decisions, easing administrative burdens and improving patient care.

**Overview**

Develop a multi-agent system on Azure to streamline patient triage and care coordination. Using a code-first approach with frameworks like Microsoft's Agent Framework, implement specialized agents for tasks such as symptom checking, priority classification, diagnostics assistance, care planning, and appointment scheduling.

---

### 2. M365 Copilot clinical documentation

**Problem Statement**

Overburdened medical staff and heavy paperwork lead to slower patient service and clinician burnout. Automated assistants (like triage bots and documentation aides) can handle routine tasks, schedule appointments, and support clinical decisions, easing administrative burdens and improving patient care.

**Overview**

Use Microsoft 365 Copilot in Outlook/Teams to auto-summarize doctor-patient conversations, draft clinical reports, and manage referrals. Through Copilot Studio and Power Platform, build low-code virtual health assistants (e.g. a patient Q&A chatbot or an internal "clinical assistant") that handle common inquiries and paperwork, freeing clinicians to focus on direct patient care.

---

## Sales & Marketing

### 3. Fine-tuned brand content model

**Problem Statement**

Campaign management must plan, design, execute, and supervise campaigns across territories while proving impact. The challenge is to turn performance and brand insights into the right territory selection and compliant collateral, coordinate approvals and content requests, activate sales engagement, track conversions end-to-end, and continuously adjust campaigns without delays or inconsistent messaging.

**Overview**

A custom model fine-tuned on your best-performing campaigns, brand tone, and compliance rules generates on-brand content and flags risky wording. Example: it rewrites an email subject line to match your style guide, inserts approved disclaimers, and warns if a claim exceeds policy. Fine-tuning on Mistral AI models supports it by learning your brand voice, product vocabulary, and regional constraints, improving consistency beyond generic LLM outputs.

---

## Human Resources

### 4. Closed-loop recruiting automation

**Problem Statement**

Recruiters and HR staff are overwhelmed by manual hiring tasks (scanning resumes, scheduling interviews) and repetitive employee queries, leaving less time for strategic talent development. AI can automate recruiting workflows (resume screening, interview scheduling, candidate Q&A) and power HR chatbots and analytics, improving hiring efficiency and employee support.

**Overview**

Integrate Copilot with Dynamics 365 Human Resources — recruiting becomes closed-loop from candidate to hire with automation across scheduling, feedback, and approvals. Example: once a candidate is shortlisted, the system proposes interview panels, schedules calendars, collects structured scorecards, and routes offers for approval while tracking time-to-hire and drop-off reasons. Dynamics supports it with a unified process and data model, workflow automation, role-based access, and dashboards for compliance and performance.

---

## Technology / IT

### 5. AI project management & IT support ticketing

**Problem Statement**

Software developers and IT support teams contend with repetitive tasks (boilerplate coding, code reviews, routine support tickets) that consume time and slow innovation. Generative AI can serve as a coding co-pilot to accelerate development (auto-writing code, tests, documentation) and as an autonomous assistant in IT operations (auto-resolving common issues and analyzing system logs), improving productivity and system reliability.

**Overview**

Integrate AI into project management and IT support by using tools like Copilot with D365 or Azure DevOps to track progress, predict delays, and manage resources. In IT service, AI can summarize tickets, suggest solutions, and draft responses, improving response times and system oversight.

---

### 6. Private codebase assistant (custom LLM)

**Problem Statement**

Software developers and IT support teams contend with repetitive tasks (boilerplate coding, code reviews, routine support tickets) that consume time and slow innovation. Generative AI can serve as a coding co-pilot to accelerate development (auto-writing code, tests, documentation) and as an autonomous assistant in IT operations (auto-resolving common issues and analyzing system logs), improving productivity and system reliability.

**Overview**

Train a custom Mistral LLM on the client's industry terminology, client's code, documentation, and runbooks using Azure. This tailored model, deployed on Azure, serves as a private assistant that understands the company coding style and architecture, helps improve GitHub to generate code, debug errors, and answer troubleshooting questions.

---

## Agentic DevOps

### 7. Agentic DevOps automation

**Problem Statement**

Software developers and IT support teams contend with repetitive tasks (boilerplate coding, code reviews, routine support tickets) that consume time and slow innovation. Generative AI can serve as a coding co-pilot to accelerate development (auto-writing code, tests, documentation) and as an autonomous assistant in IT operations (auto-resolving common issues and analyzing system logs), improving productivity and system reliability.

**Overview**

Use Azure and GitHub to transform software development with agentic AI. Design use cases for AI automation, develop AI agents, and integrate them into GitHub workflows.

---

## Employee Experience

### 8. Multimodal Microsoft Learn Knowledge Agent

**Problem Statement**

Employees still face fragmented, manual, and inconsistent support experiences across IT, workplace, and learning services. Repetitive tasks and disconnected systems slow productivity and limit personalization. AI-powered, multimodal, and proactive agents are needed to unify onboarding, workplace interactions, and knowledge access into a seamless, anticipatory employee experience.

**Overview**

Develop a multimodal "Microsoft Learn Knowledge Agent" using Copilot Studio or Foundry that integrates both voice and chat channels within a single Microsoft Teams application. This AI-powered agent will access information from the publicly available Microsoft Learn MCP server to answer user questions, seamlessly transitioning between chat and voice interactions while preserving conversational context. Furthermore, the agent should create a short assessment consisting of several questions and suggest appropriate Microsoft Learn resources by generating a personalized learning path to assist users in enhancing their skills in their chosen fields.

---

### 9. Role-based onboarding agent (Agentic Contract)

**Problem Statement**

Employees still face fragmented, manual, and inconsistent support experiences across IT, workplace, and learning services. Repetitive tasks and disconnected systems slow productivity and limit personalization. AI-powered, multimodal, and proactive agents are needed to unify onboarding, workplace interactions, and knowledge access into a seamless, anticipatory employee experience.

**Overview**

Develop a unified onboarding AI agent that follows the procedures detailed in the Knowledge article (Agentic Contract), clearly outlining the steps and tools involved. The system should provide users with proactive prompts to initiate the onboarding process, while also allowing them to start it manually if preferred. The agent must apply different agentic contracts based on the user's profile; for example, employees in Sales will undergo a different onboarding sequence than those in Engineering. This agent will be used for onboarding employees both to the company and to new roles within it.

---

## 💡 Build Ideas

> Use this section as a scratchpad when you're ready to develop one of the above into a project.

<!-- Add notes here -->
