import json
from datetime import datetime, timedelta

class Book:
    def __init__(self, title, author, isbn, total_copies):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.total_copies = total_copies
        self.available_copies = total_copies
        self.borrowed_by = {}  # user_email: due_date

    def to_dict(self):
        return {
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'total_copies': self.total_copies,
            'available_copies': self.available_copies,
            'borrowed_by': {k: v.isoformat() for k, v in self.borrowed_by.items()}
        }

    @classmethod
    def from_dict(cls, data):
        book = cls(data['title'], data['author'], data['isbn'], data['total_copies'])
        book.available_copies = data['available_copies']
        book.borrowed_by = {k: datetime.fromisoformat(v) for k, v in data['borrowed_by'].items()}
        return book

    def borrow(self, user_email, days=14):
        if self.available_copies <= 0:
            return False
        self.available_copies -= 1
        due_date = datetime.now() + timedelta(days=days)
        self.borrowed_by[user_email] = due_date
        return True

    def return_book(self, user_email):
        if user_email not in self.borrowed_by:
            return False
        self.available_copies += 1
        del self.borrowed_by[user_email]
        return True

    def is_available(self):
        return self.available_copies > 0


class User:
    def __init__(self, email, password, is_admin=False):
        self.email = email
        self.password = password  # In a real system, this would be hashed
        self.is_admin = is_admin
        self.borrowed_books = []

    def to_dict(self):
        return {
            'email': self.email,
            'password': self.password,
            'is_admin': self.is_admin,
            'borrowed_books': self.borrowed_books
        }

    @classmethod
    def from_dict(cls, data):
        user = cls(data['email'], data['password'], data['is_admin'])
        user.borrowed_books = data['borrowed_books']
        return user


class Library:
    def __init__(self):
        self.books = {}  # isbn: Book
        self.users = {}  # email: User
        self.current_user = None
        self.load_data()

    def save_data(self):
        data = {
            'books': {isbn: book.to_dict() for isbn, book in self.books.items()},
            'users': {email: user.to_dict() for email, user in self.users.items()}
        }
        with open('library_data.json', 'w') as f:
            json.dump(data, f)

    def load_data(self):
        try:
            with open('library_data.json', 'r') as f:
                data = json.load(f)
                self.books = {isbn: Book.from_dict(book_data) for isbn, book_data in data['books'].items()}
                self.users = {email: User.from_dict(user_data) for email, user_data in data['users'].items()}
        except FileNotFoundError:
            # Create default admin if no data exists
            admin = User('admin@library.com', 'admin123', True)
            self.users[admin.email] = admin
            self.save_data()

    def create_account(self, email, password, is_admin=False):
        if email in self.users:
            return False, "Email already registered"
        self.users[email] = User(email, password, is_admin)
        self.save_data()
        return True, "Account created successfully"

    def login(self, email, password):
        if email not in self.users:
            return False, "User not found"
        user = self.users[email]
        if user.password != password:
            return False, "Incorrect password"
        self.current_user = user
        return True, "Login successful"

    def logout(self):
        self.current_user = None
        return True, "Logged out successfully"

    def add_book(self, title, author, isbn, total_copies):
        if not self.current_user or not self.current_user.is_admin:
            return False, "Admin access required"
        if isbn in self.books:
            return False, "Book with this ISBN already exists"
        self.books[isbn] = Book(title, author, isbn, total_copies)
        self.save_data()
        return True, "Book added successfully"

    def borrow_book(self, isbn):
        if not self.current_user:
            return False, "Please login first"
        if self.current_user.is_admin:
            return False, "Admins cannot borrow books"
        if isbn not in self.books:
            return False, "Book not found"
        
        book = self.books[isbn]
        if book.borrow(self.current_user.email):
            self.current_user.borrowed_books.append(isbn)
            self.save_data()
            return True, f"Book borrowed successfully. Due date: {book.borrowed_by[self.current_user.email].strftime('%Y-%m-%d')}"
        return False, "No available copies of this book"

    def return_book(self, isbn):
        if not self.current_user:
            return False, "Please login first"
        if self.current_user.is_admin:
            return False, "Admins cannot return books"
        if isbn not in self.books:
            return False, "Book not found"
        if isbn not in self.current_user.borrowed_books:
            return False, "You haven't borrowed this book"
        
        book = self.books[isbn]
        if book.return_book(self.current_user.email):
            self.current_user.borrowed_books.remove(isbn)
            self.save_data()
            return True, "Book returned successfully"
        return False, "Return failed"

    def get_available_books(self):
        available_books = []
        for isbn, book in self.books.items():
            if book.is_available():
                available_books.append({
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'available_copies': book.available_copies
                })
        return available_books

    def get_user_books(self):
        if not self.current_user:
            return []
        user_books = []
        for isbn in self.current_user.borrowed_books:
            if isbn in self.books:
                book = self.books[isbn]
                due_date = book.borrowed_by.get(self.current_user.email)
                user_books.append({
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'due_date': due_date.strftime('%Y-%m-%d') if due_date else 'Unknown'
                })
        return user_books


