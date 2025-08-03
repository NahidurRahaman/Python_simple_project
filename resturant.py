import json
from enum import Enum
from datetime import datetime

class UserType(Enum):
    CUSTOMER = "Customer"
    CHEF = "Chef"
    SERVER = "Server"
    MANAGER = "Manager"
    CLEANER = "Cleaner"
    SUPPLIER = "Supplier"
    MARKETER = "Marketer"

class FoodCategory(Enum):
    BURGER = "Burger"
    PIZZA = "Pizza"
    JUICE = "Juice"
    SALAD = "Salad"
    DRINK = "Drink"

class OrderStatus(Enum):
    PENDING = "Pending"
    COOKING = "Cooking"
    READY = "Ready to Serve"
    SERVED = "Served"
    COMPLETED = "Completed"

class User:
    def __init__(self, name, email, password, user_type):
        self.name = name
        self.email = email
        self.password = password  # In real system, use hashed passwords
        self.user_type = user_type
    
    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'user_type': self.user_type.value
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data['name'],
            data['email'],
            data['password'],
            UserType(data['user_type'])
        )

class FoodItem:
    def __init__(self, name, category, price, stock):
        self.name = name
        self.category = FoodCategory(category)
        self.price = price
        self.stock = stock
    
    def to_dict(self):
        return {
            'name': self.name,
            'category': self.category.value,
            'price': self.price,
            'stock': self.stock
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data['name'],
            data['category'],
            data['price'],
            data['stock']
        )
    
    def reduce_stock(self, quantity=1):
        if self.stock >= quantity:
            self.stock -= quantity
            return True
        return False
    
    def is_available(self):
        return self.stock > 0

class OrderItem:
    def __init__(self, food_item, quantity):
        self.food_item = food_item
        self.quantity = quantity
    
    @property
    def total_price(self):
        return self.food_item.price * self.quantity

class Order:
    def __init__(self, customer_email, table_number):
        self.order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.customer_email = customer_email
        self.table_number = table_number
        self.items = []
        self.status = OrderStatus.PENDING
        self.discount_coupon = None
        self.discount_amount = 0
        self.rating = None
        self.chef = None
        self.server = None
        self.cleaner = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self, restaurant):
        return {
            'order_id': self.order_id,
            'customer_email': self.customer_email,
            'table_number': self.table_number,
            'items': [{
                'food_name': item.food_item.name,
                'quantity': item.quantity
            } for item in self.items],
            'status': self.status.value,
            'discount_coupon': self.discount_coupon,
            'discount_amount': self.discount_amount,
            'rating': self.rating,
            'chef': self.chef,
            'server': self.server,
            'cleaner': self.cleaner,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data, restaurant):
        order = cls(data['customer_email'], data['table_number'])
        order.order_id = data['order_id']
        order.items = [OrderItem(
            restaurant.find_food_item(item['food_name']),
            item['quantity']
        ) for item in data['items'] if restaurant.find_food_item(item['food_name'])]
        order.status = OrderStatus(data['status'])
        order.discount_coupon = data['discount_coupon']
        order.discount_amount = data['discount_amount']
        order.rating = data['rating']
        order.chef = data['chef']
        order.server = data['server']
        order.cleaner = data['cleaner']
        order.created_at = datetime.fromisoformat(data['created_at'])
        order.updated_at = datetime.fromisoformat(data['updated_at'])
        return order
    
    def add_item(self, food_item, quantity):
        if food_item.is_available() and food_item.reduce_stock(quantity):
            self.items.append(OrderItem(food_item, quantity))
            return True
        return False
    
    def apply_discount(self, coupon_code, discount_amount):
        self.discount_coupon = coupon_code
        self.discount_amount = discount_amount
    
    def calculate_total(self):
        subtotal = sum(item.total_price for item in self.items)
        return max(0, subtotal - self.discount_amount)
    
    def set_rating(self, rating):
        if 1 <= rating <= 5:
            self.rating = rating
            return True
        return False
    
    def update_status(self, new_status):
        self.status = new_status
        self.updated_at = datetime.now()

