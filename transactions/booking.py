from typing import Dict, Any, Optional
from datetime import datetime, date
from services.booking import BookingService
from services.flight import FlightService, Trip
from .transaction import BaseTransaction
from intent_classifier import IntentClassifier


class BookingStates:
    INIT = "INIT"
    ORIGIN = "ORIGIN"
    DESTINATION = "DESTINATION"
    OUTBOUND_DATE = "OUTBOUND_DATE"
    RETURN_DATE = "RETURN_DATE"
    TRAVEL_CLASS = "TRAVEL_CLASS"
    FLIGHT_SELECTION = "FLIGHT_SELECTION"  # New state
    CONFIRMATION = "CONFIRMATION"
    COMPLETE = "COMPLETE"


class BookingTransaction(BaseTransaction):
    VALID_CLASSES = {'FIRST', 'BUSINESS', 'ECONOMY'}
    MAX_FLIGHTS = 5

    def __init__(self, chatbot):
        super().__init__(chatbot)
        # Initialize services
        self.booking_service = BookingService()
        self.flight_service = FlightService()
        self.intent_classifier = IntentClassifier()
        # Initialize state
        self.state = BookingStates.INIT
        self.context = {
            'origin': None,
            'destination': None,
            'outbound_date': None,
            'return_date': None,
            'travel_class': None,
            'trip_type': None,
            'available_trips': [],  # Store available trips
            'selected_trip': None,
            'price': None
        }

    @property
    def requires_auth(self) -> bool:
        return self.state == BookingStates.CONFIRMATION

    def process(self, message: str) -> str:
        auth_response = self.check_and_handle_auth(message)
        if auth_response:
            return auth_response
        return self._process_internal(message)

    def _process_internal(self, message: str) -> str:
        handlers = {
            BookingStates.INIT: self._handle_init,
            BookingStates.ORIGIN: self._handle_origin,
            BookingStates.DESTINATION: self._handle_destination,
            BookingStates.OUTBOUND_DATE: self._handle_outbound_date,
            BookingStates.RETURN_DATE: self._handle_return_date,
            BookingStates.TRAVEL_CLASS: self._handle_travel_class,
            BookingStates.FLIGHT_SELECTION: self._handle_flight_selection,
            BookingStates.CONFIRMATION: self._handle_confirmation
        }
        handler = handlers.get(self.state)
        if handler:
            try:
                return handler(message)
            except Exception as e:
                print(f"Debug - Error in {self.state}: {str(e)}")
                self.state = BookingStates.COMPLETE
                return "Sorry, something went wrong. Please start a new booking."
        return "An error occurred in the booking process."

    def _format_flight_table(self, trips: list[Trip], travel_class: str) -> str:
        """Format available flights into a readable table."""
        if self.context['trip_type'] == 'ONEWAY':
            headers = [
                "Option",
                "Departure",
                "Arrival",
                "Date",
                "Time",
                f"Price ({travel_class})"
            ]

            # Create separator line
            separator = "+-------+------------+------------+------------+--------+-------------+"

            # Create header
            table = [
                separator,
                "| {:5} | {:10} | {:10} | {:10} | {:6} | {:11} |".format(
                    *headers),
                separator
            ]

            # Add rows
            for idx, trip in enumerate(trips, 1):
                flight = trip.outbound_flight
                price = trip.get_all_class_prices()[travel_class]
                row = "| {:5} | {:10} | {:10} | {:10} | {:6} | £{:9} |".format(
                    f"#{idx}",
                    flight.origin_code,
                    flight.destination_code,
                    flight.departure_date.strftime("%Y-%m-%d"),
                    flight.departure_time.strftime("%H:%M"),
                    price
                )
                table.append(row)
                table.append(separator)

        else:  # ROUNDTRIP
            headers = [
                "Option",
                "Outbound",
                "Return",
                "Out Date",
                "Ret Date",
                f"Price ({travel_class})"
            ]

            # Create separator line
            separator = "+-------+------------+------------+------------+------------+-------------+"

            # Create header
            table = [
                separator,
                "| {:5} | {:10} | {:10} | {:10} | {:10} | {:11} |".format(
                    *headers),
                separator
            ]

            # Add rows
            for idx, trip in enumerate(trips, 1):
                outbound = trip.outbound_flight
                return_flight = trip.return_flight
                price = trip.get_all_class_prices()[travel_class]
                row = "| {:5} | {:10} | {:10} | {:10} | {:10} | £{:9} |".format(
                    f"#{idx}",
                    f"{outbound.origin_code}-{outbound.destination_code}",
                    f"{return_flight.origin_code}-{return_flight.destination_code}",
                    outbound.departure_date.strftime("%Y-%m-%d"),
                    return_flight.departure_date.strftime("%Y-%m-%d"),
                    price
                )
                table.append(row)
                table.append(separator)

        return "\n".join(table)

    def _handle_travel_class(self, message: str) -> str:
        travel_class = message.upper()

        if travel_class not in self.VALID_CLASSES:
            return "Invalid travel class. Please select ECONOMY, BUSINESS, or FIRST:"

        try:
            trips = self.flight_service.search_flights(
                origin=self.context['origin'],
                destination=self.context['destination'],
                outbound_date=self.context['outbound_date'],
                return_date=self.context['return_date'],
                limit=self.MAX_FLIGHTS
            )

            if not trips:
                self.state = BookingStates.COMPLETE
                return "Sorry, no flights found for your criteria. Please start a new booking."

            # Store travel class and available trips in context
            self.context['travel_class'] = travel_class
            self.context['available_trips'] = trips

            # Create table of available flights
            table = self._format_flight_table(trips, travel_class)

            self.state = BookingStates.FLIGHT_SELECTION
            return f"Here are the available flights:\n\n{table}\n\nPlease select a flight by entering its number (1-{len(trips)}):"

        except Exception as e:
            print(f"Debug - Flight search error: {str(e)}")
            self.state = BookingStates.COMPLETE
            return "Sorry, we encountered an error while searching flights. Please start a new booking."

    def _handle_flight_selection(self, message: str) -> str:
        try:
            selection = int(message)
            if 1 <= selection <= len(self.context['available_trips']):
                selected_trip = self.context['available_trips'][selection - 1]
                prices = selected_trip.get_all_class_prices()
                price = prices.get(self.context['travel_class'])

                self.context.update({
                    'selected_trip': selected_trip,
                    'price': price
                })

                self.state = BookingStates.CONFIRMATION
                return self._get_booking_summary()
            else:
                return f"Invalid selection. Please choose a number between 1 and {len(self.context['available_trips'])}:"
        except ValueError:
            return "Please enter a valid number for your flight selection:"

    def _handle_confirmation(self, message: str) -> str:
        intent = self.intent_classifier.predict(message)

        if intent == "confirmation":
            try:
                booking = self.booking_service.create_booking(
                    trip=self.context['selected_trip'],
                    user_id=self.auth_service.current_user.id,
                    travel_class=self.context['travel_class']
                )
                self.state = BookingStates.COMPLETE
                return f"Great! Your booking is confirmed. Your reference number is: {booking.reference}"

            except Exception as e:
                print(f"Debug - Booking creation error: {str(e)}")
                self.state = BookingStates.COMPLETE
                return "I apologize, but I couldn't complete your booking. Please try again."

        elif intent == "cancellation":
            self.state = BookingStates.COMPLETE
            return "I've cancelled your booking request. Feel free to start a new booking when you're ready."

        else:
            return "I'm not sure if you want to confirm or cancel the booking. Please let me know clearly - would you like to proceed with this booking?"

    def _get_booking_summary(self) -> str:
        trip = self.context['selected_trip']
        price = self.context['price']

        summary = [
            "Here's a summary of your booking:",
            f"From: {self.context['origin']}",
            f"To: {self.context['destination']}",
            f"Date: {self.context['outbound_date']}"
        ]

        if self.context['return_date']:
            summary.append(f"Return: {self.context['return_date']}")

        summary.extend([
            f"Class: {self.context['travel_class']}",
            f"Total Price: £{price}",
            "",
            "Would you like to proceed with this booking?"
        ])

        return "\n".join(summary)

    # Rest of the methods remain the same as in the previous version
    def _handle_init(self, message: str) -> str:
        self.context['trip_type'] = 'ROUNDTRIP' if "round" in message.lower(
        ) else 'ONEWAY'
        self.state = BookingStates.ORIGIN
        return "Please enter your departure city:"

    def _handle_origin(self, message: str) -> str:
        self.context['origin'] = message
        self.state = BookingStates.DESTINATION
        return "Please enter your destination city:"

    def _handle_destination(self, message: str) -> str:
        self.context['destination'] = message
        self.state = BookingStates.OUTBOUND_DATE
        return "Please enter your outbound date (YYYY-MM-DD):"

    def _handle_outbound_date(self, message: str) -> str:
        try:
            outbound_date = datetime.strptime(message, "%Y-%m-%d").date()
            if outbound_date < date.today():
                return "Date cannot be in the past. Please enter a future date (YYYY-MM-DD):"

            self.context['outbound_date'] = outbound_date

            if self.context['trip_type'] == 'ROUNDTRIP':
                self.state = BookingStates.RETURN_DATE
                return "Please enter your return date (YYYY-MM-DD):"
            else:
                self.state = BookingStates.TRAVEL_CLASS
                return "Please select your travel class (ECONOMY/BUSINESS/FIRST):"

        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD format:"

    def _handle_return_date(self, message: str) -> str:
        try:
            return_date = datetime.strptime(message, "%Y-%m-%d").date()
            if return_date < self.context['outbound_date']:
                return "Return date must be after outbound date. Please enter a valid date (YYYY-MM-DD):"

            self.context['return_date'] = return_date
            self.state = BookingStates.TRAVEL_CLASS
            return "Please select your travel class (ECONOMY/BUSINESS/FIRST):"

        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD format:"

    @property
    def is_complete(self) -> bool:
        return self.state == BookingStates.COMPLETE