# Main program
def main():
    library = Library()
    
    while True:
        print("\nLibrary Management System")
        if library.current_user:
            if library.current_user.is_admin:
                print(f"Logged in as Admin: {library.current_user.email}")
                print("1. Add Book")
                print("2. View Available Books")
                print("3. Logout")
            else:
                print(f"Logged in as User: {library.current_user.email}")
                print("1. Borrow Book")
                print("2. Return Book")
                print("3. View Available Books")
                print("4. View My Books")
                print("5. Logout")
        else:
            print("1. Login")
            print("2. Create Account")
            print("3. View Available Books")
            print("4. Exit")
        
        choice = input("Enter your choice: ")
        
        try:
            if not library.current_user:
                # Not logged in options
                if choice == '1':
                    email = input("Email: ")
                    password = input("Password: ")
                    success, message = library.login(email, password)
                    print(message)
                
                elif choice == '2':
                    email = input("Email: ")
                    password = input("Password: ")
                    success, message = library.create_account(email, password)
                    print(message)
                
                elif choice == '3':
                    books = library.get_available_books()
                    if not books:
                        print("No books available")
                    else:
                        print("\nAvailable Books:")
                        for book in books:
                            print(f"{book['title']} by {book['author']} (ISBN: {book['isbn']}) - Available: {book['available_copies']}")
                
                elif choice == '4':
                    print("Goodbye!")
                    break
                
                else:
                    print("Invalid choice")
            
            elif library.current_user.is_admin:
                # Admin options
                if choice == '1':
                    title = input("Book title: ")
                    author = input("Author: ")
                    isbn = input("ISBN: ")
                    try:
                        copies = int(input("Number of copies: "))
                        success, message = library.add_book(title, author, isbn, copies)
                        print(message)
                    except ValueError:
                        print("Please enter a valid number for copies")
                
                elif choice == '2':
                    books = library.get_available_books()
                    if not books:
                        print("No books available")
                    else:
                        print("\nAvailable Books:")
                        for book in books:
                            print(f"{book['title']} by {book['author']} (ISBN: {book['isbn']}) - Available: {book['available_copies']}")
                
                elif choice == '3':
                    success, message = library.logout()
                    print(message)
                
                else:
                    print("Invalid choice")
            
            else:
                # Regular user options
                if choice == '1':
                    isbn = input("Enter ISBN of book to borrow: ")
                    success, message = library.borrow_book(isbn)
                    print(message)
                
                elif choice == '2':
                    isbn = input("Enter ISBN of book to return: ")
                    success, message = library.return_book(isbn)
                    print(message)
                
                elif choice == '3':
                    books = library.get_available_books()
                    if not books:
                        print("No books available")
                    else:
                        print("\nAvailable Books:")
                        for book in books:
                            print(f"{book['title']} by {book['author']} (ISBN: {book['isbn']}) - Available: {book['available_copies']}")
                
                elif choice == '4':
                    books = library.get_user_books()
                    if not books:
                        print("You haven't borrowed any books")
                    else:
                        print("\nYour Borrowed Books:")
                        for book in books:
                            print(f"{book['title']} by {book['author']} (ISBN: {book['isbn']}) - Due: {book['due_date']}")
                
                elif choice == '5':
                    success, message = library.logout()
                    print(message)
                
                else:
                    print("Invalid choice")
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()