class Restaurant:
    def __init__(self, name):
        self.name = name
        self.users = {}  # email: User
        self.menu = {}  # food_name: FoodItem
        self.orders = {}  # order_id: Order
        self.current_user = None
        self.coupons = {"WELCOME10": 10, "HAPPY20": 20}  # coupon_code: discount_amount
        self.load_data()
    
    def save_data(self):
        data = {
            'name': self.name,
            'users': {email: user.to_dict() for email, user in self.users.items()},
            'menu': {food.name: food.to_dict() for food in self.menu.values()},
            'orders': {order_id: order.to_dict(self) for order_id, order in self.orders.items()},
            'coupons': self.coupons
        }
        with open('restaurant_data.json', 'w') as f:
            json.dump(data, f)
    
    def load_data(self):
        try:
            with open('restaurant_data.json', 'r') as f:
                data = json.load(f)
                self.name = data['name']
                self.users = {email: User.from_dict(user_data) for email, user_data in data['users'].items()}
                self.menu = {food_data['name']: FoodItem.from_dict(food_data) for food_data in data['menu'].values()}
                self.orders = {order_id: Order.from_dict(order_data, self) for order_id, order_data in data['orders'].items()}
                self.coupons = data['coupons']
        except FileNotFoundError:
            # Create default admin if no data exists
            manager = User("Admin Manager", "manager@restaurant.com", "manager123", UserType.MANAGER)
            self.users[manager.email] = manager
            self.save_data()
    
    def create_account(self, name, email, password, user_type):
        if email in self.users:
            return False, "Email already registered"
        self.users[email] = User(name, email, password, user_type)
        self.save_data()
        return True, "Account created successfully"
    
    def login(self, email, password):
        if email not in self.users:
            return False, "User not found"
        user = self.users[email]
        if user.password != password:
            return False, "Incorrect password"
        self.current_user = user
        return True, f"Welcome {user.name}!"
    
    def logout(self):
        self.current_user = None
        return True, "Logged out successfully"
    
    def add_food_item(self, name, category, price, stock):
        if not self.current_user or self.current_user.user_type not in [UserType.MANAGER]:
            return False, "Manager access required"
        if name in self.menu:
            return False, "Food item already exists"
        try:
            food_category = FoodCategory(category)
            self.menu[name] = FoodItem(name, food_category, price, stock)
            self.save_data()
            return True, "Food item added successfully"
        except ValueError:
            return False, "Invalid food category"
    
    def find_food_item(self, name):
        return self.menu.get(name)
    
    def get_available_menu(self):
        return [food for food in self.menu.values() if food.is_available()]
    
    def place_order(self, table_number, items, coupon_code=None):
        if not self.current_user or self.current_user.user_type != UserType.CUSTOMER:
            return False, "Customer login required"
        
        order = Order(self.current_user.email, table_number)
        
        for item_name, quantity in items:
            food_item = self.find_food_item(item_name)
            if not food_item or not food_item.is_available():
                return False, f"{item_name} is not available"
            if not order.add_item(food_item, quantity):
                return False, f"Failed to add {item_name}"
        
        if coupon_code and coupon_code in self.coupons:
            order.apply_discount(coupon_code, self.coupons[coupon_code])
        
        self.orders[order.order_id] = order
        self.save_data()
        return True, f"Order placed successfully! Order ID: {order.order_id}"
    
    def process_order(self, order_id, action):
        if not self.current_user:
            return False, "Login required"
        
        if order_id not in self.orders:
            return False, "Order not found"
        
        order = self.orders[order_id]
        
        if action == "cook" and self.current_user.user_type == UserType.CHEF:
            order.update_status(OrderStatus.COOKING)
            order.chef = self.current_user.email
            self.save_data()
            return True, f"Order {order_id} is being cooked by {self.current_user.name}"
        
        elif action == "serve" and self.current_user.user_type == UserType.SERVER:
            if order.status != OrderStatus.READY:
                return False, "Order is not ready to serve"
            order.update_status(OrderStatus.SERVED)
            order.server = self.current_user.email
            self.save_data()
            return True, f"Order {order_id} served by {self.current_user.name}"
        
        elif action == "complete" and self.current_user.user_type == UserType.CLEANER:
            if order.status != OrderStatus.SERVED:
                return False, "Order has not been served yet"
            order.update_status(OrderStatus.COMPLETED)
            order.cleaner = self.current_user.email
            self.save_data()
            return True, f"Table {order.table_number} cleaned by {self.current_user.name}"
        
        elif action == "ready" and self.current_user.user_type == UserType.CHEF:
            if order.status != OrderStatus.COOKING:
                return False, "Order is not being cooked"
            order.update_status(OrderStatus.READY)
            self.save_data()
            return True, f"Order {order_id} is ready to serve"
        
        return False, "Invalid action for your role"
    
    def generate_bill(self, order_id):
        if order_id not in self.orders:
            return None, "Order not found"
        
        order = self.orders[order_id]
        bill_details = {
            'order_id': order.order_id,
            'customer': order.customer_email,
            'table_number': order.table_number,
            'items': [{
                'name': item.food_item.name,
                'quantity': item.quantity,
                'price': item.food_item.price,
                'total': item.total_price
            } for item in order.items],
            'subtotal': sum(item.total_price for item in order.items),
            'discount': order.discount_amount,
            'total': order.calculate_total(),
            'status': order.status.value
        }
        return bill_details, None
    
    def add_rating(self, order_id, rating):
        if not self.current_user or self.current_user.user_type != UserType.CUSTOMER:
            return False, "Customer login required"
        
        if order_id not in self.orders:
            return False, "Order not found"
        
        order = self.orders[order_id]
        if order.customer_email != self.current_user.email:
            return False, "You can only rate your own orders"
        
        if order.status != OrderStatus.COMPLETED:
            return False, "Order must be completed before rating"
        
        if order.set_rating(rating):
            self.save_data()
            return True, "Thank you for your rating!"
        return False, "Rating must be between 1 and 5"
    
    def add_supply(self, food_name, quantity):
        if not self.current_user or self.current_user.user_type != UserType.SUPPLIER:
            return False, "Supplier access required"
        
        if food_name not in self.menu:
            return False, "Food item not found"
        
        self.menu[food_name].stock += quantity
        self.save_data()
        return True, f"Added {quantity} {food_name} to stock"
    
    def add_coupon(self, coupon_code, discount_amount):
        if not self.current_user or self.current_user.user_type != UserType.MARKETER:
            return False, "Marketer access required"
        
        if coupon_code in self.coupons:
            return False, "Coupon code already exists"
        
        self.coupons[coupon_code] = discount_amount
        self.save_data()
        return True, "Coupon added successfully"

