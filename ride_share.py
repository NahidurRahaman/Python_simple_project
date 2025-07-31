# User class (base class)
class User:
    def __init__(self, name, phone):
        self.name = name
        self.phone = phone

    def __str__(self):
        return f"{self.name} ({self.phone})"


# Rider class
class Rider(User):
    def __init__(self, name, phone, location):
        super().__init__(name, phone)
        self.location = location

    def request_ride(self, destination, system):
        print(f"{self.name} is requesting a ride to {destination}")
        return system.book_ride(self, destination)


# Driver class
class Driver(User):
    def __init__(self, name, phone, location, car_model):
        super().__init__(name, phone)
        self.location = location
        self.car_model = car_model
        self.available = True

    def __str__(self):
        return f"Driver: {self.name} ({self.car_model}) - {'Available' if self.available else 'Busy'}"


# Ride class
class Ride:
    def __init__(self, rider, driver, destination):
        self.rider = rider
        self.driver = driver
        self.destination = destination
        self.status = "Pending"

    def start_ride(self):
        self.status = "Ongoing"
        self.driver.available = False
        print(f"Ride started with {self.driver.name} for {self.rider.name}")

    def end_ride(self):
        self.status = "Completed"
        self.driver.available = True
        print(f"Ride ended. {self.rider.name} reached {self.destination} safely")


# RideShareSystem class
class RideShareSystem:
    def __init__(self):
        self.drivers = []
        self.rides = []

    def register_driver(self, driver):
        self.drivers.append(driver)
        print(f"Registered driver: {driver}")

    def find_available_driver(self):
        for driver in self.drivers:
            if driver.available:
                return driver
        return None

    def book_ride(self, rider, destination):
        driver = self.find_available_driver()
        if driver:
            ride = Ride(rider, driver, destination)
            ride.start_ride()
            self.rides.append(ride)
            return ride
        else:
            print("No drivers available at the moment.")
            return None

# System
system = RideShareSystem()

# Register Drivers
driver1 = Driver("Alice", "01727527261", "Uttara", "Toyota Prius")
driver2 = Driver("Bob", "01876057476", "Banani", "Honda Civic")
system.register_driver(driver1)
system.register_driver(driver2)

# Rider
rider = Rider("Nahidur", "01578562877", "Mirpur")

# Rider requests a ride
ride1 = rider.request_ride("Gulshan", system)

# Complete the ride
if ride1:
    ride1.end_ride()
