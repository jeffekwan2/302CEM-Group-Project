from flask import Flask, render_template, request, session, redirect, url_for
import pymysql
app = Flask(__name__)
app.secret_key = 'tuesmignonne'

connection = pymysql.connect(host = 'localhost', 
    user = 'root',
    password = 'JKHKJEFFmysql115', 
    db = 'webProject', 
    local_infile = 1,
    cursorclass=pymysql.cursors.DictCursor)

@app.route('/signUp')
def student():
    return render_template('signUpPage.html')

@app.route('/signUpSuccess', methods=["POST", "GET"])
def result():
    if request.method == "POST":
        userName = request.form['userName']
        pw = request.form['pw']
        phoneNumber = request.form['phoneNumber']
        if request.form['confirm'] == request.form['pw']:
            sql = 'INSERT INTO loginInfo(userName, pw, phoneNumber) VALUES (%s, %s, %s)'
            connection.ping()
            with connection.cursor() as cursor:
                cursor.execute(sql, (userName, pw, phoneNumber))

    try:
        connection.commit()

    except Exception as e:
        connection.rollback()
    
    return render_template('signUpSuccess.html')

@app.route('/logIn', methods =['GET', 'POST'])
def login():
    if request.method == 'POST' and 'userName' in request.form and 'pw' in request.form:
        userName = request.form['userName']
        pw = request.form['pw']
        connection.ping()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM loginInfo WHERE userName = % s AND pw = % s', (userName, pw ))
            connection.commit()
            results = cursor.fetchone()
            if results:
                session['userName'] = results['userName']
                session['userID'] = results['userID']
                return redirect('http://localhost:8000/bookBrowsing')
    return render_template('loginPage.html')

@app.route('/logout')
def logout():
    session.pop('userName', None)
    return redirect('http://localhost:8000/logIn')

@app.route('/resetPassword')
def resetPassword():
    return render_template('resetPw.html')

@app.route('/resetPasswordSuccess', methods = ["POST", "GET"])
def resetPasswordSuccess():
    if request.method == "POST":
        userName = request.form['userName']
        pw = request.form['pw']
        phoneNumber = request.form['phoneNumber']
        if request.form['confirm'] == request.form['pw']:
            connection.ping()
            with connection.cursor() as cursor:
                cursor.execute('UPDATE loginInfo SET pw = %s WHERE userName = %s AND phoneNumber = %s', (pw, userName, phoneNumber))
        try:
            connection.commit()
        except Exception as e:
            connection.rollback()
            
    return render_template('pwResetSuccess.html')

@app.route('/bookBrowsing')
def bookBrowsing():
    if 'userName' in session:
        connection.ping()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM inventory")
            rows = cursor.fetchall()
            return render_template('bookBrowsing.html', products=rows)
    else:
        return redirect('http://localhost:8000/logIn')

@app.route('/customisationPage')
def customisePrinting():
    if 'userName' in session:
        return render_template("customisationPage.html")
    else:
        return redirect('http://localhost:8000/logIn')

@app.route('/add', methods = ["POST", "GET"])
def addProductToCart():
    cursor = None
    _quantity = int(request.form['quantity'])
    _bookCode = request.form['bookCode']

    if _quantity and _bookCode and request.method == 'POST':
        connection.ping()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM inventory WHERE bookCode=%s", (_bookCode))
            row = cursor.fetchone()

            itemArray = { row['bookCode'] : {'bookTitle' : row['bookTitle'], 'bookCode' : row['bookCode'], 'quantity' : _quantity, 'price' : row['price'],'image' : row['books'], 'total_price': _quantity * row['price']}}

            all_total_price = 0
            all_total_quantity = 0

            session.modified = True

            if 'cart_item' in session:
                if row['bookCode'] in session['cart_item']:
                    for key, value in session['cart_item'].items():
                        if row['bookCode'] == key:
                            old_quantity = session['cart_item'][key]['quantity']
                            total_quantity = old_quantity + _quantity
                            session['cart_item'][key]['quantity'] = total_quantity
                            session['cart_item'][key]['total_price'] = total_quantity * row['price']
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
                all_total_price = all_total_price + _quantity * row['price']
            session['all_total_quantity'] = all_total_quantity
            session['all_total_price'] = all_total_price

        return redirect('http://localhost:8000/bookBrowsing')
    else:
        return 'Error while adding item to cart'

@app.route('/bookCartOrder')
def products():
    if 'userName' in session:
        connection.ping()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM bookOrder WHERE userID=%s", session["userID"])
            bookOrderRows = cursor.fetchall()
            return render_template('cart.html', bookOrders = bookOrderRows)
    else:
        return redirect('http://localhost:8000/logIn')

@app.route('/delete/<string:bookCode>')
def delete_product(bookCode):
    all_total_price = 0
    all_total_quantity = 0
    session.modified = True

    for item in session['cart_item'].items():
        if item[0] == bookCode:
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
    return redirect(url_for('.products'))

def array_merge( first_array , second_array ):
    if isinstance( first_array , list ) and isinstance( second_array , list ):
        return first_array + second_array
    elif isinstance( first_array , dict ) and isinstance( second_array , dict ):
        return dict( list( first_array.items() ) + list( second_array.items() ) )
    elif isinstance( first_array , set ) and isinstance( second_array , set ):
        return first_array.union( second_array )
    return False

@app.route('/customisationPage/add', methods = ['POST', 'GET'])
def customisationPageAdd():
    if request.method == "POST":
        customiseBookName = request.form['customiseBookName']
        bookType = request.form['bookType']
        sql = 'INSERT INTO customise(customiseBookName, bookType, userID) VALUES (%s, %s, %s)'
        connection.ping()
        with connection.cursor() as cursor:
            cursor.execute(sql, (customiseBookName, bookType, session["userID"]))
    try:
        connection.commit()

    except Exception as e:
        connection.rollback()
    
    return redirect("http://localhost:8000/customisationPage")

@app.route('/customisationOrders')
def customisationOrders():
    connection.ping()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM customise WHERE userID=%s", session["userID"])
        customisationOrderRows = cursor.fetchall()
        return render_template('customisationOrders.html', customisationOrders = customisationOrderRows)
    
@app.route('/bookCartOrder/submit', methods = ["POST", "GET"])
def bookOrderSubmit():
    if request.method == "POST":
        connection.ping()
        with connection.cursor() as cursor:
            for key, value in session['cart_item'].items():
                    cursor.execute("INSERT INTO bookOrder(userID, amount, price, bookCode) VALUE (%s, %s, %s, %s)", (session["userID"], session['cart_item'][key]['quantity'], session['cart_item'][key]['total_price'], session['cart_item'][key]['bookCode']))
    try:
        connection.commit()

    except Exception as e:
        connection.rollback()

    session.pop('cart_item', None)

    return redirect('http://localhost:8000/bookCartOrder')

connection.close()
if __name__=="__main__":
    app.debug = True
    app.run(host="0.0.0.0", port = 8080)