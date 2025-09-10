from transactions.transaction import BaseTransaction


class StatusTransaction(BaseTransaction):
    def __init__(self, chatbot):
        super().__init__(chatbot)
        self.context['booking_ref'] = None

    def process(self, message: str) -> str:
        # Example implementation
        if not self.context.get('booking_ref'):
            self.context['booking_ref'] = message
            return "Processing status for booking: " + message
        return "Status check complete"

    @property
    def is_complete(self) -> bool:
        return bool(self.context.get('booking_ref'))
