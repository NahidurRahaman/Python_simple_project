import json
from enum import Enum
from datetime import datetime

class UserType(Enum):
    CUSTOMER = "Customer"
    SELLER = "Seller"

class ProductCategory(Enum):
    ELECTRONICS = "Electronics"
    CLOTHING = "Clothing"
    BOOKS = "Books"
    HOME = "Home"
    BEAUTY = "Beauty"

class OrderStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"

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

class Product:
    def __init__(self, name, category, price, stock, seller_email, description=""):
        self.name = name
        self.category = ProductCategory(category)
        self.price = price
        self.stock = stock
        self.seller_email = seller_email
        self.description = description
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            'name': self.name,
            'category': self.category.value,
            'price': self.price,
            'stock': self.stock,
            'seller_email': self.seller_email,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        product = cls(
            data['name'],
            data['category'],
            data['price'],
            data['stock'],
            data['seller_email'],
            data.get('description', "")
        )
        product.created_at = datetime.fromisoformat(data['created_at'])
        return product
    
    def reduce_stock(self, quantity=1):
        if self.stock >= quantity:
            self.stock -= quantity
            return True
        return False
    
    def is_available(self):
        return self.stock > 0

class OrderItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity
    
    @property
    def total_price(self):
        return self.product.price * self.quantity

class Order:
    def __init__(self, customer_email):
        self.order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.customer_email = customer_email
        self.items = []
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.shipping_address = ""
        self.payment_method = ""
    
    def to_dict(self, shop):
        return {
            'order_id': self.order_id,
            'customer_email': self.customer_email,
            'items': [{
                'product_name': item.product.name,
                'seller_email': item.product.seller_email,
                'quantity': item.quantity
            } for item in self.items],
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'shipping_address': self.shipping_address,
            'payment_method': self.payment_method
        }
    
    @classmethod
    def from_dict(cls, data, shop):
        order = cls(data['customer_email'])
        order.order_id = data['order_id']
        order.items = [OrderItem(
            shop.find_product(item['product_name'], item['seller_email']),
            item['quantity']
        ) for item in data['items'] if shop.find_product(item['product_name'], item['seller_email'])]
        order.status = OrderStatus(data['status'])
        order.created_at = datetime.fromisoformat(data['created_at'])
        order.updated_at = datetime.fromisoformat(data['updated_at'])
        order.shipping_address = data.get('shipping_address', "")
        order.payment_method = data.get('payment_method', "")
        return order
    
    def add_item(self, product, quantity):
        if product.is_available() and product.reduce_stock(quantity):
            self.items.append(OrderItem(product, quantity))
            return True
        return False
    
    def calculate_total(self):
        return sum(item.total_price for item in self.items)
    
    def update_status(self, new_status):
        self.status = new_status
        self.updated_at = datetime.now()

