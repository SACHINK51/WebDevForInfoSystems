# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
import mysql.connector
from flask_cors import CORS
import json

# Maria database connection
mysql = mysql.connector.connect(user='web', password='webPass',
  host='127.0.0.1',
  database='BookStore')

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'book_store_secret_key'
CORS(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, uID, uName, uType):
        self.id = uID
        self.uName = uName
        self.uType = uType

# Loader function for Flask-Login
@login_manager.user_loader
def load_user(uID):
    user = user_by_id_query(uID)
    if user:
        return user
    else:
        return None

# Function for database query to obtain user by ID
def user_by_id_query(uID):
    sel_query = 'SELECT * FROM users WHERE uID = %s'
    cur = mysql.cur()
    cur.execute(sel_query, (uID,))
    user = cur.fetchone()
    
    if user:
        return User(user[0], user[1], user[2])
    else:
        return None

# User signup route    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_alert = None
    if request.method == 'POST':
        uName = request.form['uName']
        uType = request.form['uType']
        pwd = request.form['pwd']

        # Before storing the password, hash it.
        hashed_pwd = bcrypt.generate_pwd_hash(pwd)

        # Add user information to the database.
        ins_query = '''
            INSERT INTO users (uName, uType, pwd)
            VALUES (%s, %s, %s)
        '''
        cur = mysql.cur(); #create a connection to the SQL instance
        cur.execute(ins_query, (uName, uType, hashed_pwd))
        mysql.commit()
        flash("User registration successful! Please sign in.", "success")
        signup_alert = "User registration successful! Please wait a moment."
        return render_template('signup.html', signup_alert=signup_alert)

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uName = request.form['uName']
        uType = request.form['uType']
        pwd = request.form['pwd']

        # Verify that the password is correct and the user exists.
        sel_query = 'SELECT * FROM users WHERE uName = %s AND uType = %s'
        cur = mysql.cur(); #create a connection to the SQL instance
        cur.execute(sel_query, (uName, uType))
        user = cur.fetchone()
        print(user[0],user[1],user[2],user[3])
        if user and bcrypt.check_pwd_hash(user[3], pwd):
            # Set user information in the session
            session['uID'] = user[0]
            session['uName'] = user[1]
            session['uType'] = user[2]

            login_user(User(user[0], user[1], user[2]))

            if session['uType'] == "Supplier":
                return redirect(url_for('supp_dashboard'));
            else:
                return redirect(url_for('cust_dashboard'));
        else:
            return 'Invalid uName or pwd'

    return render_template('login.html')

# Customer dashboard route
@app.route("/cust_dashboard")
@login_required
def cust_dashboard():
    if current_user.is_authenticated and current_user.uType == "Customer":
        cur = mysql.cur()
        cur.execute('''SELECT b.*, u.uName FROM Book b JOIN users u ON b.uID = u.uID''')
        res  = cur.fetchall()
        books = []
        for row in res :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'uName': row[6]
            }
            books.append(book)
        return render_template('customer.html', books=books)
    else:
        return 'Access refused. You are not a customer.'

# Supplier dashboard route   
@app.route("/supp_dashboard")
@login_required
def supp_dashboard():
    if current_user.is_authenticated and current_user.uType == "Supplier":
        cur = mysql.cur()
        cur.execute('''SELECT * FROM Book WHERE uID = %s''', (session['uID'],))
        res  = cur.fetchall()
        books = []
        for row in res :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'uID': row[6]
            }
            books.append(book)
        return render_template('supplier.html', books=books)
    else:
        return 'Access refused. You are not a Supplier.'

# User logout route
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    # Clear session data
    session.pop('uID', None)
    session.pop('uName', None)
    session.pop('uType', None)
    return redirect(url_for('login'))

# Default route
@app.route("/") 
def defaultPage():
    if current_user.is_authenticated:
        if current_user.uType == "Supplier":
            return redirect(url_for('supp_dashboard'))
        else:
            return redirect(url_for('cust_dashboard'))
    else:
        return redirect(url_for('login'))
    
