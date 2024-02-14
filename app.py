from flask import Flask, render_template, redirect, session, request
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///healthify.db")

#Defining Error Messages
def error(error_message):
    return render_template("error.html", error_message=error_message)

#For index route
@app.route("/")
def index():
    global user_id
    global username
    if not session.get("user_id"):
        return redirect("/login")
    username = session.get("username")
    user_id = session.get("user_id")
    print(f'TESTHERE: {session}')
    convert_month = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
    }
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    xValues = []
    yValues = []
#Looping through to add months to x-axis
    for i in range(4):
        if current_month == 0:
            current_month = 12
        xValues.append(convert_month[current_month])
        current_month -= 1
    activitycount = db.execute("SELECT * FROM weight WHERE user_id=?;", user_id)
#Looping through the database to add datas that lie within the specific months
    current_month = datetime.datetime.now().month
    for i in xValues:
        month_count = 0
        for counts in activitycount:
            if int(counts["time"][0:4]) == current_year and int(counts["time"][5:7]) == current_month:
                month_count += 1
        yValues.append(month_count)
        if current_month == 1:
            current_year -= 1
            current_month = 12
        else:
            current_month -= 1
    xValues.reverse()
    yValues.reverse()
    print(yValues)
    return render_template("index.html", username=username, user_id=user_id, xValues=xValues, yValues=yValues)

#For login route
@app.route("/login", methods=["POST", "GET"])
def login():
    #If have not logged in
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        #Error testing
        if not username:
            return error("Username field cannot be empty")
        elif not password:
            return error("Password field cannot be empty")
        rows = db.execute("SELECT * FROM users WHERE username=?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return error("Incorrect Username or Password")
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        return redirect("/")
    #If already logged in
    if session.get("user_id"):
        return redirect("/")
    #If log out is clicked
    return render_template("login.html")

#For logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#For register route
@app.route("/register", methods=["POST", "GET"])
def register():
    #Upon clicking register
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return error("Username field cannot be empty")
        elif not request.form.get("password"):
            return error("Password field cannot be empty")
        elif not request.form.get("rpassword"):
            return error("Reconfirm Password field cannot be empty")
        elif request.form.get("password") != request.form.get("rpassword"):
            return error("Password did not match reconfirmation passowrd")
        passworddb = generate_password_hash(request.form.get("password"))
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?,?);", username, passworddb)
            user_id = db.execute("SELECT id FROM users WHERE username=?;", username)[0]["id"]
            db.execute("INSERT INTO settings (user_id) VALUES(?);", user_id)
            return redirect("/")
        except:
            return error("Username already taken.")
    #Bring to register page
    return render_template("register.html")

#For weight route
@app.route("/weight", methods=["POST","GET"])
def weight():
    user_id = session.get("user_id")
    username = session.get("username")
    if request.method == "POST":
        weight_input = request.form.get("weight")
        if not weight_input:
            return redirect("/weight")
        db.execute("INSERT INTO weight (weight, user_id) VALUES(?,?);", weight_input, user_id)
        return redirect("/weight")
    if not session.get("user_id"):
        return redirect("/login")
    weights = db.execute("SELECT * FROM weight WHERE user_id=?;", user_id)
    latestweights = db.execute("SELECT * FROM weight WHERE user_id=? LIMIT 15;", user_id)
    xValues = []
    yValues = []
    rows = db.execute("SELECT * FROM settings WHERE user_id=?;", user_id)[0]
    lwl = rows["lwl"]
    uwl = rows["uwl"]
    fromdate = rows["fromdate"]
    todate = rows["todate"]
    #Adding only datas starting from the specified date and before a specified date
    for weight in weights:
        year = int(weight["time"][0:4])
        month = int(weight["time"][5:7])
        day = int(weight["time"][8:10])
        #1.If data's year falls inbetween the 2 specified years
        if year > int(fromdate[0:4]) and year < int(todate[0:4]):
            xValues.append(weight["time"][0:10])
            yValues.append(weight["weight"])
        #2.If data year is same as from year
        elif year == int(fromdate[0:4]) and year < int(todate[0:4]):
            #If data's month is more than from date's month
            if month > int(fromdate[5:7]):
                xValues.append(weight["time"][0:10])
                yValues.append(weight["weight"])
            #If data's month is same as from date's month
            elif month == int(fromdate[5:7]):
                #Check date
                if day >= int(fromdate[8:10]):
                    xValues.append(weight["time"][0:10])
                    yValues.append(weight["weight"])
        #3.If data year is same as to year
        elif year > int(fromdate[0:4]) and year == int(todate[0:4]):
            #If data's month is less than to date's month
            if month < int(todate[5:7]):
                xValues.append(weight["time"][0:10])
                yValues.append(weight["weight"])
            #If data's month is same as to date's month
            elif month == int(todate[5:7]):
                #Check date
                if day <= int(todate[8:10]):
                    xValues.append(weight["time"][0:10])
                    yValues.append(weight["weight"])
        #4.If data year is the same as from AND to date's years
        elif year == int(fromdate[0:4]) and year == int(todate[0:4]):
            #1.If month falls in between 2 specified months
            if month > int(fromdate[5:7]) and month < int(todate[5:7]):
                xValues.append(weight["time"][0:10])
                yValues.append(weight["weight"])
            #2.If data's month is same as from month
            elif month == int(fromdate[5:7]) and month < int(todate[5:7]):
                #If data's day is more than from date's day
                if day >= int(fromdate[8:10]):
                    xValues.append(weight["time"][0:10])
                    yValues.append(weight["weight"])
            #3.If data month is same as to month
            elif month > int(fromdate[5:7]) and month == int(todate[5:7]):
                #If data's day is less than to date's day
                if day <= int(todate[8:10]):
                    xValues.append(weight["time"][0:10])
                    yValues.append(weight["weight"])
            #4.If from and to month are the same
            elif month == int(fromdate[5:7]) and month == int(todate[5:7]):
                #Check date
                if day >= int(fromdate[8:10]) and day <= int(todate[8:10]):
                    xValues.append(weight["time"][0:10])
                    yValues.append(weight["weight"])

    return render_template("weight.html", weights=weights, xValues=xValues, yValues=yValues, lwl=lwl, uwl=uwl, fromdate=fromdate, todate=todate, latestweights=latestweights, username=username)


