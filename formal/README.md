# Formal Verification — WebSocket Authentication Flow

## What Was Verified

The WebSocket authentication flow of the Distributed Chat System was formally verified 
using the SPIN Model Checker (v6.5.2). The specific safety property verified was:

> No message is ever processed by the server before authentication is complete, 
> under all possible concurrent execution orderings including active attacker injection.

---

## Why Formal Verification

Standard testing only checks specific cases. A server could pass all unit tests and 
still have a race condition where an attacker injects a message during the authentication 
handshake. Formal verification using model checking explores every possible execution 
path exhaustively — not just the happy path.

This is particularly important for WebSocket systems because connections are concurrent 
and stateful. The authentication gate must hold under all possible interleavings of 
client, server, and attacker actions.

---

## The Model

The Promela model (`websocket_auth.pml`) captures three concurrent processes:

**Client** — models a legitimate user going through the full authentication flow:
1. Sends a connection request
2. Receives acceptance from server
3. Sends a valid JWT token
4. Receives authentication confirmation
5. Only then sends a chat message

**Server** — models the backend authentication gate in two phases:
- Phase 1: Only processes connection and token validation messages. Never touches the 
  message channel during this phase.
- Phase 2: Only begins processing chat messages after authentication is confirmed. 
  Any message received in Phase 2 is guaranteed to be from an authenticated connection.

**Attacker** — models a malicious actor attempting to bypass authentication by sending 
chat messages directly to the message channel without completing the auth handshake.

---

## The Safety Property

A global boolean `message_processed_while_unauthenticated` is set to true if the server 
ever processes a message before authentication completes. The assertion:
```
assert(message_processed_while_unauthenticated == false)
```

must hold in every reachable state across all possible execution orderings.

---

## How to Run

Install SPIN from https://github.com/nimble-code/Spin and compile from source, 
then run:
```bash
spin -a websocket_auth.pml
gcc -o pan pan.c
./pan
```

---

## Result
```
Errors: 0
States explored: 254
Transitions: 383
Depth reached: 31
```

Zero assertion violations across all 254 reachable states and 383 transitions. 
SPIN explored every possible interleaving of the three processes including all 
attacker injection attempts and confirmed the safety property holds in every case.

The two unreached states in the Server process are the violation branches — they 
were never reached because the two-phase design makes it structurally impossible 
for the server to process a message before authentication completes.

---

## Connection to the Real System

This model directly reflects the WebSocket handler in `backend/api/routes/websocket.py`. 
The real implementation calls `get_current_user(token, db)` before entering the message 
loop — if authentication fails the connection is closed with code 1008 and no messages 
are ever processed. The formal model proves this gate holds under concurrent adversarial 
conditions that are difficult to test empirically.
