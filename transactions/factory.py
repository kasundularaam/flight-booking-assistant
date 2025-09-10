from typing import Optional
from transactions.booking import BookingTransaction
from transactions.status import StatusTransaction
from transactions.transaction import BaseTransaction


class TransactionFactory:
    _transactions = {
        'booking': BookingTransaction,
        'status': StatusTransaction,
        # Add more transaction types here
    }

    @classmethod
    def create_transaction(cls, intent: str, chatbot) -> Optional[BaseTransaction]:
        transaction_class = cls._transactions.get(intent)
        if transaction_class:
            return transaction_class(chatbot)
        return None
