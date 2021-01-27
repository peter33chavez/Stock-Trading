import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime


from helpers import apology, login_required, lookup, usd

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

    #current user
    user_id = session["user_id"]

    # get the users stock info
    rows = db.execute("SELECT *, SUM(shares) as shares FROM transactions WHERE id=:id GROUP BY symbol HAVING SUM(shares) > 0", id=user_id)
    grand_total = 0
    users = []
    # get users current cash
    c = db.execute("SELECT cash FROM users WHERE id=:id", id=user_id)
    cash = c[0]["cash"]

    # add all needed variables into a dictionary
    for row in rows:
        stock = lookup(row["symbol"])
        cur_price = stock["price"]

        users.append({
            "symbol": row["symbol"],
            "name": stock["name"],
            "shares": row["shares"],
            "cur_price": usd(stock["price"]),
            "total": usd(stock["price"] * row["shares"])
        })

        # get grand total
        grand_total += cur_price * row["shares"]

    # add all you cash and stocks together
    grand_total += cash

    return render_template("index.html", cash=usd(cash), grand_total=usd(grand_total), users=users)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        #error checking
        if not request.form.get("symbol"):
            return apology("Stock needed", 403)

        if not lookup(request.form.get("symbol")):
            return apology("Stock not found", 403)

        if not request.form.get("shares") or not int(request.form.get("shares")) > 0:
            return apology("At least 1 share needed", 403)

        # get stock info
        symbol = request.form.get("symbol")
        price = lookup(symbol)["price"]
        name = lookup(symbol)["name"]

        # amount of shares
        shares = int(request.form.get("shares"))
        buying_amount = price * shares

        # get current user
        users_id = session["user_id"]

        # query db
        rows = db.execute("SELECT * FROM users WHERE id = :users_id", users_id=users_id)
        # get users current cash amount
        cash = rows[0]["cash"]

        # if user doesnt have enough money for the shares
        if not cash >= buying_amount:
            return apology("Sorry insufficient funds for requested shares", 403)
        else:

            #update cash amount in users table
            cash_update = cash - buying_amount
            db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=cash_update, id=users_id)

             # add users stocks into transactions table
            db.execute("INSERT INTO transactions (id, name, symbol, price, shares, buy_sell) VALUES (:id, :name, :symbol, :price, :shares, :buy_sell)",
                        id=users_id, name=name, symbol=symbol, price=price, shares=shares, buy_sell= "Buy")

            # return to the index page w/ message.
            flash("Stock successfully bought!")
            return redirect("/")

    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    #current user
    user_id = session["user_id"]

    # get the users stock info
    rows = db.execute("SELECT * FROM transactions WHERE id=:id", id=user_id)

    return render_template("history.html", rows=rows)


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

    #if user requests for a quote
    if request.method == "POST":

        # look up requested stock
        stock = lookup(request.form.get("symbol"))

        # if not found return apology
        if not bool(stock):
            return apology("Stock not found", 403)

        # else render quoted pg with requested stock quote
        else:
            name = stock["name"]
            symbol = stock["symbol"]
            price = stock["price"]
            return render_template("quoted.html", name=name, symbol=symbol, price=price)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # forget anyone else who tried to create account
    session.clear()

    if request.method == "POST":

        # Ensure username field isnt blank
        if not request.form.get("username"):
            return apology("Username invalid", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Password field is empty", 403)

        #confirm passwords are the same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                        username=request.form.get("username"))

        # check if username already exists
        if len(rows) == 1:
            return apology("Sorry username is already taken", 403)

        #variable for new user
        username = request.form.get("username")
        hash_password = generate_password_hash(request.form.get("password"))

        # add the new user to the database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username,hash=hash_password)

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                        username=username)

        session["user_id"] = rows[0]["id"]

        flash("Registered Successfully!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    #get users stock info
    user_id = session["user_id"]
    stocks = db.execute("SELECT *, SUM(shares) as shares FROM transactions WHERE id=:id GROUP BY symbol HAVING shares > 0", id=user_id)

    if request.method == "POST":

        # --error checking--

        #check for valid inputs during sell.
        if request.form.get("symbol") == "Stock Symbol":
            return apology("Stock needed", 403)

        if not request.form.get("shares") or not int(request.form.get("shares")) > 0:
            return apology("At least 1 share needed", 403)

        # store users sell request.
        selling_symbol = request.form.get("symbol")
        selling_shares = int(request.form.get("shares"))

        # check that you can sell that amount of shares
        if selling_shares > stocks[0]["shares"]:
            return apology("Requested Sell amount is over shares you currently own", 403)

        # -- end of error checking --

        else:
            # -- update tables --

            # get cash_out amount
            curr_price = lookup(selling_symbol)["price"]
            cash_out = curr_price * selling_shares
            selling_shares = (- + selling_shares)
            name = lookup(selling_symbol)["name"]

            # get users current cash amount
            rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=user_id)
            cash = rows[0]["cash"]

            #update cash amount in users table
            cash_update = cash + cash_out
            db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=cash_update, id=user_id)

            # update trasactions table
            db.execute("INSERT INTO transactions (id, name, symbol, price, shares, buy_sell) VALUES (:id, :name, :symbol, :price, :shares, :buy_sell)",
                        id=user_id, name=name, symbol=selling_symbol, price=curr_price, shares=selling_shares, buy_sell = "Sell")
            # return to the index page w/ message.
            flash("Stock successfully sold!")
            return redirect("/")

    else:
        return render_template("sell.html",stocks=stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
