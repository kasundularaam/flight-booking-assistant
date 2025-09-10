# transactions/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .auth_flow import AuthFlow


class BaseTransaction(ABC):
    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.auth_service = chatbot.auth_service
        self.context: Dict[str, Any] = {}
        self.auth_flow: Optional[AuthFlow] = None
        self._paused_for_auth = False

    @property
    def requires_auth(self) -> bool:
        """Override this in transactions that require authentication"""
        return False

    def check_and_handle_auth(self, message: str) -> Optional[str]:
        """
        Check authentication and handle auth flow if needed
        Returns: auth flow response if handling auth, None if authenticated
        """
        if not self.requires_auth:
            return None

        if not self.auth_service.is_authenticated():
            if not self.auth_flow:
                # First time hitting auth requirement
                self.auth_flow = AuthFlow(self.auth_service, self)
                self._paused_for_auth = True
                return "You need to be logged in first. Would you like to login or register?"

            # Continue with auth flow
            response = self.auth_flow.process(message)
            if self.auth_flow.is_complete:
                self.auth_flow = None
                self._paused_for_auth = False
                return f"{response}"
            return response

        return None

    def process(self, message: str) -> str:
        """
        Process incoming message
        Override this in subclasses but call super().process() first
        """
        # Check if we need to handle auth
        auth_response = self.check_and_handle_auth(message)
        if auth_response:
            return auth_response

        # Continue with normal transaction processing
        return self._process_internal(message)

    @abstractmethod
    def _process_internal(self, message: str) -> str:
        """Internal processing method to be implemented by subclasses"""
        pass

    @property
    def is_complete(self) -> bool:
        return False

    def cleanup(self) -> None:
        self.context.clear()
        self.auth_flow = None
        self._paused_for_auth = False
