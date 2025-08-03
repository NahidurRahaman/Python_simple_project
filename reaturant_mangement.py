from abc import ABC, abstractmethod
import random

class User(ABC):
    def __init__(self, name, email):
        self.name = name
        self.email = email

    @abstractmethod
    def display_role(self):
        pass

class Customer(User):
    def __init__(self, name, email):
        super().__init__(name, email)
        self.rewards = 0

    def display_role(self):
        print(f"Customer: {self.name}")

class Employee(User):
    def __init__(self, name, email):
        super().__init__(name, email)
        self.salary = 0

    def display_role(self):
        print(f"Employee: {self.name}")

class Chef(Employee):
    def cook(self, item):
        print(f"Chef {self.name} is cooking {item.name}...")

    def display_role(self):
        print(f"Chef: {self.name}")

class Server(Employee):
    def serve(self, order):
        print(f"Server {self.name} is serving table {order.table_number}.")

    def display_role(self):
        print(f"Server: {self.name}")

class Manager(Employee):
    def manage(self):
        print(f"Manager {self.name} is managing staff and orders.")

    def display_role(self):
        print(f"Manager: {self.name}")

class Cleaner(Employee):
    def clean(self):
        print(f"Cleaner {self.name} is cleaning the restaurant.")

    def display_role(self):
        print(f"Cleaner: {self.name}")

class Supplier(User):
    def supply(self, item):
        print(f"Supplier {self.name} has supplied {item}.")

    def display_role(self):
        print(f"Supplier: {self.name}")

class Marketer(User):
    def promote(self):
        print(f"Marketer {self.name} is running ads on social media.")

    def display_role(self):
        print(f"Marketer: {self.name}")

class FoodItem(ABC):
    def __init__(self, name, price):
        self.name = name
        self.price = price

    @abstractmethod
    def category(self):
        pass

class Burger(FoodItem):
    def category(self):
        return "Burger"

class Pizza(FoodItem):
    def category(self):
        return "Pizza"

class Drink(FoodItem):
    def category(self):
        return "Drink"

class Juice(FoodItem):
    def category(self):
        return "Juice"

class Salad(FoodItem):
    def category(self):
        return "Salad"

# Order class
class Order:
    def __init__(self, customer, table_number):
        self.customer = customer
        self.table_number = table_number
        self.items = []
        self.discount = 0
        self.status = "Pending"
        self.rating = None

    def add_item(self, item):
        self.items.append(item)

    def apply_discount(self, percent):
        self.discount = percent

    def total_price(self):
        total = sum(item.price for item in self.items)
        return total - (total * self.discount / 100)

    def complete_order(self):
        self.status = "Completed"

    def give_rating(self, value):
        if 1 <= value <= 5:
            self.rating = value
            print(f"Thank you! You rated us: {value}/5")

    def show_order(self):
        print(f"\nOrder for: {self.customer.name} (Table {self.table_number})")
        for item in self.items:
            print(f"  - {item.name} ({item.category()}): ${item.price}")
        print(f"Discount: {self.discount}%")
        print(f"Total after discount: ${self.total_price():.2f}")
        print(f"Status: {self.status}")
        if self.rating:
            print(f"Rating: {self.rating}/5")


class Restaurant:
    def __init__(self, name):
        self.name = name
        self.menu = []
        self.staff = []
        self.customers = []
        self.orders = []

    def add_menu_item(self, item):
        self.menu.append(item)

    def add_staff(self, employee):
        self.staff.append(employee)

    def add_customer(self, customer):
        self.customers.append(customer)

    def show_menu(self):
        print(f"\n\ Menu of {self.name}")
        for i, item in enumerate(self.menu, start=1):
            print(f"{i}. {item.name} ({item.category()}) - ${item.price}")

    def get_item_by_index(self, index):
        if 0 <= index < len(self.menu):
            return self.menu[index]
        return None

    def print_bill(self, order):
        print("\n========= BILL =========")
        order.show_order()
        print("========================")

    def process_order(self, order):
        chef = next((s for s in self.staff if isinstance(s, Chef)), None)
        server = next((s for s in self.staff if isinstance(s, Server)), None)
        cleaner = next((s for s in self.staff if isinstance(s, Cleaner)), None)

        if chef:
            for item in order.items:
                chef.cook(item)
        if server:
            server.serve(order)
        if cleaner:
            cleaner.clean()

        order.complete_order()
        self.orders.append(order)
        self.print_bill(order)


if __name__ == "__main__":
    resto = Restaurant("Full Feature Restaurant")

    # Add menu items
    resto.add_menu_item(Burger("Cheese Burger", 150))
    resto.add_menu_item(Pizza("Margherita Pizza", 300))
    resto.add_menu_item(Drink("Coca-Cola", 50))
    resto.add_menu_item(Juice("Orange Juice", 70))
    resto.add_menu_item(Salad("Greek Salad", 120))

    # Add staff
    resto.add_staff(Chef("Gordon Ramsay", "chef@resto.com"))
    resto.add_staff(Server("Alice", "server@resto.com"))
    resto.add_staff(Manager("Nila", "manager@resto.com"))
    resto.add_staff(Cleaner("Bob", "cleaner@resto.com"))

    # Add suppliers and marketers
    supplier = Supplier("Tarek", "supplier@resto.com")
    marketer = Marketer("Sumaiya", "marketing@resto.com")
    supplier.supply("Vegetables")
    marketer.promote()

    # Add customers and take orders
    c1 = Customer("Rahim", "rahim@gmail.com")
    c2 = Customer("Karim", "karim@gmail.com")
    resto.add_customer(c1)
    resto.add_customer(c2)

    resto.show_menu()

    order1 = Order(c1, table_number=1)
    order1.add_item(resto.get_item_by_index(0))
    order1.add_item(resto.get_item_by_index(2))
    order1.apply_discount(10)
    resto.process_order(order1)
    order1.give_rating(5)

    order2 = Order(c2, table_number=2)
    order2.add_item(resto.get_item_by_index(1))
    order2.add_item(resto.get_item_by_index(4))
    order2.add_item(resto.get_item_by_index(3))
    order2.apply_discount(5)
    resto.process_order(order2)
    order2.give_rating(4)

    print("\nThank you for visiting!")