class EShop:
    def __init__(self, name):
        self.name = name
        self.users = {}  # email: User
        self.products = []  # List of Product objects
        self.orders = {}  # order_id: Order
        self.current_user = None
        self.load_data()
    
    def save_data(self):
        data = {
            'name': self.name,
            'users': {email: user.to_dict() for email, user in self.users.items()},
            'products': [product.to_dict() for product in self.products],
            'orders': {order_id: order.to_dict(self) for order_id, order in self.orders.items()}
        }
        with open('eshop_data.json', 'w') as f:
            json.dump(data, f)
    
    def load_data(self):
        try:
            with open('eshop_data.json', 'r') as f:
                data = json.load(f)
                self.name = data['name']
                self.users = {email: User.from_dict(user_data) for email, user_data in data['users'].items()}
                self.products = [Product.from_dict(product_data) for product_data in data['products']]
                self.orders = {order_id: Order.from_dict(order_data, self) for order_id, order_data in data['orders'].items()}
        except FileNotFoundError:
            # Initialize with no data
            pass
    
    def create_account(self, name, email, password, user_type):
        if email in self.users:
            return False, "Email already registered"
        try:
            user_type_enum = UserType(user_type)
            self.users[email] = User(name, email, password, user_type_enum)
            self.save_data()
            return True, "Account created successfully"
        except ValueError:
            return False, "Invalid user type"
    
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
    
    def add_product(self, name, category, price, stock, description=""):
        if not self.current_user or self.current_user.user_type != UserType.SELLER:
            return False, "Seller access required"
        try:
            product_category = ProductCategory(category)
            self.products.append(Product(
                name, product_category, price, stock, 
                self.current_user.email, description
            ))
            self.save_data()
            return True, "Product added successfully"
        except ValueError:
            return False, "Invalid product category"
    
    def find_product(self, name, seller_email=None):
        for product in self.products:
            if product.name == name:
                if seller_email is None or product.seller_email == seller_email:
                    return product
        return None
    
    def get_available_products(self):
        return [product for product in self.products if product.is_available()]
    
    def get_products_by_seller(self, seller_email):
        return [product for product in self.products 
                if product.seller_email == seller_email and product.is_available()]
    
    def place_order(self, items, shipping_address, payment_method):
        if not self.current_user or self.current_user.user_type != UserType.CUSTOMER:
            return False, "Customer login required"
        
        order = Order(self.current_user.email)
        order.shipping_address = shipping_address
        order.payment_method = payment_method
        
        for product_name, seller_email, quantity in items:
            product = self.find_product(product_name, seller_email)
            if not product or not product.is_available():
                return False, f"{product_name} is not available"
            if not order.add_item(product, quantity):
                return False, f"Failed to add {product_name}"
        
        self.orders[order.order_id] = order
        self.save_data()
        return True, f"Order placed successfully! Order ID: {order.order_id}"
    
    def update_order_status(self, order_id, new_status):
        if not self.current_user:
            return False, "Login required"
        
        if order_id not in self.orders:
            return False, "Order not found"
        
        order = self.orders[order_id]
        
        # Only seller who has products in this order can update status
        if self.current_user.user_type == UserType.SELLER:
            seller_products_in_order = any(
                item.product.seller_email == self.current_user.email 
                for item in order.items
            )
            if not seller_products_in_order:
                return False, "You don't have products in this order"
        
        try:
            status_enum = OrderStatus(new_status)
            order.update_status(status_enum)
            self.save_data()
            return True, f"Order status updated to {new_status}"
        except ValueError:
            return False, "Invalid order status"
    
    def generate_invoice(self, order_id):
        if order_id not in self.orders:
            return None, "Order not found"
        
        order = self.orders[order_id]
        invoice = {
            'order_id': order.order_id,
            'customer_email': order.customer_email,
            'items': [],
            'total': order.calculate_total(),
            'status': order.status.value,
            'shipping_address': order.shipping_address,
            'payment_method': order.payment_method,
            'date': order.created_at.strftime("%Y-%m-%d")
        }
        
        # Group items by seller
        seller_items = {}
        for item in order.items:
            seller_email = item.product.seller_email
            if seller_email not in seller_items:
                seller_items[seller_email] = {
                    'seller_name': self.users[seller_email].name,
                    'items': []
                }
            seller_items[seller_email]['items'].append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': item.product.price,
                'total': item.total_price
            })
        
        invoice['sellers'] = seller_items
        return invoice, None

