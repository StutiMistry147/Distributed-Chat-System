# Distributed Chat System
## Overview
A full-stack distributed real-time messaging platform built with FastAPI, React, and Redis. 
The system supports multi-server architecture where messages are broadcast across server 
instances via Redis pub/sub, ensuring no message is lost under concurrent load. Extends 
core chat functionality with an AI sidecar for semantic message search and channel 
summarization, both running as decoupled async services that never block message delivery.

## Features
- Real-time messaging via WebSockets with presence tracking
- Distributed architecture with Redis pub/sub for cross-server communication
- Semantic search using FAISS vector store and sentence-transformers embeddings
- AI channel summarization via Gemini API with streaming response
- JWT authentication with bcrypt password hashing
- Formal verification of WebSocket authentication flow using SPIN Model Checker

## Architecture
The system is built across three independent layers that communicate through a message 
queue, ensuring real-time performance is never blocked by storage or AI processing.

The real-time layer manages WebSocket connections, message routing across channels, and 
user presence tracking. Every message is published to a Redis queue immediately on receipt, 
decoupling delivery from storage and AI processing. Multiple server instances stay in sync 
through Redis pub/sub so a message sent to instance A is broadcast to users connected to 
instance B.

The persistence layer uses PostgreSQL via SQLAlchemy to store users, servers, channels, 
and full message history. A FAISS vector store maintains embeddings of all messages, 
updated asynchronously by the AI sidecar after every message save.

The AI sidecar is a completely decoupled async service that subscribes to the message 
stream and processes messages in the background. It embeds every incoming message using 
sentence-transformers for semantic search, and generates channel summaries on demand via 
the Gemini API. If the AI sidecar goes down, core chat continues unaffected.

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

## Formal Verification
The WebSocket authentication flow was formally verified using the SPIN Model Checker 
(v6.5.2) with a Promela model capturing three concurrent processes — a legitimate client, 
a server, and an active attacker attempting to inject messages without authenticating. 
The safety property verified was: no message is ever processed by the server before 
authentication is complete, under all possible concurrent execution orderings. SPIN 
explored 254 states and 383 transitions with zero assertion violations, formally proving 
the authentication gate holds even under adversarial conditions. The model is located in 
the formal/ directory.

<ins>Note: Live demo requires local setup. The AI features (semantic search, channel summarization) depend on locally loaded ML models, and the database is seeded with local data. Clone the repo and follow the setup instructions to run it fully.</ins>
