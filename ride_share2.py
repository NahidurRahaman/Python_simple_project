from abc import ABC, abstractmethod
from datetime import datetime
import math

# ------------------- Ride Sharing System ------------------- #
class Ride_Sharing:
    def __init__(self, company_name):
        self.company_name = company_name
        self.drivers = []
        self.riders = []
        self.rides = []

    def add_rider(self, rider):
        self.riders.append(rider)

    def add_driver(self, driver):
        self.drivers.append(driver)

# ------------------- Abstract User ------------------- #
class User(ABC):
    id_counter = 1

    def __init__(self, name, email, nid):
        self.name = name
        self.email = email
        self._id = User.id_counter
        User.id_counter += 1
        self.__nid = nid
        self.wallet = 0

    @abstractmethod
    def display_profile(self):
        raise NotImplementedError

# ------------------- Rider ------------------- #
class Rider(User):
    def __init__(self, name, email, nid, current_location, initial_amount):
        super().__init__(name, email, nid)
        self.current_location = current_location
        self.wallet = initial_amount
        self.current_ride = None

    def display_profile(self):
        print(f"Rider: {self.name}, Email: {self.email}, Wallet: {self.wallet}")

    def load_cash(self, amount):
        if amount > 0:
            self.wallet += amount

    def request_ride(self, destination, ride_matching):
        if not self.current_ride:
            ride_request = RideRequest(self, destination)
            self.current_ride = ride_matching.find_driver(ride_request)

# ------------------- Driver ------------------- #
class Driver(User):
    def __init__(self, name, email, nid, current_location, vehicle):
        super().__init__(name, email, nid)
        self.current_location = current_location
        self.vehicle = vehicle
        self.rating = []
        self.current_ride = None

    def display_profile(self):
        avg_rating = sum(self.rating) / len(self.rating) if self.rating else "N/A"
        print(f"Driver: {self.name}, Email: {self.email}, Rating: {avg_rating}, Vehicle: {self.vehicle.vehicle_type}")

    def accept_ride(self, ride):
        self.current_ride = ride
        ride.set_driver(self)

    def update_location(self, location):
        self.current_location = location

    def add_rating(self, rate):
        self.rating.append(rate)

# ------------------- Ride Class ------------------- #
class Ride:
    def __init__(self, start_location, end_location, rider, vehicle):
        self.start_location = start_location
        self.end_location = end_location
        self.driver = None
        self.rider = rider
        self.vehicle = vehicle
        self.start_time = None
        self.end_time = None
        self.estimated_fare = self.calculate_fare()

    def set_driver(self, driver):
        self.driver = driver

    def calculate_fare(self):
        distance = math.dist(self.start_location, self.end_location)
        return round(distance * self.vehicle.rate, 2)

    def start_ride(self):
        self.start_time = datetime.now()

    def end_ride(self, rating):
        self.end_time = datetime.now()
        fare = self.estimated_fare
        if self.rider.wallet >= fare:
            self.rider.wallet -= fare
            self.driver.wallet += fare
            self.driver.add_rating(rating)
            print(f"Ride ended. Fare: {fare}")
        else:
            print("Not enough balance!")

# ------------------- Ride Request ------------------- #
class RideRequest:
    def __init__(self, rider, destination):
        self.rider = rider
        self.destination = destination

# ------------------- Ride Matching ------------------- #
class RideMatching:
    def __init__(self, drivers):
        self.available_drivers = drivers

    def find_driver(self, ride_request):
        rider_location = ride_request.rider.current_location
        closest_driver = None
        min_distance = float('inf')

        for driver in self.available_drivers:
            if driver.vehicle.status == 'available':
                dist = math.dist(driver.current_location, rider_location)
                if dist < min_distance:
                    min_distance = dist
                    closest_driver = driver

        if closest_driver:
            ride = Ride(rider_location, ride_request.destination, ride_request.rider, closest_driver.vehicle)
            closest_driver.accept_ride(ride)
            print(f"Ride matched with driver: {closest_driver.name}, Fare: {ride.estimated_fare}")
            return ride
        else:
            print("No available driver found.")
            return None

# ------------------- Vehicle Types ------------------- #
class Vehicle(ABC):
    def __init__(self, vehicle_type, license_plate, rate):
        self.vehicle_type = vehicle_type
        self.license_plate = license_plate
        self.rate = rate
        self.status = 'available'

    @abstractmethod
    def start_drive(self):
        pass

class Car(Vehicle):
    def __init__(self, license_plate):
        super().__init__('car', license_plate, 15)

    def start_drive(self):
        self.status = 'unavailable'

class Bike(Vehicle):
    def __init__(self, license_plate):
        super().__init__('bike', license_plate, 8)

    def start_drive(self):
        self.status = 'unavailable'

class CNG(Vehicle):
    def __init__(self, license_plate):
        super().__init__('cng', license_plate, 5)

    def start_drive(self):
        self.status = 'unavailable'

# ------------------- Test Run ------------------- #
if __name__ == "__main__":
    company = Ride_Sharing("UrbanGo")

    # Add Riders
    rider1 = Rider("Alice", "alice@email.com", "1234", (10, 10), 500)
    company.add_rider(rider1)

    # Add Drivers
    car = Car("CAR-123")
    driver1 = Driver("Bob", "bob@email.com", "5678", (11, 10), car)
    company.add_driver(driver1)

    bike = Bike("BIKE-456")
    driver2 = Driver("John", "john@email.com", "8910", (20, 30), bike)
    company.add_driver(driver2)

    # Ride Matching System
    ride_match = RideMatching(company.drivers)

    # Rider requests ride
    rider1.request_ride((15, 12), ride_match)

    # Start and end ride
    ride = rider1.current_ride
    if ride:
        ride.start_ride()
        ride.end_ride(rating=5)

    # Check balances and profiles
    rider1.display_profile()
    driver1.display_profile()
