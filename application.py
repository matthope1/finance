import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from credit import credit_validation

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

    #query database to get list of stocks that current user owns
    stock_list = db.execute("SELECT DISTINCT symbol FROM transactions WHERE user_id =  :user_id",
                          user_id = session["user_id"])
    #query users database to get amount of cash that current user has
    cash_query = db.execute("SELECT cash from users where id = :user_id", user_id = session["user_id"])

    cash = round(cash_query[0]["cash"], 2)

    #2d list to store stock data
    stock_info_list = []


    for stock in stock_list:
        stock_symbol = stock['symbol']

        stock_lookup = lookup(stock_symbol)

        stock_name = stock_lookup["name"]
        price_per_share = stock_lookup["price"]

        num_of_shares_query = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = :user_id and symbol = :symbol", user_id = session["user_id"], symbol = stock_symbol)

        num_of_shares_owned = num_of_shares_query[0]['SUM(shares)']
        stock_info_list.append([stock_symbol, stock_name, num_of_shares_owned, price_per_share, round(price_per_share * num_of_shares_owned, 2)])

    #total amount of cash + stock user owns
    account_total = 0
    for stock in stock_info_list:
        account_total = account_total + stock[4]

    account_total = round(account_total + cash, 2)


    return render_template("index.html", stock_info_list = stock_info_list, cash = cash, total = account_total)



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
        if not stock_data:
            return apology("invalid symbol", 400)

        #if number of shares isnt a number or its value is less than 1
        if not (isinstance(number_of_shares, int) and number_of_shares > 0):
            return apology("number of shares must be a valid number greater than 0", 403)


        price_per_share = stock_data["price"]

        amount_to_spend = price_per_share * number_of_shares

        cash_query = db.execute("SELECT cash FROM users WHERE id = :user_id",
              user_id = session["user_id"])

        cash = cash_query[0]["cash"]

        #check if user has enough cash to buy their shares
        if cash < amount_to_spend:
            return apology("insufficient funds in account", 403)

        else:

            cash_left = cash - amount_to_spend
            #update cash on users table to reflect transaction
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = cash_left, user_id = session["user_id"])

            #add new transaction to transactions table
            db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date) VALUES (:user_id, :symbol, :shares, :price, CURRENT_TIMESTAMP )",
            user_id = session["user_id"], symbol = symbol, shares = number_of_shares, price = price_per_share)

            flash("Buy sucessful!")
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")

    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
        # User reached route via GET

    history_query = db.execute("SELECT symbol, shares, price, date FROM transactions WHERE user_id = :user_id", user_id = session["user_id"])

    return render_template("history.html", history = history_query)


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
        username_query = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(username_query) != 1 or not check_password_hash(username_query[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = username_query[0]["id"]

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

            if not symbol:
                return apology("must provide a symbol",403)

            quote = lookup(symbol)
            #if lookup for that symbol returns valid response
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

        #make sure that user input a username
        if not username:
            return apology("must provide a username", 403)


        username_query = db.execute("SELECT username FROM users WHERE username = :username",
                                username=username)


        #check if username already exists
        if len(username_query) == 1:
            return apology("username taken",403)


        #make sure that user input a passowrd
        if not password:
            return apology("must provide a password", 403)

        if not password == request.form.get("confirmation"):
            return apology("passwords must match")


        hashed_pass = generate_password_hash(password)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username = username, password = hashed_pass)


        flash("Registration sucessful!")
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        stock_symbol = request.form.get("symbol")
        sell_quantity = int(request.form.get("shares"))


        if not stock_symbol:
            return apology("missing symbol")

        if not sell_quantity:
            return apology("missing shares")

        if sell_quantity < 0:
            return apology("Number of shares must be greater than 0")

        #query transactions database to calculate how many shares user owns
        num_of_shares_query = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = :user_id and symbol = :symbol", user_id = session["user_id"], symbol = stock_symbol)
        num_of_shares_owned = num_of_shares_query[0]['SUM(shares)']

        if not (num_of_shares_owned > 0 and num_of_shares_owned >= sell_quantity):
            return apology("not enough shares owned")

        stock_lookup = lookup(stock_symbol)

        price_per_share = stock_lookup["price"]

        current_cash = db.execute("SELECT cash FROM users WHERE id = :user_id",
              user_id = session["user_id"])

        cash = current_cash[0]["cash"]

        cash_to_add = cash + price_per_share * sell_quantity

        sell_quantity = sell_quantity * - 1; #change sell quantity to a negative number

        #update logged in users's cash to reflect amount gained from selling shares
        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = cash_to_add, user_id = session["user_id"])

        #add new transaction to transactions table
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date) VALUES(:user_id, :symbol, :shares, :price, CURRENT_TIMESTAMP) ",
                        user_id = session["user_id"], symbol = stock_symbol, shares = sell_quantity, price = price_per_share)


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

        return render_template("sell.html", stock_list = stock_list)


@app.route("/profile")
@login_required
def profile():
    """ Manage user profile """

    username_query = db.execute("SELECT username FROM users WHERE id = :user_id", user_id = session["user_id"])

    username = username_query[0]["username"]

    return render_template("profile.html", user = username)



@app.route("/change-pass", methods=["GET","POST"])
@login_required
def change_pass():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        old_pass = request.form.get("old-password")
        new_pass = request.form.get("new-password")
        confirm_new = request.form.get("confirm-new")


        if not old_pass:
            return apology("Missing old password")

        if not new_pass:
            return apology("missing new-password")

        if not confirm_new:
            return apology("missing password confirmation")


        hash_query = db.execute("SELECT hash FROM users where id = :user_id", user_id = session["user_id"])

        if len(hash_query) != 1 or not check_password_hash(hash_query[0]["hash"], old_pass):
            return apology("Invalid old password", 403)

        if new_pass != confirm_new:
            return apology("passwords must match")

        hashed_pass = generate_password_hash(new_pass)

        db.execute("UPDATE users SET hash = :password WHERE id = :user_id", password = hashed_pass, user_id = session["user_id"])

        flash("Password Changed!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change-pass.html")


@app.route("/add-cash", methods=["GET","POST"])
@login_required
def add_cash():
    # User reached route via POST (as by submitting a form via POST)

    if request.method == "POST":

        amount = int(request.form.get("amount"))

        name = request.form.get("name")
        credit = request.form.get("creditC")
        expiration = request.form.get("expiration")
        ccv = request.form.get("ccv")


        if not amount:
            return apology("missing amount")

        if not name:
            return apology("missing name")

        if not credit:
            return apology("missing credit card number")

        if not expiration:
            return apology("missing expiration date")

        if not ccv:
            return apology("missing ccv")


        card_valid = credit_validation(credit)

        if not card_valid:
            return apology("Invalid credit card information")

        cash_query = db.execute("SELECT cash from users where id = :user_id", user_id = session["user_id"])
        cash = cash_query[0]['cash']

        cash = cash + amount

        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = cash, user_id = session["user_id"])

        flash("Added Cash!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("add-cash.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
