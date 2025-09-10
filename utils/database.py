from peewee import *
import csv
from datetime import datetime

# Connect to SQLite database
db = SqliteDatabase('db/airline.db')

# Base Model


class BaseModel(Model):
    class Meta:
        database = db

# Models


class User(BaseModel):
    id = AutoField()
    name = CharField()
    email = CharField(unique=True)
    password = CharField()
    preferred_class = CharField(null=True)  # Changed to allow NULL


class Flight(BaseModel):
    id = IntegerField(primary_key=True)
    origin_base = CharField()
    origin_location = CharField()
    origin_code = CharField()
    departure_date = DateField()
    departure_time = TimeField()
    destination_base = CharField()
    destination_location = CharField()
    destination_code = CharField()
    status = CharField()
    # Added base_price field
    base_price = DecimalField(decimal_places=2, auto_round=True)


class Booking(BaseModel):
    id = AutoField()
    reference = CharField(unique=True)
    trip_type = CharField()  # ONEWAY or ROUNDTRIP
    outbound_flight = ForeignKeyField(Flight, backref='outbound_bookings')
    return_flight = ForeignKeyField(
        Flight, backref='return_bookings', null=True)  # null for ONEWAY trips
    travel_class = CharField()  # To store the selected class
    created_at = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, backref='bookings')
    # Added total amount field
    total_amount = DecimalField(decimal_places=2, auto_round=True)


def initialize_db():
    db.connect()
    # Drop existing tables if force_reload
    db.create_tables([User, Flight, Booking], safe=True)
    print("Database initialized!")


def load_flights_from_csv(force_reload=False):
    # Check if flights already exist
    if Flight.select().count() > 0 and not force_reload:
        print("Flights data already exists. Use force_reload=True to reload data.")
        return

    if force_reload:
        Flight.delete().execute()

    with open('data/flights.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            departure_date = datetime.strptime(
                row['departure_date'], '%d/%m/%Y').date()
            departure_time = datetime.strptime(
                row['departure_time'], '%H:%M').time()

            Flight.create(
                id=row['id'],
                origin_base=row['origin_base'],
                origin_location=row['origin_location'],
                origin_code=row['origin_code'],
                departure_date=departure_date,
                departure_time=departure_time,
                destination_base=row['destination_base'],
                destination_location=row['destination_location'],
                destination_code=row['destination_code'],
                status=row['status'],
                base_price=float(row['base_price'])  # Added base_price
            )

    print("Flights loaded successfully!")
