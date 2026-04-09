def get_history(session_state):
    if "history" not in session_state:
        session_state.history = []
    return session_state.history

def update_history(session_state, message):
    session_state.history.append(message)