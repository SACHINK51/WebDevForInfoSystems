# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
import pyodbc
from flask_cors import CORS
import json

# MySQL database connection
mysql = (
    r'DRIVER={SQL Server};'
    r'SERVER=DESKTOP-GER7MB4\SQLEXPRESS;'
    r'DATABASE=BookStore;'
    ##r'UID=DESKTOP-GER7MB4\Dell;'
    ##r'PWD='
)

# Establishing connection to the database
conn = pyodbc.connect(mysql)

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'book_store_secret_key'
CORS(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, userID, userName, userType):
        self.id = userID
        self.userName = userName
        self.userType = userType

# Loader function for Flask-Login
@login_manager.user_loader
def load_user(userID):
    user = query_user_by_id(userID)
    if user:
        return user
    else:
        return None

# Database query function to get user by ID
def query_user_by_id(userID):
    select_query = 'SELECT * FROM users WHERE userID = ?'
    cursor = conn.cursor()
    cursor.execute(select_query, (userID,))
    user = cursor.fetchone()
    
    if user:
        return User(user[0], user[1], user[2])
    else:
        return None

# Route for user signup    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_alert = None
    if request.method == 'POST':
        userName = request.form['userName']
        userType = request.form['userType']
        password = request.form['password']

        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(password)

        # Insert user details into the database
        insert_query = '''
            INSERT INTO users (userName, UserType, Password)
            VALUES (?, ?, ?)
        '''
        cursor = conn.cursor(); #create a connection to the SQL instance
        cursor.execute(insert_query, (userName, userType, hashed_password))
        conn.commit()
        flash("Signup successful! Please login.", "success")
        signup_alert = "Signup successful! Please wait a moment."
        return render_template('signup.html', signup_alert=signup_alert)

    return render_template('signup.html')

# Route for user login	
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userName = request.form['userName']
        userType = request.form['userType']
        password = request.form['password']

        # Check if the user exists and the password is correct
        select_query = 'SELECT * FROM users WHERE userName = ? AND userType = ?'
        cursor = conn.cursor(); #create a connection to the SQL instance
        cursor.execute(select_query, (userName, userType))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user[3], password):
            # Set user information in the session
            session['userID'] = user[0]
            session['userName'] = user[1]
            session['userType'] = user[2]

            login_user(User(user[0], user[1], user[2]))

            if session['userType'] == "Supplier":
                return redirect(url_for('supplier_dashboard'));
            else:
                return redirect(url_for('customer_dashboard'));
        else:
            return 'Invalid userName or password'

    return render_template('login.html')

# Route for customer dashboard
@app.route("/customer_dashboard")
@login_required
def customer_dashboard():
    if current_user.is_authenticated and current_user.userType == "Customer":
        cur = conn.cursor()
        cur.execute('''SELECT b.*, u.userName FROM Book b JOIN users u ON b.userID = u.userID''')
        results  = cur.fetchall()
        books = []
        for row in results :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'userName': row[6]
            }
            books.append(book)
        return render_template('customer.html', books=books)
    else:
        return 'Access denied. You are not a customer.'

# Route for supplier dashboard     
@app.route("/supplier_dashboard")
@login_required
def supplier_dashboard():
    if current_user.is_authenticated and current_user.userType == "Supplier":
        cur = conn.cursor()
        cur.execute('''SELECT * FROM Book WHERE userID = ?''', (session['userID'],))
        results  = cur.fetchall()
        books = []
        for row in results :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'userID': row[6]
            }
            books.append(book)
        return render_template('supplier.html', books=books)
    else:
        return 'Access denied. You are not a Supplier.'

# Route for user logout
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    # Clear session data
    session.pop('userID', None)
    session.pop('userName', None)
    session.pop('userType', None)
    return redirect(url_for('login'))

