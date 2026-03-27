# 💬 Distributed Chat System 🗨️
## Overview
A full-stack distributed messaging platform built with FastAPI, React, and Redis,
with WebSocket authentication safety formally verified using the SPIN Model Checker.

The system supports multi-server message broadcast via Redis pub/sub and extends
core chat with an AI sidecar for semantic search and channel summarization, running
as a fully decoupled async service that never blocks message delivery.

_> Live demo requires local setup, the AI features depend on locally loaded ML models
> and a seeded local database. Clone and follow the setup instructions below._

## Features
- Real-time messaging via WebSockets with presence tracking
- Distributed architecture with Redis pub/sub for cross-server communication
- Semantic search using FAISS vector store and sentence-transformers embeddings
- AI channel summarization via Gemini API with streaming response
- JWT authentication with bcrypt password hashing
- Formal verification of WebSocket authentication flow using SPIN Model Checker

## Architecture
Three independent layers communicate through a message queue so real-time performance
is never blocked by storage or AI processing.

The **real-time layer** manages WebSocket connections, message routing, and presence
tracking. Every message is published to Redis immediately on receipt. Multiple server
instances stay in sync via pub/sub, a message sent to instance A is broadcast to
users on instance B.

The **persistence layer** uses PostgreSQL via SQLAlchemy for users, channels, and
message history. A FAISS vector store maintains embeddings of all messages, updated
asynchronously after every save.

The **AI sidecar** is a completely decoupled async service that subscribes to the
message stream and processes in the background, semantic embeddings via
sentence-transformers, channel summaries on demand via Gemini API. If it goes down,
core chat continues unaffected.

<img width="1410" height="1202" alt="image" src="https://github.com/user-attachments/assets/b62f936e-3632-43c8-9106-2f0f6cf93f53" />


## Tech Stack
| Layer        | Technology                                    |
|--------------|-----------------------------------------------|
| Backend      | Python, FastAPI, SQLAlchemy, WebSockets       |
| Frontend     | React 18, Vite, Tailwind CSS, Zustand         |
| Database     | PostgreSQL                                    |
| Cache        | Redis                                         |
| AI           | sentence-transformers, FAISS, Gemini API      |
| Verification | SPIN Model Checker, Promela                   |

## Formal Verification
The WebSocket authentication flow was verified using SPIN Model Checker (v6.5.2).
A Promela model captures three concurrent processes — a legitimate client, a server,
and an attacker attempting to inject messages without authenticating.

**Safety property verified:** no message is ever processed before authentication
completes, across all possible concurrent execution orderings.

SPIN explored 254 states and 383 transitions with zero assertion violations —
formally proving the authentication gate holds under adversarial conditions.
The model is in the `formal/` directory.

## How to Run
### Backend
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your credentials
python -m uvicorn main:app --reload
```
### Frontend
```
cd frontend
npm install
npm run dev
```
