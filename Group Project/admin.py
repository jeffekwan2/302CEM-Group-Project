from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import pymysql
import re
import requests
import json
import os
from fileinput import filename
app = Flask(__name__)
app.secret_key = 'tuesmignonne'

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

connection = pymysql.connect(host = 'localhost', 
    user = 'root',
    password = 'JKHKJEFFmysql115', 
    db = '302cem_admin', 
    local_infile = 1,
    cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()

# def getAdminInfo(id):
#     sql = 'SELECT *, SUBSTRING(AdminName, 1, 1) AS sName from tbl_admin WHERE AdminID={id}'
#     connection.ping()
#     cursor.execute(sql.format(id=id))
#     connection.commit()
#     admin = cursor.fetchall()
#     return admin

# def send_data():
#     data = {'message': 'Hello from App1'}
#     url = 'http://localhost:8000/receive-data'
#     response = requests.post(url, json=json.dumps(data))
#     return jsonify({'status': 'Data sent', 'response': response.text})

# def sendproductlist(): 
#     data = ([{"productID":2, "product_name": "Apple Pen", "quantity":18},
# {"productID":3, "product_name": "Apple pie", "quantity":12} ])
    
#     url = "http://localhost:8000/receive-data"
#     r = requests.post(url,data=json.dumps(data))
#     return "order finished"

# def receive_data():
#     data = request.json
#     print("Data received:", data)
#     # Process the data here (e.g., save to database)
#     return jsonify({'status': 'Data received and processed'})

@app.route('/signIn', methods =['GET', 'POST'])
def signIn():
    msg = ''
    if request.method == 'POST' and 'Email' in request.form and 'PW' in request.form:
        Email = request.form['Email']
        PW = request.form['PW']
        connection.ping()
        cursor.execute('SELECT * FROM tbl_admin WHERE Email = % s AND Password = % s', (Email, PW, ))
        connection.commit()
        results = cursor.fetchone()
        if results:
            session['AdminName'] = results['AdminName']
            session['AdminID'] = results['AdminID']
            id = int(session['AdminID'])
            # return redirect(url_for('inventory', id = id))
            return redirect(url_for('inventory'))
        else:
            msg = 'Incorrect username / password !'
    return render_template('adminSignIn.html', msg = msg)

@app.route('/signOut')
def signOut():
    session.pop('username', None)
    return redirect(url_for('signIn'))

@app.route('/admin/inventory')
def inventory():
    if 'userName' in session:
        connection.ping()
        cursor.execute("SELECT * FROM tbl_product")
        connection.commit()
        rows = cursor.fetchall()
        # admin = getAdminInfo(id)
        # return render_template('adminInventory.html', products=rows, admin = admin)
        return render_template('adminInventory.html', products=rows)
    else:
        return redirect(url_for('signIn'))

@app.route('/admin/inventory/add', methods =['GET', 'POST'])
def addInventory():
    if 'userName' in session:
        # admin = getAdminInfo(id)
        if request.method == 'POST':
            connection.ping()
            invName = request.form['invName']
            invDescription = request.form['invDescription']
            invAmount = request.form['invAmount']
            invPrice = request.form['invPrice']
            invPicture = request.files['invPicture']

            UPLOAD_FOLDER = (r'D:\SCOPE\Year 3\302CEM Coding Group\Group Project\static\styles\product_photo')
            app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
            invPicture.save(os.path.join(app.config['UPLOAD_FOLDER'], invPicture.filename))

            sql = 'INSERT INTO tbl_product (ProductName, Description, Stock, UnitRate, Attachment) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute( sql, (invName, invDescription, invAmount, invPrice, invPicture.filename))
            connection.commit()
            
            url = 'http://localhost:8000/customer/receive-data'
            data = ({"ProductName": invName, 
                     "Description": invDescription, 
                     "UnitRate": invPrice, 
                     "Attachment": invPicture.filename})
            
            headers = {'Content-Type': 'application/json'}

            response = requests.post(url, json=json.dumps(data, default=str), headers=headers)

        return redirect(url_for('inventory'))
    else:
        return redirect(url_for('signIn'))

@app.route('/admin/inventory/editInventory/<int:ProductID>', methods=['GET', 'POST'])
def editInventory(ProductID):
    if 'userName' in session:
        return render_template('adminEditInventory.html', ProductID = ProductID)
    else:
        return redirect(url_for('signIn'))

@app.route('/admin/inventory/editInventory/submit', methods=['GET', 'POST'])
def editInventory1():
    if 'userName' in session:
        # admin = getAdminInfo(id)
        if request.method == 'POST':
            connection.ping()
            invName = request.form['invName']
            invDescription = request.form['invDescription']
            invAmount = request.form['invAmount']
            invPrice = request.form['invPrice']
            invPicture = request.files['invPicture']
            ProductID = request.form['ProductID']

            UPLOAD_FOLDER = (r'D:\SCOPE\Year 3\302CEM Coding Group\Group Project\static\styles\product_photo')
            app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
            invPicture.save(os.path.join(app.config['UPLOAD_FOLDER'], invPicture.filename))

            sql = 'UPDATE tbl_product SET ProductName = %s, Description = %s, Stock = %s, UnitRate = %s, Attachment = %s WHERE ProductID = %s'
            cursor.execute( sql, (invName, invDescription, invAmount, invPrice, invPicture.filename, ProductID))
            connection.commit()
            
            url = 'http://localhost:8000/customer/receive-data2'
            data = ({"ProductName": invName, 
                     "Description": invDescription, 
                     "UnitRate": invPrice, 
                     "Attachment": invPicture.filename,
                     "ProductID": ProductID})
            
            headers = {'Content-Type': 'application/json'}

            response = requests.post(url, json=json.dumps(data, default=str), headers=headers)

        return redirect(url_for('inventory'))
    else:
        return redirect(url_for('signIn'))
    
@app.route('/admin/receive-data', methods=['GET', 'POST'])
def receive_data():
    received_data = request.get_json()
    print("Data received:", received_data)

    datas = json.loads(received_data)

    sql = 'INSERT INTO tbl_order (CustomerID, OrderStatus, OrderDate, TotalAmount) VALUES (%s, %s, %s, %s)'
    cursor.execute( sql, (datas[0]['CustomerID'], datas[0]['OrderStatus'], datas[0]['OrderDate'], datas[0]['TotalAmount']))
    connection.commit()

    for data in datas:
        sql1 = "INSERT INTO tbl_orderdetail (OrderID, ProductID, Quantity, Amount) VALUE (%s, %s, %s, %s)"
        cursor.execute( sql1, (data['OrderID'], data['ProductID'], data['Quantity'], data['TotalUnitPrice']))
        connection.commit()

    return redirect(url_for('orders'))
    # return redirect(url_for('product', id = id, user = user))

@app.route('/admin/orders/')
def orders():
    if 'userName' in session:
        connection.ping()
        cursor.execute("SELECT * FROM tbl_order")
        rows = cursor.fetchall()
        return render_template('adminOrder.html', products = rows)
    else:
        return redirect(url_for('signIn'))
    
@app.route('/admin/orders/<int:OrderID>')
def viewOrder(OrderID):
    if 'userName' in session:
        connection.ping()
        cursor.execute("SELECT * FROM tbl_orderdetail WHERE OrderID=%s", OrderID)
        rows = cursor.fetchall()
        return render_template('adminOrderView.html', products = rows)
    else:
        return redirect(url_for('signIn'))
    
@app.route('/admin/orders/<int:OrderID>/orderDeliver')    
def deliverOrder(OrderID):
    if 'userName' in session:
        connection.ping()
        cursor.execute("SELECT * FROM tbl_orderdetail WHERE OrderID=%s", OrderID)
        rows = cursor.fetchall()
        OrderStatus = "Delivering"

        order = []
        data = {}

        for row in rows:
            sql = 'SELECT Stock FROM tbl_product WHERE ProductID = (SELECT ProductID FROM tbl_orderdetail WHERE OrderID = %s AND ProductID = %s)'
            cursor.execute(sql, (OrderID, row['ProductID']))
            tempdata = cursor.fetchall()
            tempstock = int(tempdata[0]['Stock']) - int(row['Quantity'])

            if int(tempdata[0]['Stock']) > row['Quantity']:
                cursor.execute('UPDATE tbl_order SET OrderStatus = %s WHERE OrderID = %s',(OrderStatus, OrderID))
                connection.commit()
                sql1 = 'UPDATE tbl_product SET Stock = %s WHERE ProductID = %s'
                cursor.execute(sql1, (tempstock, row['ProductID']))
                connection.commit()

                data  = {"OrderID": OrderID, 
                        "OrderStatus": OrderStatus}
                order.append(data)

                headers = {'Content-Type': 'application/json'}
                url = 'http://localhost:8000/customer/receive-data1'
                response = requests.post(url, json=json.dumps(order, default=str), headers=headers)
            else:
                pass
       
            return redirect(url_for('orders'))
    else:
        return redirect(url_for('signIn'))
    
@app.route('/profileCreation', methods =['GET', 'POST'])
def profileCreation():
    msg = ''
    if 'userName' in session:
        if request.method == 'POST' and 'Name' in request.form and 'Email' in request.form and 'PW' in request.form and 'ConfirmPW' in request.form and 'PhoneNumber' in request.form:
            Name = request.form['Name']
            PhoneNumber = request.form['PhoneNumber']
            Email = request.form['Email']
            PW = request.form['PW']
            ConfirmPW = request.form['ConfirmPW']

            connection.ping()
            cursor.execute('SELECT * FROM tbl_admin WHERE Email = % s', (Email, ))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
                msg = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', Name):
                msg = 'Name must contain only characters and numbers !'
            elif not Name or not Email or not PW:
                msg = 'Please fill out the form !'
            elif request.form['ConfirmPW'] != request.form['PW']:
                msg = 'Confirm Password does not match with Passowrd'
            else:
                cursor.execute( 'INSERT INTO tbl_admin (Password, AdminName, PhoneNo, Email) VALUES (%s, %s, %s, %s)', (PW, Name, PhoneNumber,Email))
                connection.commit()
                msg = 'You have successfully registered !'

        elif request.method == 'POST':
            msg = 'Please fill out the form !'
        return render_template('adminProfileCreation.html', msg = msg)
    else:
        return redirect(url_for('signIn'))

if __name__=="__main__":
    app.debug = True
    app.run(host="0.0.0.0", port = 5000)