def main():
    restaurant = Restaurant("Delicious Bites")
    
    while True:
        print("\n=== Restaurant Management System ===")
        print(f"Restaurant: {restaurant.name}")
        
        if restaurant.current_user:
            print(f"\nLogged in as: {restaurant.current_user.name} ({restaurant.current_user.user_type.value})")
            
            if restaurant.current_user.user_type == UserType.CUSTOMER:
                print("1. View Menu")
                print("2. Place Order")
                print("3. View My Orders")
                print("4. Rate Order")
                print("5. View Bill")
                print("6. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    menu = restaurant.get_available_menu()
                    if not menu:
                        print("No items available in the menu")
                    else:
                        print("\nAvailable Menu:")
                        for item in menu:
                            print(f"{item.name} ({item.category.value}) - ${item.price} (Stock: {item.stock})")
                
                elif choice == '2':
                    table_number = input("Enter table number: ")
                    items = []
                    while True:
                        item_name = input("Enter food item name (or 'done' to finish): ")
                        if item_name.lower() == 'done':
                            break
                        if not restaurant.find_food_item(item_name):
                            print("Invalid item name")
                            continue
                        try:
                            quantity = int(input("Enter quantity: "))
                            if quantity <= 0:
                                print("Quantity must be positive")
                                continue
                            items.append((item_name, quantity))
                        except ValueError:
                            print("Please enter a valid number")
                    
                    coupon = input("Enter coupon code (leave blank if none): ")
                    success, message = restaurant.place_order(table_number, items, coupon if coupon else None)
                    print(message)
                
                elif choice == '3':
                    customer_orders = [order for order in restaurant.orders.values() 
                                      if order.customer_email == restaurant.current_user.email]
                    if not customer_orders:
                        print("You have no orders")
                    else:
                        print("\nYour Orders:")
                        for order in customer_orders:
                            print(f"Order ID: {order.order_id} | Table: {order.table_number} | Status: {order.status.value}")
                
                elif choice == '4':
                    order_id = input("Enter order ID to rate: ")
                    try:
                        rating = int(input("Enter rating (1-5): "))
                        success, message = restaurant.add_rating(order_id, rating)
                        print(message)
                    except ValueError:
                        print("Please enter a number between 1 and 5")
                
                elif choice == '5':
                    order_id = input("Enter order ID to view bill: ")
                    bill, error = restaurant.generate_bill(order_id)
                    if error:
                        print(error)
                    else:
                        print("\n=== Bill ===")
                        print(f"Order ID: {bill['order_id']}")
                        print(f"Customer: {bill['customer']}")
                        print(f"Table: {bill['table_number']}")
                        print("\nItems:")
                        for item in bill['items']:
                            print(f"{item['name']} x{item['quantity']} @ ${item['price']} = ${item['total']}")
                        print(f"\nSubtotal: ${bill['subtotal']}")
                        print(f"Discount: ${bill['discount']}")
                        print(f"Total: ${bill['total']}")
                        print(f"Status: {bill['status']}")
                
                elif choice == '6':
                    restaurant.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
            
            elif restaurant.current_user.user_type == UserType.MANAGER:
                print("1. Add Food Item")
                print("2. View Menu")
                print("3. View All Orders")
                print("4. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    name = input("Enter food name: ")
                    print("Available categories:")
                    for category in FoodCategory:
                        print(category.value)
                    category = input("Enter category: ")
                    try:
                        price = float(input("Enter price: "))
                        stock = int(input("Enter initial stock: "))
                        success, message = restaurant.add_food_item(name, category, price, stock)
                        print(message)
                    except ValueError:
                        print("Invalid price or stock value")
                
                elif choice == '2':
                    menu = restaurant.menu.values()
                    if not menu:
                        print("No items in the menu")
                    else:
                        print("\nMenu:")
                        for item in menu:
                            print(f"{item.name} ({item.category.value}) - ${item.price} (Stock: {item.stock})")
                
                elif choice == '3':
                    if not restaurant.orders:
                        print("No orders yet")
                    else:
                        print("\nAll Orders:")
                        for order in restaurant.orders.values():
                            print(f"ID: {order.order_id} | Table: {order.table_number} | Status: {order.status.value}")
                
                elif choice == '4':
                    restaurant.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
            
            elif restaurant.current_user.user_type in [UserType.CHEF, UserType.SERVER, UserType.CLEANER]:
                print("1. View Pending Orders")
                print("2. Process Order")
                print("3. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    status_to_show = {
                        UserType.CHEF: OrderStatus.PENDING,
                        UserType.SERVER: OrderStatus.READY,
                        UserType.CLEANER: OrderStatus.SERVED
                    }.get(restaurant.current_user.user_type)
                    
                    orders_to_show = [order for order in restaurant.orders.values() 
                                     if order.status == status_to_show]
                    
                    if not orders_to_show:
                        print(f"No {status_to_show.value} orders")
                    else:
                        print(f"\n{status_to_show.value} Orders:")
                        for order in orders_to_show:
                            print(f"ID: {order.order_id} | Table: {order.table_number}")
                            for item in order.items:
                                print(f"  - {item.food_item.name} x{item.quantity}")
                
                elif choice == '2':
                    order_id = input("Enter order ID to process: ")
                    action = {
                        UserType.CHEF: "cook",
                        UserType.SERVER: "serve",
                        UserType.CLEANER: "complete"
                    }.get(restaurant.current_user.user_type)
                    
                    success, message = restaurant.process_order(order_id, action)
                    print(message)
                
                elif choice == '3':
                    restaurant.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
            
            elif restaurant.current_user.user_type == UserType.SUPPLIER:
                print("1. View Menu Stock")
                print("2. Add Supply")
                print("3. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    print("\nCurrent Stock:")
                    for item in restaurant.menu.values():
                        print(f"{item.name}: {item.stock}")
                
                elif choice == '2':
                    food_name = input("Enter food name to supply: ")
                    try:
                        quantity = int(input("Enter quantity to add: "))
                        success, message = restaurant.add_supply(food_name, quantity)
                        print(message)
                    except ValueError:
                        print("Please enter a valid number")
                
                elif choice == '3':
                    restaurant.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
            
            elif restaurant.current_user.user_type == UserType.MARKETER:
                print("1. View Coupons")
                print("2. Add Coupon")
                print("3. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    print("\nAvailable Coupons:")
                    for code, discount in restaurant.coupons.items():
                        print(f"{code}: ${discount} discount")
                
                elif choice == '2':
                    code = input("Enter new coupon code: ")
                    try:
                        discount = float(input("Enter discount amount: "))
                        success, message = restaurant.add_coupon(code, discount)
                        print(message)
                    except ValueError:
                        print("Please enter a valid discount amount")
                
                elif choice == '3':
                    restaurant.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
        
        else:
            print("\n1. Login")
            print("2. Create Account")
            print("3. Exit")
            
            choice = input("Enter your choice: ")
            
            if choice == '1':
                email = input("Email: ")
                password = input("Password: ")
                success, message = restaurant.login(email, password)
                print(message)
            
            elif choice == '2':
                name = input("Name: ")
                email = input("Email: ")
                password = input("Password: ")
                print("Available user types:")
                for user_type in UserType:
                    print(user_type.value)
                user_type = input("Enter user type: ")
                try:
                    user_type_enum = UserType(user_type)
                    success, message = restaurant.create_account(name, email, password, user_type_enum)
                    print(message)
                except ValueError:
                    print("Invalid user type")
            
            elif choice == '3':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice")

if __name__ == "__main__":
    main()