# Book insertion route
@app.route('/add_book', methods=['GET','POST'])
@login_required
def add_book():
    if current_user.uType == "Supplier":
        try:
            if request.method == 'POST':
                bookName = request.form['bookName']
                price = request.form['price']
                rating = request.form['rating']
                quantity = request.form['quantity']
                bookDescription = request.form['bookDescription']
                uID = session.get('uID')
                
                # Insert book into the Book table
                ins_query = '''
                    INSERT INTO Book (bookName, price, rating, quantity, bookDescription, uID)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cur = mysql.cur()
                cur.execute(ins_query, (bookName, price, rating, quantity, bookDescription, uID))
                mysql.commit()

            return redirect(url_for('supp_dashboard'))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Book updation route
@app.route('/update_book/<int:book_id>', methods=['GET','PUT'])
@login_required
def update_book(book_id):
    if current_user.uType == "Supplier":
        try:
            if request.method == 'PUT':
                data = request.get_json()
                bookName = data.get('new_book_name')
                price = data.get('new_price')
                rating = data.get('new_rating')
                quantity = data.get('new_quantity')
                bookDescription = data.get('new_book_description')
                uID = session.get('uID')
                bookID = book_id

                # Update book in the Book table
                update_query = '''
                    UPDATE Book
                    SET bookName = %s, price = %s, rating = %s, quantity = %s, bookDescription = %s
                    WHERE bookID = %s;
                '''
                cur = mysql.cur()
                resp = cur.execute(update_query, (bookName, price, rating, quantity, bookDescription, bookID))
                mysql.commit()

                return jsonify({'message': 'Book updated successfully'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Book deletion route
@app.route('/delete_book/<int:book_id>', methods=['GET','DELETE'])
@login_required
def delete_book(book_id):
    if current_user.uType == "Supplier":
        try:
            if request.method == 'DELETE':
                delete_query = '''
                    DELETE FROM Book WHERE bookID = %s
                '''
                cur = mysql.cur()
                cur.execute(delete_query, (book_id,))
                mysql.commit()

                return jsonify({'message': 'Book deleted successfully'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Book filtering route
@app.route('/filter/<filter_value>')
@login_required
def filter_method(filter_value):
    if current_user.is_authenticated and current_user.uType == "Customer":
        cur = mysql.cur()
        if(filter_value == "priceLTH"):
            filterQuery='''SELECT b.*, u.uName FROM Book b JOIN users u ON b.uID = u.uID order By price'''
        elif(filter_value == "priceHTL"):
            filterQuery='''SELECT b.*, u.uName FROM Book b JOIN users u ON b.uID = u.uID order By price DESC'''
        elif(filter_value == "ratingLTH"):
            filterQuery='''SELECT b.*, u.uName FROM Book b JOIN users u ON b.uID = u.uID order By rating'''
        elif(filter_value == "ratingHTL"):
            filterQuery='''SELECT b.*, u.uName FROM Book b JOIN users u ON b.uID = u.uID order By rating DESC'''
        else:
            filterQuery='''SELECT b.*, u.uName FROM Book b JOIN users u ON b.uID = u.uID'''
        cur.execute(filterQuery);
        res = cur.fetchall()
        books = []
        for row in res :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'uName': row[6]
            }
            books.append(book)
        return jsonify(books), 200
    else:
        return 'Access denied. You are not a customer.'

# Book searching route    
@app.route('/search/<search_term>')
@login_required
def search_method(search_term):
    if current_user.is_authenticated and current_user.uType == "Customer":
        cur = mysql.cur()
        query = '''
        SELECT b.*, u.uName
        FROM Book b
        JOIN users u ON b.uID = u.uID
        WHERE b.bookName LIKE %s
            OR b.bookDescription LIKE %s
        '''
        cur.execute(query, ('%'+ search_term + '%', '%' + search_term + '%'))
        res = cur.fetchall()
        books = []
        for row in res :
            book = {
                'bookID': row[0],
                'BookName': row[1],
                'Price': row[2],
                'Rating': row[3],
                'Quantity': row[4],
                'BookDescription': row[5],
                'uName': row[6]
            }
            books.append(book)
        return jsonify(books), 200
    else:
        return 'Access denied. You are not a customer.'
      
if __name__ == "__main__":
  app.run(host='0.0.0.0',port='8080', ssl_context=('cert.pem', 'privkey.pem')) #Run the flask app at port 8080
