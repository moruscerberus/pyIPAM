from app import db, bcrypt, User  # Import db, bcrypt, and User from app.py

def create_admin_user():
    # Input for admin username and password
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    # Hash password using bcrypt
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create and add the admin user to the database
    admin_user = User(username=username, password=hashed_password)
    db.session.add(admin_user)
    db.session.commit()
    print(f"Admin user {username} created successfully!")

if __name__ == "__main__":
    # Ensure the database tables exist
    from app import app
    with app.app_context():  # Use app context to interact with the database
        db.create_all()  # Create the database tables
        create_admin_user()
