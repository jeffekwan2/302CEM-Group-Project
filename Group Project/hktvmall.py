from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import pymysql
import re
import requests
import json
import os
from fileinput import filename
import datetime

app = Flask(__name__)
app.secret_key = 'tuesmignonne'

connection = pymysql.connect(host = 'localhost', 
    user = 'root',
    password = 'JKHKJEFFmysql115', 
    db = '302cem_shopping', 
    local_infile = 1,
    cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()

# def getUserInfo(id):
#     sql = 'SELECT *, SUBSTRING(CustomerName, 1, 1) AS sName from tbl_Customer WHERE CustomerID={id}'
#     connection.ping()
#     cursor.execute(sql.format(id=id))
#     user = cursor.fetchall()
#     return user

@app.route('/signUp', methods =['GET', 'POST'])
def signUp():
    msg = ''
    if request.method == 'POST' and 'Name' in request.form and 'Email' in request.form and 'PW' in request.form :
        Name = request.form['Name']
        Email = request.form['Email']
        PW = request.form['PW']
        connection.ping()
        cursor.execute('SELECT * FROM tbl_customer WHERE Email = % s', (Email, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', Name):
            msg = 'Name must contain only characters and numbers !'
        elif not Name or not Email or not PW:
            msg = 'Please fill out the form !'
        else:
            cursor.execute( 'INSERT INTO tbl_customer(Password, CustomerName, Email) VALUES (%s, %s, %s)', (PW, Name, Email))
            connection.commit()
            msg = 'You have successfully registered !'

    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('cusSignUp.html', msg = msg)

@app.route('/signIn', methods =['GET', 'POST'])
def signIn():
    msg = ''
    if request.method == 'POST' and 'Email' in request.form and 'PW' in request.form:
        Email = request.form['Email']
        PW = request.form['PW']
        connection.ping()
        cursor.execute('SELECT * FROM tbl_Customer WHERE Email = % s AND password = % s', (Email, PW, ))
        connection.commit()
        results = cursor.fetchone()
        if results:
            session['CustomerName'] = results['CustomerName']
            session['CustomerID'] = results['CustomerID']
            id = int(session['CustomerID'])
            return redirect(url_for('product'))
        else:
            msg = 'Incorrect username / password !'
    return render_template('cusSignIn.html', msg = msg)

@app.route('/signOut')
def signOut():
    session.pop('username', None)
    return redirect(url_for('signIn'))

@app.route('/customer/receive-data', methods=['GET', 'POST'])
def receive_data():
    received_data = request.get_json()
    print("Data received:", received_data)

    data = json.loads(received_data)
    invName = data['ProductName']
    invDescription = data['Description']
    invPrice = data['UnitRate']
    invPicture = data['Attachment']

    sql = 'INSERT INTO tbl_product (ProductName, Description, UnitRate, Attachment) VALUES (%s, %s, %s, %s)'
    cursor.execute( sql, (invName, invDescription, invPrice, invPicture))
    connection.commit()

    return redirect(url_for('product'))
    # return redirect(url_for('product', id = id, user = user))

@app.route('/customer/receive-data1', methods=['GET', 'POST'])
def receive_data1():
    received_data1 = request.get_json()
    print("Data received:", received_data1)

    data1 = json.loads(received_data1)

    for data in data1:
        cursor.execute('UPDATE tbl_order SET OrderStatus = %s WHERE OrderID = %s',(data['OrderStatus'], data['OrderID']))
        connection.commit()

    return redirect(url_for('orders'))
    # return redirect(url_for('product', id = id, user = user))

@app.route('/customer/receive-data2', methods=['GET', 'POST'])
def receive_data2():
    received_data2 = request.get_json()
    print("Data received:", received_data2)

    data = json.loads(received_data2)
    invName = data['ProductName']
    invDescription = data['Description']
    invPrice = data['UnitRate']
    invPicture = data['Attachment']
    ProductID = data['ProductID']

    sql = 'UPDATE tbl_product SET ProductName = %s, Description = %s, UnitRate = %s, Attachment = %s WHERE ProductID = %s'
    cursor.execute( sql, (invName, invDescription, invPrice, invPicture, ProductID))
    connection.commit()

    return redirect(url_for('product'))
    # return redirect(url_for('product', id = id, user = user))

@app.route('/customer/product', methods=['GET', 'POST'])
def product():
    # user = getUserInfo(id)
    if 'userName' in session:
        connection.ping()
        cursor.execute("SELECT * FROM tbl_product")
        rows = cursor.fetchall()
        # user = getUserInfo(id)
        # return render_template('cusProduct.html', products=rows, user = user)
        return render_template('cusProduct.html', products=rows)
    else:
        return redirect(url_for('signIn'))
    
@app.route('/customer/cart')
def cart():
    if 'userName' in session:
        # connection.ping()
        # with connection.cursor() as cursor:
        #     cursor.execute("SELECT * FROM bookOrder WHERE userID=%s", session["userID"])
        #     bookOrderRows = cursor.fetchall()
        return render_template('cusCart.html')
    else:
        return redirect(url_for('signIn'))
    
@app.route('/customer/product/add-to-cart', methods = ["POST", "GET"])
def addProductToCart():
    cursor = None
    _quantity = int(request.form['quantity'])
    ProductID = request.form['ProductID']

    if _quantity and ProductID and request.method == 'POST':
        connection.ping()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tbl_product WHERE ProductID=%s", (ProductID))
            row = cursor.fetchone()

            itemArray = { str(row['ProductID']) : {'Product' : row['ProductName'], 'ProductID' : str(row['ProductID']),  'quantity' : _quantity, 'price' : row['UnitRate'],'image' : row['Attachment'], 'total_price': _quantity * row['UnitRate']}}

            all_total_price = 0
            all_total_quantity = 0

            session.modified = True

            if 'cart_item' in session:
                if str(row['ProductID']) in session['cart_item']:
                    for key, value in session['cart_item'].items():
                        if str(row['ProductID']) == key:
                            old_quantity = session['cart_item'][key]['quantity']
                            total_quantity = old_quantity + _quantity
                            session['cart_item'][key]['quantity'] = total_quantity
                            session['cart_item'][key]['total_price'] = total_quantity * row['UnitRate']
                            session['cart_item'] = array_merge(session['cart_item'], itemArray)
                else:
                    session['cart_item'] = array_merge(session['cart_item'], itemArray)
                        
                for key, value in session['cart_item'].items():
                    individual_quantity = int(session['cart_item'][key]['quantity'])
                    individual_price = float(session['cart_item'][key]['total_price'])
                    all_total_quantity = all_total_quantity + individual_quantity
                    all_total_price = all_total_price + individual_price
            else:
                session['cart_item'] = itemArray
                all_total_quantity = all_total_quantity + _quantity
                all_total_price = all_total_price + _quantity * row['UnitRate']
            session['all_total_quantity'] = all_total_quantity
            session['all_total_price'] = all_total_price

        return redirect(url_for('product'))
    else:
        return 'Error while adding item to cart'
    
@app.route('/customer/delete/<string:ProductID>')
def delete_product(ProductID):
    all_total_price = 0
    all_total_quantity = 0
    session.modified = True

    for item in session['cart_item'].items():
        if item[0] == ProductID:
            session['cart_item'].pop(item[0], None)
            if 'cart_item' in session:
                for key, value in session['cart_item'].items():
                    individual_quantity = int(session['cart_item'][key]['quantity'])
                    individual_price = float(session['cart_item'][key]['total_price'])
                    all_total_quantity = all_total_quantity + individual_quantity
                    all_total_price = all_total_price + individual_price
            break
    if all_total_quantity == 0:
        session.pop('all_total_quantity')
        session.pop('all_total_price')
    else:
        session['all_total_quantity'] = all_total_quantity
        session['all_total_price'] = all_total_price
    return redirect(url_for('cart'))

def array_merge( first_array , second_array ):
    if isinstance( first_array , list ) and isinstance( second_array , list ):
        return first_array + second_array
    elif isinstance( first_array , dict ) and isinstance( second_array , dict ):
        return dict( list( first_array.items() ) + list( second_array.items() ) )
    elif isinstance( first_array , set ) and isinstance( second_array , set ):
        return first_array.union( second_array )
    return False

@app.route('/customer/cart/submit', methods = ["POST", "GET"])
def cartSubmit():
    if request.method == "POST":
        now = datetime.datetime.now()
        OrderDate =now.strftime("%Y-%m-%d")
        TotalAmount = session['all_total_price']
        connection.ping()

        sql = "INSERT INTO tbl_order (CustomerID, OrderStatus, OrderDate, TotalAmount) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (session['CustomerID'], "Paid", OrderDate, TotalAmount))
        connection.commit()

        sql1 = "SELECT MAX(OrderID) FROM tbl_order"
        cursor.execute(sql1)
        connection.commit()
        result = cursor.fetchone()

        sql2 = "INSERT INTO tbl_orderdetail (OrderID, ProductID, Quantity, Amount) VALUE (%s, %s, %s, %s)"
        for key, value in session['cart_item'].items():
            cursor.execute(sql2, (result['MAX(OrderID)'], session['cart_item'][key]['ProductID'], session['cart_item'][key]['quantity'], session['cart_item'][key]['total_price']))
        connection.commit()

        json_CustomerID = session['CustomerID']
        json_OrderStatus = "Paid"

        order = []
        data = {}

        for key, value in session['cart_item'].items():
            data  = {"CustomerID": json_CustomerID, 
                    "OrderStatus": json_OrderStatus, 
                    "OrderDate": OrderDate,
                    "TotalUnitPrice": session['cart_item'][key]['total_price'],
                    "OrderID": result['MAX(OrderID)'], 
                    "ProductID": session['cart_item'][key]['ProductID'], 
                    "Quantity": session['cart_item'][key]['quantity'],
                    "TotalAmount": TotalAmount}
            order.append(data)

        headers = {'Content-Type': 'application/json'}
        url = 'http://localhost:5000/admin/receive-data'
        response = requests.post(url, json=json.dumps(order, default=str), headers=headers)

        session.pop('cart_item', None)
        return redirect(url_for('cart'))
    
@app.route('/customer/orders')
def orders():
    if 'userName' in session:
        connection.ping()
        cursor.execute("SELECT * FROM tbl_order WHERE CustomerID=%s", session["CustomerID"])
        rows = cursor.fetchall()
        return render_template('cusOrder.html', products = rows)
    else:
        return redirect(url_for('signIn'))
    
@app.route('/customer/orders/<int:OrderID>')
def viewOrder(OrderID):
    if 'userName' in session:
        connection.ping()
        cursor.execute("SELECT * FROM tbl_orderdetail WHERE OrderID=%s", OrderID)
        rows = cursor.fetchall()
        return render_template('cusOrderView.html', products = rows)
    else:
        return redirect(url_for('signIn'))

if __name__=="__main__":
    app.debug = True
    app.run(host="0.0.0.0", port = 8000)