# Default route
@app.route("/") 
def defaultPage():
    if current_user.is_authenticated:
        if current_user.userType == "Supplier":
            return redirect(url_for('supplier_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    else:
        return redirect(url_for('login'))
    
# Route for adding a new product
@app.route('/add_book', methods=['GET','POST'])
@login_required
def add_book():
    if current_user.userType == "Supplier":
        try:
            if request.method == 'POST':
                bookName = request.form['bookName']
                price = request.form['price']
                rating = request.form['rating']
                quantity = request.form['quantity']
                bookDescription = request.form['bookDescription']
                userID = session.get('userID')
                
                # Insert product into the Product table
                insert_query = '''
                    INSERT INTO Book (bookName, price, rating, quantity, bookDescription, userID)
                    VALUES (?, ?, ?, ?, ?, ?)
                '''
                cursor = conn.cursor()
                cursor.execute(insert_query, (bookName, price, rating, quantity, bookDescription, userID))
                conn.commit()

            return redirect(url_for('supplier_dashboard'))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Route for updating a product
@app.route('/update_book/<int:book_id>', methods=['GET','PUT'])
@login_required
def update_book(book_id):
    if current_user.userType == "Supplier":
        try:
            if request.method == 'PUT':
                data = request.get_json()
                bookName = data.get('new_book_name')
                price = data.get('new_price')
                rating = data.get('new_rating')
                quantity = data.get('new_quantity')
                bookDescription = data.get('new_book_description')
                userID = session.get('userID')
                bookID = book_id

                # Update product in the Product table
                update_query = '''
                    UPDATE Book
                    SET bookName = ?, price = ?, rating = ?, quantity = ?, bookDescription = ?
                    WHERE bookID = ?;
                '''
                cursor = conn.cursor()
                resp = cursor.execute(update_query, (bookName, price, rating, quantity, bookDescription, bookID))
                mysql.commit()

                return jsonify({'message': 'Book updated successfully'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Route for deleting a book
@app.route('/delete_book/<int:book_id>', methods=['GET','DELETE'])
@login_required
def delete_book(book_id):
    if current_user.userType == "Supplier":
        try:
            if request.method == 'DELETE':
                delete_query = '''
                    DELETE FROM Book WHERE bookID = ?
                '''
                cursor = conn.cursor()
                cursor.execute(delete_query, (book_id,))
                conn.commit()

                return jsonify({'message': 'Book deleted successfully'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Route for filtering a product
@app.route('/filter/<filter_value>')
@login_required
def filter_method(filter_value):
    if current_user.is_authenticated and current_user.userType == "Customer":
        cursor = conn.cursor()
        if(filter_value == "priceLTH"):
            filterQuery='''SELECT b.*, u.userName FROM Book b JOIN users u ON b.userID = u.userID order By price'''
        elif(filter_value == "priceHTL"):
            filterQuery='''SELECT b.*, u.userName FROM Book b JOIN users u ON b.userID = u.userID order By price DESC'''
        elif(filter_value == "ratingLTH"):
            filterQuery='''SELECT b.*, u.userName FROM Book b JOIN users u ON b.userID = u.userID order By rating'''
        elif(filter_value == "ratingHTL"):
            filterQuery='''SELECT b.*, u.userName FROM Book b JOIN users u ON b.userID = u.userID order By rating DESC'''
        else:
            filterQuery='''SELECT b.*, u.userName FROM Book b JOIN users u ON b.userID = u.userID'''
        cursor.execute(filterQuery);
        results = cursor.fetchall()
        books = []
        for row in results :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'userName': row[6]
            }
            books.append(book)
        return jsonify(books), 200
    else:
        return 'Access denied. You are not a customer.'

# Route for searching a book    
@app.route('/search/<search_term>')
@login_required
def search_method(search_term):
    if current_user.is_authenticated and current_user.userType == "Customer":
        cursor = conn.cursor()
        query = '''
        SELECT b.*, u.userName
        FROM Book b
        JOIN users u ON b.userID = u.userID
        WHERE n.bookName LIKE ?
            OR b.bookDescription LIKE ?
        '''
        cursor.execute(query, ('%'+ search_term + '%', '%' + search_term + '%'))
        results = cursor.fetchall()
        books = []
        for row in results :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'userName': row[6]
            }
            books.append(book)
        return jsonify(books), 200
    else:
        return 'Access denied. You are not a customer.'
    
      
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080)

##if __name__ == "__main__":
  ##app.run(host='0.0.0.0',port='8080', ssl_context=('cert.pem', 'privkey.pem')) #Run the flask app at port 8080
