from flask import Flask,session, request, render_template, redirect, url_for, flash 
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message


import matplotlib.pyplot as plt
import io
import base64






from datetime import datetime

app = Flask(__name__)

app.secret_key = 'yushmanth@123467890'



def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',        
        user='root',             
        password='55555',       
        database='finance',
        auth_plugin='mysql_native_password'      
    )
    return conn


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Validate if the user already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user:
            flash('Email already registered! Please log in.')
            cursor.close()
            conn.close()
            return redirect(url_for('show_login'))

        # Insert the new user into the database
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))
        conn.commit()

        cursor.close()
        conn.close()
        flash('Registration successful! Please log in.')
        return redirect(url_for('show_login'))

    return render_template('register.html')  # Show registration form

# Login route (GET and POST)
@app.route('/login', methods=['GET', 'POST'])
def show_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if user exists and password matches
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):  
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!')
            cursor.close()
            conn.close()
            return redirect(url_for('index'))  
        else:
            flash('Invalid email or password!')
            cursor.close()
            conn.close()
            return redirect(url_for('show_login'))

    return render_template('login.html')  


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/balances')
def balances():
    user_id = session.get('user_id')  
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, CONCAT('**** **** **** ', RIGHT(card_number, 4)) AS card_number, cardholder_name, expiry_date, amount
        FROM accounts WHERE user_id = %s
    """, (user_id,))    
    accounts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('balances.html', accounts=accounts)


# handle adding a new account
@app.route('/add_account', methods=['POST'])
def add_account():
    user_id = session.get('user_id')
    card_number = request.form['card_number']
    cardholder_name = request.form['cardholder_name']
    expiry_date = request.form['expiry_date']
    cvv = request.form['cvv']
    amount = request.form['amount']

    # Add the account to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO accounts (user_id, card_number, cardholder_name, expiry_date, cvv, amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, card_number, cardholder_name, expiry_date, cvv, amount))
        conn.commit()  
        flash('Account added successfully!', 'success') 
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')  
    finally:
        cursor.close()
        conn.close()

    # Fetch the updated accounts list
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM accounts')
    accounts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('balances.html', accounts=accounts)


@app.route('/transactions')
def transactions():
    user_id = session.get('user_id')  
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT t.id, t.account_id, t.payment_type, t.payment_date, t.amount,
               a.cardholder_name
        FROM transactions t
        INNER JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = %s
    ''', (user_id,))
    transactions = cursor.fetchall()

    cursor.execute('''
        SELECT id, cardholder_name
        FROM accounts
        WHERE user_id = %s
    ''', (user_id,))
    accounts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('transactions.html', transactions=transactions, accounts=accounts)


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    user_id = session.get('user_id')

    # Validate user session
    if not user_id:
        return redirect('/login')  # Redirect or error if user not logged in

    # Get form data with default values
    account_id = request.form.get('account_id')
    payment_type = request.form.get('payment_type')
    payment_date = request.form.get('payment_date')
    try:
        amount = float(request.form.get('amount', 0.0))
    except ValueError:
        return "Invalid amount provided", 400

    # Database connection
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Validate account ownership
        cur.execute('''
            SELECT id FROM accounts
            WHERE id = %s AND user_id = %s
        ''', (account_id, user_id))
        account = cur.fetchone()
        if not account:
            return "Unauthorized access to account", 403

        # Insert transaction
        cur.execute('''
            INSERT INTO transactions (account_id, payment_type, payment_date, amount)
            VALUES (%s, %s, %s, %s)
        ''', (account_id, payment_type, payment_date, amount))

        # Update account amount
        if payment_type == "Credit":
            cur.execute('''
                UPDATE accounts
                SET amount = amount + %s
                WHERE id = %s
            ''', (amount, account_id))
        else:
            cur.execute('''
                UPDATE accounts
                SET amount = amount - %s
                WHERE id = %s
            ''', (amount, account_id))

        conn.commit()

        # Fetch updated transactions
        cur.execute('''
            SELECT t.id, t.account_id, t.payment_type, t.payment_date, t.amount,
                   a.cardholder_name
            FROM transactions t
            INNER JOIN accounts a ON t.account_id = a.id
            WHERE a.user_id = %s
        ''', (user_id,))
        transactions = cur.fetchall()

        # Fetch all accounts for the user
        cur.execute('''
            SELECT id, cardholder_name
            FROM accounts
            WHERE user_id = %s
        ''', (user_id,))
        accounts = cur.fetchall()

    except Exception as e:
        conn.rollback()
        return f"An error occurred: {str(e)}", 500
    finally:
        cur.close()
        conn.close()

    # Render template
    return render_template('transactions.html', transactions=transactions, accounts=accounts)

@app.route('/bills')
def bills():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    if not user_id:
        return redirect('/login')  # Redirect to login if not authenticated
    

    # Database connection
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM accounts WHERE user_id = %s', (user_id,))
    accounts = cur.fetchall()

    # Fetch bills associated with the user
    cur.execute('''
        SELECT bill_id, name, category, due_date, amount, status, description
        FROM bills
        WHERE user_id = %s
    ''', (user_id,))
    bills = cur.fetchall()


    cur.close()
    conn.close()

    # Render the bills.html template with data
    return render_template('bills.html', bills=bills,accounts=accounts)



# Route to add a new bill
@app.route('/add_bill', methods=['POST'])
def add_bill():
    user_id = session.get('user_id')  # Get the logged-in user
    if not user_id:
        return redirect('/login')  # Redirect to login if the user is not logged in

    bill_name = request.form['bill_name']
    category = request.form['category']
    due_date = request.form['due_date']
    amount = request.form['amount']
    description = request.form.get('description', '')  # Optional field

    # Insert the new bill into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO bills (user_id, name, category, due_date, amount, description, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, bill_name, category, due_date, amount, description, 'Unpaid'))  # Default status as 'Unpaid'
        conn.commit()

        flash('Bill added successfully!', 'success')  # Success message

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')  # Error message in case of failure

    finally:
        cursor.close()
        conn.close()

    # After adding the bill, redirect to the bills page
    return redirect(url_for('bills'))  # Redirect to bills page to see the updated list


@app.route('/pay_bill/<int:bill_id>', methods=['POST'])
def pay_bill(bill_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    # Get the account_id and payment_date from the form
    account_id = request.form['account_id']
    payment_date = request.form['payment_date']

    # Update the bill status and payment details in the database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE bills
        SET status = 'Paid'
        WHERE bill_id = %s
    ''', (bill_id,))  # Pass bill_id as a tuple


    cursor.execute('SELECT amount FROM bills WHERE bill_id = %s', (bill_id,))
    bill_amount = cursor.fetchone()[0]  # Assuming amount is not NULL

        # Add a new transaction
    cursor.execute('''
            INSERT INTO transactions (account_id, payment_type, payment_date, amount)
            VALUES (%s, %s, %s, %s)
        ''', (account_id, 'Withdrawn', payment_date, bill_amount))

    conn.commit()

    cursor.close()
    conn.close()

    flash('Bill paid successfully!', 'success')
    return redirect(url_for('bills'))
















@app.route('/expenses')
def expenses():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    if not user_id:
        return redirect('/login')  # Redirect to login if not authenticated
    
    # Database connection
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    # Fetch the expenses grouped by category for the logged-in user
    cur.execute('''
    SELECT t.category, SUM(t.amount) AS total_amount
    FROM transactions t
    INNER JOIN accounts a ON t.account_id = a.id
    WHERE a.user_id = %s AND t.payment_type = 'Expenses'
    GROUP BY t.category
''', (user_id,))

    expenses_data = cur.fetchall()

    categories = [row['category'] for row in expenses_data]
    amounts = [row['total_amount'] for row in expenses_data]
    
    cur.close()
    conn.close()

    # Generate the bar chart
    chart_img = create_bar_chart(categories, amounts)

    return render_template('expenses.html', chart_img=chart_img)


def create_bar_chart(categories, amounts):
    """Create a bar chart using Matplotlib and return it as a base64 string."""
    fig, ax = plt.subplots()

    x_indices = range(len(categories))  # Generate indices for the categories
    ax.bar(x_indices, amounts, color='skyblue')
    ax.set_xticks(x_indices)  # Set ticks to match the number of categories
    ax.set_xticklabels(categories, rotation=45, ha='right')  # Label the x-axis with categories

    ax.set_xlabel('Categories')
    ax.set_ylabel('Amount')
    ax.set_title('Expenses by Category')

    # Save the plot to a BytesIO object and convert to base64
    img = io.BytesIO()
    plt.tight_layout()  # Ensure layout doesn't cut off labels
    plt.savefig(img, format='png')
    img.seek(0)
    chart_img = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close(fig)

    return chart_img



# Goals route
@app.route('/goals')
def goals():
    return render_template('goals.html')

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')



if __name__ == '__main__':
    app.run(debug=True)
