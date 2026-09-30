"""Conversation memory: track last N turns per session."""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("parakh.memory")

# In-memory session store: {session_id: [(question, answer), ...]}
_sessions: Dict[str, List[Tuple[str, str]]] = {}

MAX_TURNS = 5  # Keep last 5 turns per session


def add_turn(session_id: str, question: str, answer: str) -> None:
    """Add a Q&A turn to the session history."""
    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append((question, answer))

    # Keep only last MAX_TURNS
    if len(_sessions[session_id]) > MAX_TURNS:
        _sessions[session_id] = _sessions[session_id][-MAX_TURNS:]

    logger.info(f"Added turn to session {session_id} (total: {len(_sessions[session_id])} turns)")


def get_history(session_id: str) -> str:
    """Get formatted conversation history for context."""
    if session_id not in _sessions or not _sessions[session_id]:
        return ""

    lines = []
    for i, (q, a) in enumerate(_sessions[session_id], 1):
        # Truncate very long answers
        a_short = a[:200] + "..." if len(a) > 200 else a
        lines.append(f"Turn {i}:\nUser: {q}\nAssistant: {a_short}")

    return "\n\n".join(lines)


def clear_session(session_id: str) -> None:
    """Clear history for one session."""
    if session_id in _sessions:
        del _sessions[session_id]
        logger.info(f"Cleared session {session_id}")


def append_to_history(session_id: str, question: str, answer: str) -> None:
    """Append a turn to the session history (alias for add_turn for backward compatibility)."""
    add_turn(session_id, question, answer)
