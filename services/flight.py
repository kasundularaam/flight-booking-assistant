# services/flight.py
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict
from decimal import Decimal
from utils.database import Flight
from peewee import fn, SQL


class Rates:
    """Simple class to hold rate configurations"""
    TRIP_TYPE_RATES = {
        'ONEWAY': 1.0,    # Base rate
        'ROUNDTRIP': 0.9  # 10% discount on total
    }

    CLASS_RATES = {
        'FIRST': 2.5,     # 2.5x of base price
        'BUSINESS': 1.8,  # 1.8x of base price
        'ECONOMY': 1.0    # Base price
    }


@dataclass(frozen=True)
class FlightInfo:
    """Data class to represent flight information without exposing ORM details"""
    id: int
    origin_base: str
    origin_location: str
    origin_code: str
    departure_date: date
    departure_time: datetime.time
    destination_base: str
    destination_location: str
    destination_code: str
    status: str
    base_price: Decimal

    @classmethod
    def from_orm(cls, flight: Flight) -> 'FlightInfo':
        """Convert Flight ORM object to FlightInfo"""
        return cls(
            id=flight.id,
            origin_base=flight.origin_base,
            origin_location=flight.origin_location,
            origin_code=flight.origin_code,
            departure_date=flight.departure_date,
            departure_time=flight.departure_time,
            destination_base=flight.destination_base,
            destination_location=flight.destination_location,
            destination_code=flight.destination_code,
            status=flight.status,
            base_price=Decimal(str(flight.base_price))
        )


@dataclass
class Trip:
    """Data class to represent a complete trip (outbound and optional return flight)"""
    trip_type: str
    outbound_flight: FlightInfo
    return_flight: Optional[FlightInfo] = None

    def _calculate_base_trip_price(self) -> Decimal:
        """Calculate the base price considering trip type"""
        total_base = self.outbound_flight.base_price
        if self.trip_type == 'ROUNDTRIP' and self.return_flight:
            total_base += self.return_flight.base_price

        return total_base * Decimal(str(Rates.TRIP_TYPE_RATES[self.trip_type]))

    def get_first_class_price(self) -> Decimal:
        """Calculate price for First Class"""
        base_price = self._calculate_base_trip_price()
        return round(base_price * Decimal(str(Rates.CLASS_RATES['FIRST'])), 2)

    def get_business_class_price(self) -> Decimal:
        """Calculate price for Business Class"""
        base_price = self._calculate_base_trip_price()
        return round(base_price * Decimal(str(Rates.CLASS_RATES['BUSINESS'])), 2)

    def get_economy_class_price(self) -> Decimal:
        """Calculate price for Economy Class"""
        base_price = self._calculate_base_trip_price()
        return round(base_price * Decimal(str(Rates.CLASS_RATES['ECONOMY'])), 2)

    def get_all_class_prices(self) -> Dict[str, Decimal]:
        """Get prices for all classes at once"""
        return {
            'FIRST': self.get_first_class_price(),
            'BUSINESS': self.get_business_class_price(),
            'ECONOMY': self.get_economy_class_price()
        }


class FlightService:
    """Service class for managing flight searches and related operations"""

    DEFAULT_NEARBY_DAYS = 2
    DEFAULT_SEARCH_LIMIT = 5

    def _get_nearby_dates(self, target_date: date, num_days: int = DEFAULT_NEARBY_DAYS) -> List[date]:
        """Get list of dates around the specified date"""
        return [
            target_date + timedelta(days=i)
            for i in range(-num_days, num_days + 1)
        ]

    def _build_location_condition(self, field_prefix: str, location: str) -> SQL:
        """Build SQL condition for location search"""
        location = location.lower().strip()
        return (
            (fn.LOWER(getattr(Flight, f"{field_prefix}_location")) == location) |
            (fn.LOWER(getattr(Flight, f"{field_prefix}_code")) == location) |
            (fn.LOWER(getattr(Flight, f"{field_prefix}_base")) == location)
        )

    def search_flights(
        self,
        origin: str,
        destination: str,
        outbound_date: date,
        return_date: Optional[date] = None,
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> List[Trip]:
        """Search for flights based on criteria"""
        trips = []
        nearby_outbound_dates = self._get_nearby_dates(outbound_date)

        # Build location conditions
        origin_condition = self._build_location_condition('origin', origin)
        destination_condition = self._build_location_condition(
            'destination', destination)

        # Get outbound flights
        outbound_flights = (Flight
                            .select()
                            .where(
                                origin_condition &
                                destination_condition &
                                (Flight.departure_date.in_(nearby_outbound_dates))
                            )
                            .order_by(
                                fn.ABS(fn.JULIANDAY(Flight.departure_date) -
                                       fn.JULIANDAY(outbound_date.strftime('%Y-%m-%d'))),
                                Flight.departure_time
                            )
                            .limit(limit))

        # Handle one-way trips
        if return_date is None:
            return [
                Trip(
                    trip_type='ONEWAY',
                    outbound_flight=FlightInfo.from_orm(outbound)
                )
                for outbound in outbound_flights
            ]

        # Handle round trips
        nearby_return_dates = self._get_nearby_dates(return_date)
        return_origin_condition = self._build_location_condition(
            'origin', destination)
        return_destination_condition = self._build_location_condition(
            'destination', origin)

        for outbound in outbound_flights:
            return_flights = (Flight
                              .select()
                              .where(
                                  return_origin_condition &
                                  return_destination_condition &
                                  (Flight.departure_date.in_(nearby_return_dates)) &
                                  (Flight.departure_date > outbound.departure_date)
                              )
                              .order_by(
                                  fn.ABS(fn.JULIANDAY(Flight.departure_date) -
                                         fn.JULIANDAY(return_date.strftime('%Y-%m-%d'))),
                                  Flight.departure_time
                              )
                              .limit(1))

            for return_flight in return_flights:
                trips.append(Trip(
                    trip_type='ROUNDTRIP',
                    outbound_flight=FlightInfo.from_orm(outbound),
                    return_flight=FlightInfo.from_orm(return_flight)
                ))

        return sorted(
            trips,
            key=lambda x: abs(
                (x.outbound_flight.departure_date - outbound_date).days)
        )[:limit]