def main():
    eshop = EShop("QuickShop")
    
    while True:
        print("\n=== E-Shopping Application ===")
        print(f"Store: {eshop.name}")
        
        if eshop.current_user:
            print(f"\nLogged in as: {eshop.current_user.name} ({eshop.current_user.user_type.value})")
            
            if eshop.current_user.user_type == UserType.CUSTOMER:
                print("1. Browse Products")
                print("2. Place Order")
                print("3. View My Orders")
                print("4. View Invoice")
                print("5. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    products = eshop.get_available_products()
                    if not products:
                        print("No products available")
                    else:
                        print("\nAvailable Products:")
                        for product in products:
                            print(f"\n{product.name} ({product.category.value})")
                            print(f"Seller: {eshop.users[product.seller_email].name}")
                            print(f"Price: ${product.price}")
                            print(f"Stock: {product.stock}")
                            if product.description:
                                print(f"Description: {product.description}")
                
                elif choice == '2':
                    items = []
                    while True:
                        product_name = input("Enter product name (or 'done' to finish): ")
                        if product_name.lower() == 'done':
                            break
                        
                        seller_email = None
                        product = None
                        
                        # Find product by name
                        matches = [p for p in eshop.get_available_products() if p.name.lower() == product_name.lower()]
                        
                        if not matches:
                            print("Product not found")
                            continue
                        elif len(matches) > 1:
                            print("Multiple sellers found for this product:")
                            for i, p in enumerate(matches, 1):
                                print(f"{i}. {p.name} by {eshop.users[p.seller_email].name} (${p.price})")
                            selection = input("Select seller (number): ")
                            try:
                                product = matches[int(selection)-1]
                            except (ValueError, IndexError):
                                print("Invalid selection")
                                continue
                        else:
                            product = matches[0]
                        
                        try:
                            quantity = int(input("Enter quantity: "))
                            if quantity <= 0:
                                print("Quantity must be positive")
                                continue
                            if quantity > product.stock:
                                print(f"Only {product.stock} available")
                                continue
                            
                            items.append((product.name, product.seller_email, quantity))
                        except ValueError:
                            print("Please enter a valid number")
                    
                    if not items:
                        print("No items in order")
                        continue
                    
                    shipping_address = input("Enter shipping address: ")
                    payment_method = input("Enter payment method: ")
                    
                    success, message = eshop.place_order(items, shipping_address, payment_method)
                    print(message)
                
                elif choice == '3':
                    customer_orders = [order for order in eshop.orders.values() 
                                     if order.customer_email == eshop.current_user.email]
                    if not customer_orders:
                        print("You have no orders")
                    else:
                        print("\nYour Orders:")
                        for order in sorted(customer_orders, key=lambda o: o.created_at, reverse=True):
                            print(f"\nOrder ID: {order.order_id}")
                            print(f"Date: {order.created_at.strftime('%Y-%m-%d')}")
                            print(f"Status: {order.status.value}")
                            print(f"Total: ${order.calculate_total()}")
                
                elif choice == '4':
                    order_id = input("Enter order ID to view invoice: ")
                    invoice, error = eshop.generate_invoice(order_id)
                    if error:
                        print(error)
                    else:
                        print("\n=== Invoice ===")
                        print(f"Order ID: {invoice['order_id']}")
                        print(f"Customer: {invoice['customer_email']}")
                        print(f"Date: {invoice['date']}")
                        print(f"Status: {invoice['status']}")
                        print(f"\nShipping Address: {invoice['shipping_address']}")
                        print(f"Payment Method: {invoice['payment_method']}")
                        
                        print("\nOrder Details:")
                        for seller_email, seller_data in invoice['sellers'].items():
                            print(f"\nSeller: {seller_data['seller_name']}")
                            for item in seller_data['items']:
                                print(f"{item['product_name']} x{item['quantity']} @ ${item['price']} = ${item['total']}")
                        
                        print(f"\nTotal Amount: ${invoice['total']}")
                
                elif choice == '5':
                    eshop.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
            
            elif eshop.current_user.user_type == UserType.SELLER:
                print("1. Add Product")
                print("2. View My Products")
                print("3. View My Orders")
                print("4. Update Order Status")
                print("5. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    name = input("Product name: ")
                    print("Available categories:")
                    for category in ProductCategory:
                        print(category.value)
                    category = input("Category: ")
                    try:
                        price = float(input("Price: "))
                        stock = int(input("Initial stock: "))
                        description = input("Description (optional): ")
                        success, message = eshop.add_product(name, category, price, stock, description)
                        print(message)
                    except ValueError:
                        print("Invalid price or stock value")
                
                elif choice == '2':
                    products = eshop.get_products_by_seller(eshop.current_user.email)
                    if not products:
                        print("You have no products listed")
                    else:
                        print("\nYour Products:")
                        for product in products:
                            print(f"\n{product.name} ({product.category.value})")
                            print(f"Price: ${product.price}")
                            print(f"Stock: {product.stock}")
                            if product.description:
                                print(f"Description: {product.description}")
                
                elif choice == '3':
                    seller_orders = []
                    for order in eshop.orders.values():
                        for item in order.items:
                            if item.product.seller_email == eshop.current_user.email:
                                seller_orders.append(order)
                                break
                    
                    if not seller_orders:
                        print("No orders for your products")
                    else:
                        print("\nOrders for Your Products:")
                        for order in sorted(seller_orders, key=lambda o: o.created_at, reverse=True):
                            print(f"\nOrder ID: {order.order_id}")
                            print(f"Customer: {order.customer_email}")
                            print(f"Date: {order.created_at.strftime('%Y-%m-%d')}")
                            print(f"Status: {order.status.value}")
                            
                            print("Items from you:")
                            for item in order.items:
                                if item.product.seller_email == eshop.current_user.email:
                                    print(f"- {item.product.name} x{item.quantity}")
                
                elif choice == '4':
                    order_id = input("Enter order ID to update: ")
                    print("Available statuses:")
                    for status in OrderStatus:
                        print(status.value)
                    new_status = input("New status: ")
                    success, message = eshop.update_order_status(order_id, new_status)
                    print(message)
                
                elif choice == '5':
                    eshop.logout()
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
                success, message = eshop.login(email, password)
                print(message)
            
            elif choice == '2':
                name = input("Name: ")
                email = input("Email: ")
                password = input("Password: ")
                print("User types:")
                for user_type in UserType:
                    print(user_type.value)
                user_type = input("Select user type: ")
                success, message = eshop.create_account(name, email, password, user_type)
                print(message)
            
            elif choice == '3':
                print("Thank you for shopping with us!")
                break
            
            else:
                print("Invalid choice")

if __name__ == "__main__":
    main()