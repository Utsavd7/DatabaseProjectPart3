import sqlite3
import hashlib
import os
import uuid
from typing import Optional, List, Tuple

class WelcomeHomeApp:
    def __init__(self, db_path='welcomehome.db'):
        """Initialize the application and set up database"""
        self.db_path = db_path
        self.current_user = None
        self.current_order = None
        self._create_database()

    def _create_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL
            )''')

            # Donors table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS donors (
                donor_id TEXT PRIMARY KEY,
                name TEXT,
                contact_info TEXT
            )''')

            # Categories table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                subcategory TEXT
            )''')

            # Items table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                category_id INTEGER,
                name TEXT,
                description TEXT,
                status TEXT DEFAULT 'available',
                location TEXT,
                FOREIGN KEY(category_id) REFERENCES categories(category_id)
            )''')

            # Orders table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                client_username TEXT,
                status TEXT DEFAULT 'in_progress',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_username) REFERENCES users(username)
            )''')

            # Order Items table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                order_id TEXT,
                item_id TEXT,
                PRIMARY KEY(order_id, item_id),
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(item_id) REFERENCES items(item_id)
            )''')

            # Donations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                donation_id TEXT PRIMARY KEY,
                donor_id TEXT,
                staff_username TEXT,
                donation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(donor_id) REFERENCES donors(donor_id),
                FOREIGN KEY(staff_username) REFERENCES users(username)
            )''')

            conn.commit()

    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32).hex()
        
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                       password.encode('utf-8'), 
                                       salt.encode('utf-8'), 
                                       100000).hex()
        return pwdhash, salt

    def register_user(self, username: str, password: str, role: str):
        """Register a new user"""
        hashed_password, salt = self._hash_password(password)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password, salt, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, hashed_password, salt, role))
                conn.commit()
                print(f"User {username} registered successfully.")
        except sqlite3.IntegrityError:
            print("Username already exists.")

    def login(self, username: str, password: str) -> bool:
        """Login user and create session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password, salt, role FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            
            if result:
                stored_password, salt, role = result
                hashed_input, _ = self._hash_password(password, salt)
                
                if hashed_input == stored_password:
                    self.current_user = {
                        'username': username,
                        'role': role
                    }
                    print(f"Welcome, {username}!")
                    return True
            
            print("Invalid username or password.")
            return False

    def find_item_locations(self, item_id: str) -> List[str]:
        """Find locations of all pieces of an item"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT location FROM items WHERE item_id = ?', (item_id,))
            return [row[0] for row in cursor.fetchall()]

    def find_order_items(self, order_id: str) -> List[Tuple[str, List[str]]]:
        """Return list of items in an order with their locations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.item_id, i.location 
                FROM items i
                JOIN order_items oi ON i.item_id = oi.item_id
                WHERE oi.order_id = ?
            ''', (order_id,))
            return cursor.fetchall()

    def accept_donation(self, donor_id: str, items: List[dict]):
        """Accept donation from a donor"""
        if not self.current_user or self.current_user['role'] != 'staff':
            print("Only staff can accept donations.")
            return

        # Verify donor exists
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM donors WHERE donor_id = ?', (donor_id,))
            if not cursor.fetchone():
                print("Donor not registered.")
                return

            # Generate donation ID
            donation_id = str(uuid.uuid4())

            # Record donation
            cursor.execute('''
                INSERT INTO donations (donation_id, donor_id, staff_username)
                VALUES (?, ?, ?)
            ''', (donation_id, donor_id, self.current_user['username']))

            # Insert items
            for item in items:
                item_id = item.get('item_id', str(uuid.uuid4()))
                cursor.execute('''
                    INSERT INTO items (item_id, category_id, name, description, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    item_id, 
                    item.get('category_id'), 
                    item.get('name'), 
                    item.get('description'), 
                    item.get('location')
                ))

            conn.commit()
            print("Donation recorded successfully.")

    def start_order(self, client_username: str):
        """Start a new order for a client"""
        if not self.current_user or self.current_user['role'] != 'staff':
            print("Only staff can start orders.")
            return None

        # Verify client exists
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (client_username,))
            if not cursor.fetchone():
                print("Client not found.")
                return None

            order_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO orders (order_id, client_username)
                VALUES (?, ?)
            ''', (order_id, client_username))
            conn.commit()

            self.current_order = order_id
            return order_id

    def add_to_order(self, item_id: str):
        """Add item to current order"""
        if not self.current_order:
            print("No active order. Start an order first.")
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check item availability
            cursor.execute('SELECT status FROM items WHERE item_id = ?', (item_id,))
            status = cursor.fetchone()
            
            if not status or status[0] != 'available':
                print("Item not available.")
                return

            # Add to order and mark as ordered
            cursor.execute('''
                INSERT INTO order_items (order_id, item_id)
                VALUES (?, ?)
            ''', (self.current_order, item_id))

            cursor.execute('''
                UPDATE items 
                SET status = 'ordered' 
                WHERE item_id = ?
            ''', (item_id,))

            conn.commit()
            print("Item added to order.")

    def prepare_order(self, order_id: str):
        """Update items in an order to ready for delivery"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update items to 'ready' location
            cursor.execute('''
                UPDATE items 
                SET location = 'delivery_holding', status = 'ready'
                WHERE item_id IN (
                    SELECT item_id FROM order_items 
                    WHERE order_id = ?
                )
            ''', (order_id,))

            # Update order status
            cursor.execute('''
                UPDATE orders 
                SET status = 'ready_for_delivery'
                WHERE order_id = ?
            ''', (order_id,))

            conn.commit()
            print("Order prepared for delivery.")

    def get_user_orders(self):
        """Get all orders related to the current user"""
        if not self.current_user:
            print("No user logged in.")
            return []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT order_id, status, created_at 
                FROM orders 
                WHERE client_username = ? OR EXISTS (
                    SELECT 1 FROM order_items oi 
                    JOIN items i ON oi.item_id = i.item_id 
                    WHERE oi.order_id = orders.order_id
                )
            ''', (self.current_user['username'],))
            return cursor.fetchall()

# Example usage demonstration
def main():
    app = WelcomeHomeApp()
    
    # Register users
    app.register_user('admin', 'password123', 'staff')
    app.register_user('client1', 'clientpass', 'client')
    
    # Login
    if app.login('admin', 'password123'):
        # Add some sample categories and items
        # Implement more interactive methods as needed
        pass

if __name__ == '__main__':
    main()
