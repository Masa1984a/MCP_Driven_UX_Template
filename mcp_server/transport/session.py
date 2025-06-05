"""
Session management for Streamable HTTP transport.

Provides session creation, validation, state management, and cleanup
for MCP Streamable HTTP connections.
"""

import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .sse import SSEConnectionManager


@dataclass
class SessionData:
    """Session data container for Streamable HTTP sessions."""
    session_id: str
    connection_manager: SSEConnectionManager
    created_at: datetime
    last_activity: datetime
    state: Dict[str, Any] = field(default_factory=dict)
    auth_info: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


class SessionManager:
    """
    Manages MCP sessions for Streamable HTTP implementation.
    
    Provides session creation, validation, state management, and cleanup
    with thread-safe operations.
    """
    
    def __init__(self, max_age_minutes: int = 30):
        """
        Initialize session manager.
        
        Args:
            max_age_minutes: Maximum age for sessions before cleanup
        """
        self.sessions: Dict[str, SessionData] = {}
        self.max_age_minutes = max_age_minutes
        self._lock = threading.Lock()
    
    def create_session(self, auth_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new MCP session with cryptographically secure ID.
        
        Session ID MUST be:
        - Globally unique and cryptographically secure
        - Only contain visible ASCII characters (0x21 to 0x7E)
        
        Args:
            auth_info: Optional authentication information
            
        Returns:
            Generated session ID
        """
        import secrets
        import string
        
        # Generate cryptographically secure session ID with visible ASCII chars only
        # Characters 0x21-0x7E (33-126): !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~
        visible_ascii = string.ascii_letters + string.digits + string.punctuation
        # Remove space (0x20) as it's not in the range 0x21-0x7E
        visible_ascii = ''.join(c for c in visible_ascii if 0x21 <= ord(c) <= 0x7E)
        
        # Generate 32-character session ID for high entropy
        session_id = ''.join(secrets.choice(visible_ascii) for _ in range(32))
        
        with self._lock:
            # Ensure uniqueness (extremely unlikely collision, but check anyway)
            while session_id in self.sessions:
                session_id = ''.join(secrets.choice(visible_ascii) for _ in range(32))
            
            session_data = SessionData(
                session_id=session_id,
                connection_manager=SSEConnectionManager(),
                created_at=datetime.now(),
                last_activity=datetime.now(),
                auth_info=auth_info or {}
            )
            
            self.sessions[session_id] = session_data
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate session ID and check if session is active.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            True if session exists and is active
        """
        with self._lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            # Check if session is expired
            age = datetime.now() - session.created_at
            if age.total_seconds() > self.max_age_minutes * 60:
                # Mark as inactive and remove
                session.is_active = False
                del self.sessions[session_id]
                return False
            
            return session.is_active
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            SessionData object or None if not found
        """
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.last_activity = datetime.now()
                return session
            return None
    
    def get_connection_manager(self, session_id: str) -> Optional[SSEConnectionManager]:
        """
        Get SSE connection manager for session.
        
        Args:
            session_id: Session ID
            
        Returns:
            SSEConnectionManager instance or None if session not found
        """
        session = self.get_session(session_id)
        if session:
            return session.connection_manager
        return None
    
    def update_session_activity(self, session_id: str):
        """
        Update session last activity timestamp.
        
        Args:
            session_id: Session ID to update
        """
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].last_activity = datetime.now()
    
    def update_session_state(self, session_id: str, key: str, value: Any):
        """
        Update session state.
        
        Args:
            session_id: Session ID
            key: State key
            value: State value
        """
        session = self.get_session(session_id)
        if session:
            with self._lock:
                session.state[key] = value
    
    def get_session_state(self, session_id: str, key: str, default: Any = None) -> Any:
        """
        Get session state value.
        
        Args:
            session_id: Session ID
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        session = self.get_session(session_id)
        if session:
            return session.state.get(key, default)
        return default
    
    def remove_session(self, session_id: str) -> bool:
        """
        Remove session.
        
        Args:
            session_id: Session ID to remove
            
        Returns:
            True if session was removed
        """
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.is_active = False
                del self.sessions[session_id]
                return True
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired_sessions = []
        
        with self._lock:
            for session_id, session in self.sessions.items():
                # Check age
                age = now - session.created_at
                inactivity = now - session.last_activity
                
                if (age.total_seconds() > self.max_age_minutes * 60 or
                    inactivity.total_seconds() > self.max_age_minutes * 60 or
                    not session.is_active):
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                if session_id in self.sessions:
                    self.sessions[session_id].is_active = False
                    del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def get_active_session_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        with self._lock:
            return len([s for s in self.sessions.values() if s.is_active])
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information dictionary or None
        """
        session = self.get_session(session_id)
        if session:
            return {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_active": session.is_active,
                "state_keys": list(session.state.keys()),
                "auth_info": {k: "***" for k in session.auth_info.keys()}  # Hide sensitive data
            }
        return None