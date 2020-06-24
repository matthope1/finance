import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

from datetime import datetime


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # to get list of all the stocks a particular user has
    # we can select distinct symbol from transactions where userid = current user
    #then we can add up all the amounts of shares +/- and then
    # multipy by current stock price using lookup
    # to find the total amount for any given stock

    #to send this data to the index page
    #we can create a 2d array to store symbol name shares price total
    #for each of the stocks that the current user owns
    #then we can display a a tr with 5 tds on the index page with afformententioned info


    stock_list = db.execute("SELECT DISTINCT symbol FROM transactions WHERE user_id =  :user_id",
                          user_id = session["user_id"])

    cash_query = db.execute("SELECT cash from users where id = :user_id", user_id = session["user_id"])

    cash = round(cash_query[0]["cash"], 2)

    #2d list to store stock data
    stock_info_list = [] #symbol Name Shares Price TOTAL


    for item in stock_list:
        stock_symbol = item['symbol']

        stock_lookup = lookup(stock_symbol)

        stock_name = stock_lookup["name"]
        stock_price = stock_lookup["price"]

        num_of_shares_query = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = :user_id and symbol = :symbol", user_id = session["user_id"], symbol = stock_symbol)

        num_of_shares_owned = num_of_shares_query[0]['SUM(shares)']
        # print(item)
        stock_info_list.append([stock_symbol, stock_name, num_of_shares_owned, stock_price, stock_price * num_of_shares_owned ])



    total = 0
    for item in stock_info_list:
        total = total + item[4]
        # print(item)

    total = round(total + cash, 2)




    return render_template("index.html", stock_info_list = stock_info_list, cash = cash, total = total)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

            symbol = request.form.get("symbol")
            number_of_shares = int(request.form.get("shares"))

            #if the user left the symbol blank on the form
            if not symbol:
                return apology("must provide a symbol", 403)

            # the user left the number of shares blank
            if not number_of_shares:
                return apology("must provide number of shares",403)

            stock_data = lookup(symbol)

            # if lookup returns with valid data
            if stock_data:

                if isinstance(number_of_shares, int) and number_of_shares > 0:
                    price_per_share = stock_data["price"]

                    amount_to_spend = price_per_share * number_of_shares

                    rows = db.execute("SELECT cash FROM users WHERE id = :user_id",
                          user_id = session["user_id"])

                    cash = rows[0]["cash"]
                    current_date_time = datetime.now()
                    dt_string = current_date_time.strftime("%d/%m/%Y %H:%M:%S")


                    #check if user has enough cash to buy their shares, render apology if they dont

                    if cash < amount_to_spend:
                        return apology("insufficient funds in account", 403)

                    else:

                        #were going to need to update the user table
                        #the current users cash needs to be subtracted with "UPDATE"
                        #update the table by setting current users cash to cash left

                        cash_left = cash - amount_to_spend



                        # print("The data to be inserted into transactions table")
                        # print("the user:", session["user_id"], "Has this:", cash, " and will have", cash_left, " After the transaction")
                        # print("(symbol, shares, price, date)")
                        # print("symbol:", symbol, " shares:", number_of_shares, "price: ", price_per_share, " datetime", current_date_time)
                        # print(dt_string)

                        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = cash_left, user_id = session["user_id"])

                        #add new transaction to transactions table
                        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date) VALUES (:user_id, :symbol, :shares, :price, CURRENT_TIMESTAMP )",
                        user_id = session["user_id"], symbol = symbol, shares = number_of_shares, price = price_per_share)

                        flash("Buy sucessful!")
                        return render_template("index.html")


                    #add one or more new tables to keep track of purchases

                else:
                    return apology("number of shares must be a valid number greater than 0", 403)

            else:
                return apology("invalid symbol", 400)


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")

    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
            symbol = request.form.get("symbol")
            # print("this happens...1")

            if not symbol:
                return apology("must provide a symbol",403)

            quote = lookup(symbol)

            if quote:
                name = quote["name"]
                price = quote["price"]
                symbol = quote["symbol"]

                return render_template("quoted.html",name = name, price = price, symbol = symbol)

            else:
                return apology("invalid symbol", 400)


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        #print("Username: ", username)
        #print("Password: ", password)

        #ensure that user input a username
        if not username:
            return apology("must provide a username", 403)


        rows = db.execute("SELECT username FROM users WHERE username = :username",
                                username=username)


        #check if username already exists
        if len(rows) == 1:
            return apology("username taken",403)


        #ensure that user input a passowrd
        if not password:
            return apology("must provide a password", 403)

        if not password == request.form.get("confirmation"):
            return apology("passwords must match")


        hashed_pass = generate_password_hash(password)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username = username, password = hashed_pass)

        flash("Registration sucessful!", "info")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("register.html")



    #return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        quantity = request.form.get("shares")

        #TODO
        #render apology if user failes to select stock or if user does not own any shares
        #if quantity is not a positive int render apology
        #if user does not own that many shares of said stock return apology


        print(symbol)
        print(quantity)

        flash("Sold!")
        return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # we need to query the finance table to get stock list for current user
        stock_list_query = db.execute("SELECT DISTINCT symbol FROM transactions WHERE user_id =  :user_id",
                          user_id = session["user_id"])
        stock_list = []

        for item in stock_list_query:
            stock_list.append(item['symbol'])

        print(stock_list)

        return render_template("sell.html", stock_list = stock_list)




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)