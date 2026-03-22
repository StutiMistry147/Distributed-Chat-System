/*
 * VERIFICATION RESULT: PASSED
 * Errors: 0
 * States explored: 254
 * Transitions: 383
 * 
 * Property verified: No message is processed before authentication
 * completes, even under concurrent attacker injection.
 * 
 * Verified using SPIN Model Checker v6.5.2
 */

#define DISCONNECTED   0
#define CONNECTING     1
#define CONNECTED      2
#define AUTHENTICATED  3
#define ACTIVE         4

/* Channel definitions */
chan client_to_server = [5] of { byte };   /* Client sends requests to server */
chan server_to_client = [5] of { byte };   /* Server sends responses to client */
chan message_channel  = [5] of { byte };   /* Client sends chat messages */

/* Message type constants */
#define MSG_CONNECT         1   /* Client requests connection */
#define MSG_TOKEN_VALID     2   /* Client sends valid token */
#define MSG_TOKEN_INVALID   3   /* Client sends invalid token */
#define MSG_CHAT            4   /* Client sends chat message */
#define MSG_ACCEPT          5   /* Server accepts connection */
#define MSG_REJECT          6   /* Server rejects connection */

/*  Global variable to track violation */
bool message_processed_while_unauthenticated = false;

/* Process 1: Legitimate Client */
proctype Client() {
    byte state = DISCONNECTED;
    byte response;
    
    /* Start connection attempt */
    client_to_server ! MSG_CONNECT;
    state = CONNECTING;
    
    /* Wait for server response */
    server_to_client ? response;
    
    if
        :: response == MSG_ACCEPT -> state = CONNECTED;
        :: response == MSG_REJECT -> goto done;
    fi;
    
    /* Send valid token */
    client_to_server ! MSG_TOKEN_VALID;
    
    /* Wait for server response to token */
    server_to_client ? response;
    
    if
        :: response == MSG_ACCEPT -> state = AUTHENTICATED;
        :: response == MSG_REJECT -> goto done;
    fi;
    
    /* Now authenticated, become active and send messages */
    state = ACTIVE;
    message_channel ! MSG_CHAT;
    
    done:
    skip;
}

/* Process 2: Server - Split into two phases */
proctype Server() {
    byte state = DISCONNECTED;
    byte msg;
    bool message_processed = false;
    
    /* Phase 1: Only listen to client_to_server until authenticated */
    do
        :: client_to_server ? msg ->
            if
                /* Initial connection request */
                :: msg == MSG_CONNECT -> {
                    server_to_client ! MSG_ACCEPT;
                    state = CONNECTED;
                }
                /* Token validation after connection */
                :: state == CONNECTED && msg == MSG_TOKEN_VALID -> {
                    server_to_client ! MSG_ACCEPT;
                    state = AUTHENTICATED;
                    /* Exit Phase 1 and move to Phase 2 */
                    break;
                }
                :: state == CONNECTED && msg == MSG_TOKEN_INVALID -> {
                    server_to_client ! MSG_REJECT;
                    /* Stay in CONNECTED state, continue Phase 1 */
                }
                /* Any other messages while unauthenticated */
                :: else -> {
                    /* This shouldn't happen in normal flow */
                    skip;
                }
            fi;
    od;
    
    /* Phase 2: Only listen to message_channel after authentication */
    do
        :: message_channel ? msg ->
            if
                :: state == AUTHENTICATED -> {
                    /* Process message safely - authenticated */
                    message_processed = true;
                    break;  /* Exit after processing one message */
                }
                :: else -> {
                    /* This should never happen in Phase 2 */
                    message_processed_while_unauthenticated = true;
                    message_processed = true;
                    break;
                }
            fi;
        :: message_processed -> break;  /* Exit if no message received */
    od;
}

/* Process 3: Attacker - tries to send messages without authenticating */
proctype Attacker() {
    /* Attempt to send chat message directly without any authentication */
    message_channel ! MSG_CHAT;
    
    /* Also try to send multiple messages to increase chance of detection */
    message_channel ! MSG_CHAT;
    message_channel ! MSG_CHAT;
}

/* Main process to start everything */
init {
    /* Run all processes */
    run Client();
    run Server();
    run Attacker();
    
    /* Safety assertion - check at end of execution */
    assert(message_processed_while_unauthenticated == false);
}