#For settings route
@app.route("/settings")
def settings():
    if not session.get("user_id"):
        return redirect("/login")
    username = session.get("username")
    return render_template("settings.html", username=username)

#For change password
@app.route("/changepassword", methods = ["POST"])
def changepassword():
    if not session.get("user_id"):
        return redirect("/login")
    user_id = session["user_id"]
    username = session.get("username")
    oldpassword = request.form.get("oldpassword")
    password = request.form.get("password")
    rpassword = request.form.get("rpassword")
    #Error testing
    if not oldpassword or not password or not rpassword:
        return error("Password field cannot be empty")
    rows = db.execute("SELECT * FROM users WHERE id=?", user_id)
    if password != rpassword:
        return error("New password does not match reconfirmation password")
    if not check_password_hash(rows[0]["hash"], oldpassword):
        return error("Incorrect current password")
    passworddb = generate_password_hash(password)
    db.execute("UPDATE users SET hash=? WHERE id=?;", passworddb, user_id)
    session.clear()
    return redirect("/login")

#For graph modifications
@app.route("/modifygraph", methods = ["POST"])
def modifygraph():
    if not session.get("user_id"):
        return redirect("/login")
    user_id = session["user_id"]
    lwl = request.form.get("lower_weight_limit")
    uwl = request.form.get("upper_weight_limit")
    fromdate = request.form.get("fromdate")
    todate = request.form.get("todate")

    if lwl:
        db.execute("UPDATE settings SET lwl=? WHERE user_id=?;", lwl, user_id)
    if uwl:
        db.execute("UPDATE settings SET uwl=? WHERE user_id=?;", uwl, user_id)
    if fromdate:
        db.execute("UPDATE settings SET fromdate=? WHERE user_id=?;", fromdate, user_id)
    if todate:
        db.execute("UPDATE settings SET todate=? WHERE user_id=?;", todate, user_id)
    return redirect("/weight")

@app.route("/moredata")
def moredata():
    if not session.get("user_id"):
        return redirect("/login")
    user_id = session["user_id"]
    username = session.get("username")
    weights = db.execute("SELECT * FROM weight WHERE user_id=?;", user_id)
    datas = []
    rows = db.execute("SELECT * FROM settings WHERE user_id=?;", user_id)[0]
    tablefromdate = rows["tablefromdate"]
    tabletodate = rows["tabletodate"]
    #Adding only datas starting from the specified date and before a specified date
    for weight in weights:
        year = int(weight["time"][0:4])
        month = int(weight["time"][5:7])
        day = int(weight["time"][8:10])
        #1.If data's year falls inbetween the 2 specified years
        if year > int(tablefromdate[0:4]) and year < int(tabletodate[0:4]):
            datas.append(weight)
        #2.If data year is same as from year
        elif year == int(tablefromdate[0:4]) and year < int(tabletodate[0:4]):
            #If data's month is more than from date's month
            if month > int(tablefromdate[5:7]):
                datas.append(weight)
            #If data's month is same as from date's month
            elif month == int(tablefromdate[5:7]):
                #Check date
                if day >= int(tablefromdate[8:10]):
                    datas.append(weight)
        #3.If data year is same as to year
        elif year > int(tablefromdate[0:4]) and year == int(tabletodate[0:4]):
            #If data's month is less than to date's month
            if month < int(tabletodate[5:7]):
                datas.append(weight)
            #If data's month is same as to date's month
            elif month == int(tabletodate[5:7]):
                #Check date
                if day <= int(tabletodate[8:10]):
                    datas.append(weight)
        #4.If data year is the same as from AND to date's years
        elif year == int(tablefromdate[0:4]) and year == int(tabletodate[0:4]):
            #1.If month falls in between 2 specified months
            if month > int(tablefromdate[5:7]) and month < int(tabletodate[5:7]):
                datas.append(weight)
            #2.If data's month is same as from month
            elif month == int(tablefromdate[5:7]) and month < int(tabletodate[5:7]):
                #If data's day is more than from date's day
                if day >= int(tablefromdate[8:10]):
                    datas.append(weight)
            #3.If data month is same as to month
            elif month > int(tablefromdate[5:7]) and month == int(tabletodate[5:7]):
                #If data's day is less than to date's day
                if day <= int(tabletodate[8:10]):
                    datas.append(weight)
            #4.If from and to month are the same
            elif month == int(tablefromdate[5:7]) and month == int(tabletodate[5:7]):
                #Check date
                if day >= int(tablefromdate[8:10]) and day <= int(tabletodate[8:10]):
                    datas.append(weight)

    return render_template("moredata.html", datas=datas, username=username)

@app.route("/modifytable", methods = ["POST"])
def modifytable():
    if not session.get("user_id"):
        return redirect("/login")
    username = session.get("username")
    user_id = session["user_id"]
    tablefromdate = request.form.get("tablefromdate")
    tabletodate = request.form.get("tabletodate")
    if tablefromdate:
        db.execute("UPDATE settings SET tablefromdate=? WHERE user_id=?;", tablefromdate, user_id)
    if tabletodate:
        db.execute("UPDATE settings SET tabletodate=? WHERE user_id=?;", tabletodate, user_id)
    return redirect("/moredata")