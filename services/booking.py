from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
import string
import random
from decimal import Decimal
from utils.database import Booking
from services.flight import Trip


@dataclass
class BookingInfo:
    """Data class to represent booking information without exposing ORM details"""
    id: int
    reference: str
    trip_type: str
    outbound_flight_id: int
    return_flight_id: Optional[int]
    travel_class: str
    created_at: datetime
    user_id: int
    total_amount: float

    @classmethod
    def from_orm(cls, booking: Booking) -> 'BookingInfo':
        """Convert Booking ORM object to BookingInfo"""
        return cls(
            id=booking.id,
            reference=booking.reference,
            trip_type=booking.trip_type,
            outbound_flight_id=booking.outbound_flight.id,
            return_flight_id=booking.return_flight.id if booking.return_flight else None,
            travel_class=booking.travel_class,
            created_at=booking.created_at,
            user_id=booking.user.id,
            total_amount=float(booking.total_amount)
        )


class BookingService:
    """Service class for managing flight bookings"""

    # Class constants
    VALID_TRAVEL_CLASSES = frozenset({'FIRST', 'BUSINESS', 'ECONOMY'})
    REFERENCE_LENGTH = 6

    @staticmethod
    def _generate_reference() -> str:
        """
        Generate a unique booking reference

        Returns:
            str: A unique 6-character reference code
        """
        while True:
            chars = string.ascii_uppercase + string.digits
            reference = ''.join(random.choice(chars)
                                for _ in range(BookingService.REFERENCE_LENGTH))

            exists = Booking.select().where(Booking.reference == reference).exists()
            if not exists:
                return reference

    def _calculate_total_amount(self, trip: Trip, travel_class: str) -> Decimal:
        """
        Calculate total amount based on travel class

        Args:
            trip: Trip object containing flight details
            travel_class: Selected travel class

        Returns:
            Decimal: Total amount for the booking
        """
        if travel_class == 'FIRST':
            return trip.get_first_class_price()
        elif travel_class == 'BUSINESS':
            return trip.get_business_class_price()
        return trip.get_economy_class_price()  # ECONOMY

    def create_booking(
        self,
        trip: Trip,
        user_id: int,
        travel_class: str
    ) -> BookingInfo:
        """
        Create a new booking for a trip

        Args:
            trip: Trip object containing flight details
            user_id: ID of the user making the booking
            travel_class: Selected travel class (FIRST, BUSINESS, or ECONOMY)

        Returns:
            BookingInfo: Object with the created booking details

        Raises:
            ValueError: If invalid travel class or trip type
            DoesNotExist: If user or flights not found
        """
        if travel_class not in self.VALID_TRAVEL_CLASSES:
            raise ValueError(
                f"Invalid travel class. Must be one of: {
                    ', '.join(self.VALID_TRAVEL_CLASSES)}"
            )

        total_amount = self._calculate_total_amount(trip, travel_class)

        booking = Booking.create(
            reference=self._generate_reference(),
            trip_type=trip.trip_type,
            outbound_flight=trip.outbound_flight.id,
            return_flight=trip.return_flight.id if trip.return_flight else None,
            travel_class=travel_class,
            user=user_id,
            total_amount=total_amount
        )

        return BookingInfo.from_orm(booking)

    def get_booking_by_reference(self, reference: str) -> Optional[BookingInfo]:
        """
        Get booking details by reference number

        Args:
            reference: Booking reference code

        Returns:
            Optional[BookingInfo]: Booking information if found, None otherwise
        """
        try:
            booking = Booking.get(Booking.reference == reference)
            return BookingInfo.from_orm(booking)
        except Booking.DoesNotExist:
            return None

    def get_user_bookings(self, user_id: int) -> List[BookingInfo]:
        """
        Get all bookings for a specific user

        Args:
            user_id: ID of the user

        Returns:
            List[BookingInfo]: List of user's bookings, sorted by creation date
        """
        bookings = (Booking
                    .select()
                    .where(Booking.user == user_id)
                    .order_by(Booking.created_at.desc()))

        return [BookingInfo.from_orm(booking) for booking in bookings]

    def delete_booking(self, booking_id: int, user_id: int) -> bool:
        """
        Delete a booking by ID (only if it belongs to the specified user)

        Args:
            booking_id: ID of the booking to delete
            user_id: ID of the user who owns the booking

        Returns:
            bool: True if booking was deleted, False if not found or not owned by user
        """
        try:
            booking = Booking.get(
                (Booking.id == booking_id) &
                (Booking.user == user_id)
            )
            booking.delete_instance()
            return True
        except Booking.DoesNotExist:
            return False
