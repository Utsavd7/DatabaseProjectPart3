import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import uuid
import sys
import re
sys.path.append('.')  # Ensure the previous script is importable
from welcomehomeapp import WelcomeHomeApp  # Import the backend logic

class WelcomeHomeGUI:
    def __init__(self, master):
        # Configure root window
        self.master = master
        self.master.title("WelcomeHome Inventory Management")
        self.master.geometry("800x600")
        self.master.minsize(600, 500)

        # Backend application instance
        self.app = WelcomeHomeApp()

        # Current user and state tracking
        self.current_user = None

        # Apply modern styling
        self.apply_modern_styling()

        # Create initial login window
        self.create_login_window()

    def apply_modern_styling(self):
        """Apply modern styling to the application"""
        style = ttk.Style()
        style.theme_use('clam')

        # Color palette
        bg_color = '#f4f4f4'
        primary_color = '#4A90E2'
        secondary_color = '#50C878'
        text_color = '#333333'

        # Configure root window
        self.master.configure(background=bg_color)

        # Button styling
        style.configure('TButton', 
            background=primary_color, 
            foreground='white', 
            font=('Helvetica', 10, 'bold'),
            padding=10
        )
        style.map('TButton', 
            background=[('active', secondary_color)],
            foreground=[('active', 'white')]
        )

        # Entry styling
        style.configure('TEntry', 
            font=('Helvetica', 10),
            padding=5
        )

        # Label styling
        style.configure('TLabel', 
            font=('Helvetica', 10),
            background=bg_color,
            foreground=text_color
        )

    def create_login_window(self):
        """Create login window with modern design"""
        # Clear any existing widgets
        for widget in self.master.winfo_children():
            widget.destroy()

        # Login Frame
        login_frame = tk.Frame(self.master, padx=40, pady=40, bg='#f4f4f4')
        login_frame.pack(expand=True)

        # Title
        title_label = tk.Label(login_frame, 
            text="WelcomeHome", 
            font=("Helvetica", 24, "bold"), 
            fg='#4A90E2', 
            bg='#f4f4f4')
        title_label.pack(pady=20)

        # Username
        username_label = tk.Label(login_frame, text="Username", bg='#f4f4f4')
        username_label.pack()
        self.username_entry = ttk.Entry(login_frame, width=40)
        self.username_entry.pack(pady=5)

        # Password
        password_label = tk.Label(login_frame, text="Password", bg='#f4f4f4')
        password_label.pack()
        self.password_entry = ttk.Entry(login_frame, show="*", width=40)
        self.password_entry.pack(pady=5)

        # Login Button
        login_button = ttk.Button(login_frame, text="Login", command=self.login, width=30)
        login_button.pack(pady=10)

        # Register Button
        register_button = ttk.Button(login_frame, text="Register New User", command=self.open_registration_window, width=30)
        register_button.pack(pady=5)

    def validate_input(self, username, password):
        """Validate input before submission"""
        if not username:
            messagebox.showwarning("Input Error", "Username cannot be empty")
            return False
        if len(password) < 6:
            messagebox.showwarning("Input Error", "Password must be at least 6 characters long")
            return False
        return True

    def login(self):
        """Enhanced login method with validation"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not self.validate_input(username, password):
            return

        try:
            if self.app.login(username, password):
                self.current_user = self.app.current_user
                self.create_main_dashboard()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")
        except Exception as e:
            self.handle_exception(str(e))

    def open_registration_window(self):
        """Open user registration window with validation"""
        reg_window = tk.Toplevel(self.master)
        reg_window.title("User Registration")
        reg_window.geometry("400x350")
        reg_window.configure(background='#f4f4f4')

        tk.Label(reg_window, text="Register New User", 
                 font=("Helvetica", 16, "bold"), 
                 bg='#f4f4f4', 
                 fg='#4A90E2').pack(pady=10)

        # Username
        tk.Label(reg_window, text="Username", bg='#f4f4f4').pack()
        username_entry = ttk.Entry(reg_window, width=30)
        username_entry.pack(pady=5)

        # Password
        tk.Label(reg_window, text="Password (min 6 characters)", bg='#f4f4f4').pack()
        password_entry = ttk.Entry(reg_window, show="*", width=30)
        password_entry.pack(pady=5)

        # Role Selection
        tk.Label(reg_window, text="Role", bg='#f4f4f4').pack()
        role_var = tk.StringVar(value="client")
        roles = ["client", "staff", "volunteer"]
        role_dropdown = ttk.Combobox(reg_window, 
                                     textvariable=role_var, 
                                     values=roles, 
                                     state="readonly",
                                     width=27)
        role_dropdown.pack(pady=5)

        # Register Button
        def register():
            username = username_entry.get().strip()
            password = password_entry.get()
            role = role_var.get()

            # Validate inputs
            if not username:
                messagebox.showwarning("Error", "Username cannot be empty")
                return
            if len(password) < 6:
                messagebox.showwarning("Error", "Password must be at least 6 characters")
                return

            try:
                self.app.register_user(username, password, role)
                messagebox.showinfo("Success", "User registered successfully")
                reg_window.destroy()
            except Exception as e:
                messagebox.showerror("Registration Error", str(e))

        ttk.Button(reg_window, text="Register", command=register).pack(pady=10)

    def create_main_dashboard(self):
        """Redesigned dashboard with grid layout and role-based actions"""
        # Clear existing widgets
        for widget in self.master.winfo_children():
            widget.destroy()

        # Main dashboard frame
        dashboard_frame = tk.Frame(self.master, padx=20, pady=20, bg='#f4f4f4')
        dashboard_frame.pack(expand=True, fill=tk.BOTH)

        # Welcome header
        welcome_label = tk.Label(dashboard_frame, 
            text=f"Welcome, {self.current_user['username']}", 
            font=("Helvetica", 18, "bold"),
            fg='#333333',
            bg='#f4f4f4'
        )
        welcome_label.pack(pady=20)

        # Role display
        role_label = tk.Label(dashboard_frame, 
            text=f"Role: {self.current_user['role'].capitalize()}", 
            font=("Helvetica", 12),
            fg='#666666',
            bg='#f4f4f4'
        )
        role_label.pack(pady=10)

        # Action buttons with icons (simulated with text)
        actions = [
            ("📦 Donations", self.handle_donation),
            ("📝 Start Order", self.start_order),
            ("🚚 Prepare Order", self.prepare_order),
            ("🔍 Find Item Locations", self.find_item_locations),
            ("📋 View Orders", self.view_user_orders)
        ]

        # Create buttons dynamically based on user role
        for text, command in actions:
            if (self.current_user['role'] in ['staff', 'admin']) or text not in ["📦 Donations", "📝 Start Order", "🚚 Prepare Order"]:
                btn = ttk.Button(dashboard_frame, 
                    text=text, 
                    command=command, 
                    width=30
                )
                btn.pack(pady=5)

        # Logout button
        logout_btn = ttk.Button(dashboard_frame, 
            text="🚪 Logout", 
            command=self.logout, 
            width=30
        )
        logout_btn.pack(side=tk.BOTTOM, pady=20)

    def logout(self):
        """Enhanced logout with confirmation"""
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.current_user = None
            self.create_login_window()

    def handle_donation(self):
        """Handle donation process with enhanced error handling"""
        try:
            # Donor ID input
            donor_id = simpledialog.askstring("Donation", "Enter Donor ID:")
            if not donor_id:
                return

            # Multiple item entry
            items = []
            while True:
                item_name = simpledialog.askstring("Donation", "Enter Item Name (or cancel to finish):")
                if not item_name:
                    break

                item_details = {
                    'item_id': str(uuid.uuid4()),
                    'name': item_name,
                    'description': simpledialog.askstring("Donation", f"Description for {item_name}:") or "",
                    'location': simpledialog.askstring("Donation", f"Storage Location for {item_name}:") or ""
                }
                items.append(item_details)

            # Process donation
            self.app.accept_donation(donor_id, items)
            messagebox.showinfo("Donation", "Donation recorded successfully!")
        
        except Exception as e:
            messagebox.showerror("Donation Error", str(e))

    def start_order(self):
        """Start a new order with error handling"""
        try:
            client_username = simpledialog.askstring("New Order", "Enter Client Username:")
            if client_username:
                order_id = self.app.start_order(client_username)
                if order_id:
                    messagebox.showinfo("Order Started", f"New order created: {order_id}")
        except Exception as e:
            messagebox.showerror("Order Error", str(e))

    def find_item_locations(self):
        """Find locations of an item"""
        item_id = simpledialog.askstring("Find Item", "Enter Item ID:")
        if item_id:
            try:
                locations = self.app.find_item_locations(item_id)
                if locations:
                    messagebox.showinfo("Item Locations", "\n".join(locations))
                else:
                    messagebox.showinfo("Item Locations", "No locations found for this item.")
            except Exception as e:
                messagebox.showerror("Search Error", str(e))

    def find_order_items(self):
        """Find items in an order"""
        order_id = simpledialog.askstring("Find Order", "Enter Order ID:")
        if order_id:
            try:
                items = self.app.find_order_items(order_id)
                if items:
                    item_list = "\n".join([f"Item ID: {item[0]}, Location: {item[1]}" for item in items])
                    messagebox.showinfo("Order Items", item_list)
                else:
                    messagebox.showinfo("Order Items", "No items found for this order.")
            except Exception as e:
                messagebox.showerror("Search Error", str(e))

    def prepare_order(self):
        """Prepare an order for delivery"""
        try:
            order_id = simpledialog.askstring("Prepare Order", "Enter Order ID:")
            if order_id:
                self.app.prepare_order(order_id)
                messagebox.showinfo("Order Preparation", "Order prepared for delivery!")
        except Exception as e:
            messagebox.showerror("Order Error", str(e))

    def view_user_orders(self):
        """View orders related to the current user"""
        try:
            orders = self.app.get_user_orders()
            if orders:
                order_list = "\n".join([f"Order ID: {order[0]}, Status: {order[1]}, Created: {order[2]}" for order in orders])
                messagebox.showinfo("My Orders", order_list)
            else:
                messagebox.showinfo("My Orders", "No orders found.")
        except Exception as e:
            messagebox.showerror("Orders Error", str(e))

    def add_to_order(self):
        """Add an item to the current order"""
        try:
            item_id = simpledialog.askstring("Add to Order", "Enter Item ID to add:")
            if item_id:
                self.app.add_to_order(item_id)
                messagebox.showinfo("Order Update", "Item added to order successfully!")
        except Exception as e:
            messagebox.showerror("Order Error", str(e))

    def handle_exception(self, error_message):
        """Centralized error handling method"""
        error_window = tk.Toplevel(self.master)
        error_window.title("Error")
        error_window.geometry("300x200")
        error_window.configure(background='#f4f4f4')
        
        # Error icon and message
        tk.Label(error_window, text="⚠️ Error", 
                 font=("Helvetica", 16, "bold"), 
                 bg='#f4f4f4', 
                 fg='#FF6347').pack(pady=10)
        tk.Label(error_window, text=error_message, 
                 wraplength=250, 
                 bg='#f4f4f4').pack(pady=10)
        
        # Close button
        ttk.Button(error_window, text="Close", command=error_window.destroy).pack(pady=10)

def main():
    root = tk.Tk()
    app = WelcomeHomeGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()