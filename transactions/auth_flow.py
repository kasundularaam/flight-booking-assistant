# transactions/auth_flow.py
from dataclasses import dataclass
from typing import Optional, Dict, Any


class AuthFlowStates:
    INIT = "INIT"
    AWAITING_EMAIL = "AWAITING_EMAIL"
    AWAITING_PASSWORD = "AWAITING_PASSWORD"
    AWAITING_NAME = "AWAITING_NAME"
    COMPLETE = "COMPLETE"


class AuthFlow:
    def __init__(self, auth_service, parent_transaction):
        self.auth_service = auth_service
        self.parent_transaction = parent_transaction
        self.state = AuthFlowStates.INIT
        self.context = {
            'action': None,  # 'login' or 'register'
            'email': None,
            'password': None,
            'name': None
        }

    def process(self, message: str) -> str:
        if self.state == AuthFlowStates.INIT:
            return self._handle_init(message)
        elif self.state == AuthFlowStates.AWAITING_EMAIL:
            return self._handle_email(message)
        elif self.state == AuthFlowStates.AWAITING_PASSWORD:
            return self._handle_password(message)
        elif self.state == AuthFlowStates.AWAITING_NAME:
            return self._handle_name(message)
        return "An error occurred in authentication."

    def _handle_init(self, message: str) -> str:
        message = message.lower()
        if 'register' in message or 'sign up' in message:
            self.context['action'] = 'register'
            response = "Let's create an account. Please enter your email:"
        else:
            self.context['action'] = 'login'
            response = "Please enter your email to login:"

        self.state = AuthFlowStates.AWAITING_EMAIL
        return response

    def _handle_email(self, message: str) -> str:
        self.context['email'] = message
        self.state = AuthFlowStates.AWAITING_PASSWORD
        return "Please enter your password:"

    def _handle_password(self, message: str) -> str:
        self.context['password'] = message

        if self.context['action'] == 'login':
            success, msg = self.auth_service.login(
                email=self.context['email'],
                password=self.context['password']
            )
            if success:
                self.state = AuthFlowStates.COMPLETE
                return f"{msg}\nNow, let's continue with your booking."
            return f"{msg}\nPlease try again with your email:"
        else:
            self.state = AuthFlowStates.AWAITING_NAME
            return "Please enter your name:"

    def _handle_name(self, message: str) -> str:
        self.context['name'] = message
        success, msg = self.auth_service.register(
            name=self.context['name'],
            email=self.context['email'],
            password=self.context['password']
        )
        if success:
            self.state = AuthFlowStates.COMPLETE
            return f"{msg}\nNow, let's continue with your booking."
        self.state = AuthFlowStates.AWAITING_EMAIL
        return f"{msg}\nPlease try again with your email:"

    @property
    def is_complete(self) -> bool:
        return self.state == AuthFlowStates.COMPLETE
