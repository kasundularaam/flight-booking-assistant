from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import date
from services.auth import Auth, UserInfo
from services.booking import BookingService
from services.flight import FlightService
from intent_classifier import IntentClassifier
from transactions.factory import TransactionFactory
from transactions.transaction import BaseTransaction


class FlightBookingChatbot:
    def __init__(self):
        self.auth_service = Auth()
        self.intent_classifier = IntentClassifier()
        self.current_transaction = None

    def _get_intent(self, message: str) -> str:
        """Classify the user's intent from their message"""
        try:
            return self.intent_classifier.predict(message)
        except ValueError:
            return "unknown"

    def _handle_unknown_intent(self) -> str:
        """Handle cases where intent couldn't be determined"""
        return "I'm not sure I understand. Could you please rephrase that?"

    def process_message(self, message: str) -> str:
        # If there's an active transaction, continue with it
        if self.current_transaction and not self.current_transaction.is_complete:
            response = self.current_transaction.process(message)
            if self.current_transaction.is_complete:
                self.current_transaction.cleanup()
                self.current_transaction = None
            return response

        # No active transaction, classify intent and create new transaction
        intent = self._get_intent(message)
        transaction = TransactionFactory.create_transaction(intent, self)

        if transaction:
            self.current_transaction = transaction
            return transaction.process(message)

        return self._handle_unknown_intent()

    def start_chat(self) -> None:
        """Start the chat loop"""
        print("Bot: Hello! Welcome to Berry Airlines. How can I help you today?")

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("Bot: Thank you for using Berry Airlines. Goodbye!")
                    break

                response = self.process_message(user_input)
                print(f"Bot: {response}")

            except KeyboardInterrupt:
                print("\nBot: Goodbye!")
                break
            except Exception as e:
                print(f"Bot: I encountered an error: {str(e)}")
                print("Bot: Let's start over. How can I help you?")
                self.current_transaction = None


if __name__ == "__main__":
    chatbot = FlightBookingChatbot()
    chatbot.start_chat()
