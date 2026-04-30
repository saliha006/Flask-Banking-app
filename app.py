from flask import Flask, request, redirect, url_for, session
import sqlalchemy as sa 
from sqlalchemy.orm import declarative_base, Session 
import random

app = Flask(__name__) 
app.secret_key = 'bankkey'

Base = declarative_base() 
db = sa.create_engine("sqlite:///bank.db")


class User(Base):
    __tablename__ = 'user'
    id = sa.Column(sa.Integer, primary_key = True, autoincrement= True)
    username = sa.Column(sa.String(50), nullable= False)
    password = sa.Column(sa.String(80), nullable= False)
    email = sa.Column(sa.String(80),nullable= False)

class Account(Base):
    __tablename__ = 'account'
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    account_number = sa.Column(sa.Integer, nullable= False, unique= True)
    balance = sa.Column(sa.Float, nullable= False, default= 0.00)
    
class Transaction(Base):
    __tablename__ = 'transaction'
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    account_id = sa.Column(sa.Integer, sa.ForeignKey('account.id'))
    description = sa.Column(sa.String(50), nullable = False)
    amount = sa.Column(sa.Float, nullable = False)
    date = sa.Column(sa.String(30), nullable = False)

class Payee(Base):
    __tablename__ = 'payee'
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    name = sa.Column(sa.String(30), nullable = False)
    bank = sa.Column(sa.String(30), nullable = False)
    account_number = sa.Column(sa.Integer, nullable = False)
    sort_code = sa.Column(sa.String(30), nullable = False)


Base.metadata.create_all(db)

@app.route("/")
def Home():
    return "Welcome to the Bank App"

@app.route("/register", methods = ['GET', 'POST'])
def Register():
    if request.method == 'GET':
        return "Register here"

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        with Session(db) as s:
            new_user = User(username = username, password = password, email = email)
            s.add(new_user)
            s.flush()  # Ensure the new user is added to the session to get the ID

            s.add(Account(user_id = new_user.id, account_number = random.randint(12345678, 87654321), balance = 1000.00))
            s.add(Account(user_id = new_user.id, account_number = random.randint(12345678, 87654321), balance = 500.00))
            s.commit()
            return redirect(url_for("Login"))
        #return render_template("register.html") # For HTML form, not implemented here and others
        

@app.route("/login", methods = ['GET', 'POST'])
def Login():
    if request.method == 'GET':
        return "Login here"

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with Session(db) as s:
            user = s.query(User).filter_by(username = username, password = password).first()

        if user:
           session['username']= user.username
           return redirect(url_for("Accounts"))
        else:
           return "Username not found"
                #return to register should be implemneted here or forgot pass
        

        #implement by order of features commented here.

        #forgot pass button taht redirects to password reset page

        #register button that redirects to register page

        #add button in html taht lets you press next and redirects to accounts


@app.route("/accounts")
def Accounts():

    if 'username' in session:
        username = session['username']
        with Session(db) as s:
            user = s.query(User).filter_by(username = username).first()
            accounts = s.query(Account).filter_by(user_id = user.id).all()

        #loop
        account_info = ""
        for account in accounts:
            account_info += f"{account.account_number} (${account.balance:.2f})"

        return f"Hello, {username}, Your Accounts: {account_info}"
    else:
        return redirect(url_for("Login"))
    
    #implement by order of features commented here.

    #in html add logo on to right corner use creative softwre of my ownto do it

    #make 2 div containers with 2 diff accounts

    #add 3 buttons on bottom home payment and products

@app.route("/payment")
def Payment():
    return "Payment Page"

    #payment button that redirects to payment page no matter where its clicked

@app.route("/account_summary")
def Summary():
    return "Account Summary Page"

#current balance div in html 

#move money button that redirects to select payee page

#has a list f transactions that shows the last 2-3 transactions for each account

#home button that redirects to accounts page

#products button that redirects to products page


@app.route("/select_payee")
def SelectPayee():
    return "Select Payee Page"

#has add payee button that redirects to add new payee page on top right corner

#has a list of payees in html 

#has a enter amount text box inteh belwo list of payees

#has cancel and submit buttons

#cancle redicrects to account summary page

#submit shows conformation message with f string (payee name) with okay btton toclose teh pop up message

#whenneww payee is added it showws a confirmation messae with okay btton toclose teh pop up message


@app.route("/add_new_payee")
def AddNewPayee():
    return "Add New Payee Page"

#form with text boxes for payee name, bank name, account number, sort code and submit button which shows same confirmation 
# pop up as above in select payee class 


@app.route("/products")
def Product():
    return "Products Page"

#products page has a botton taht redirects to accout page when clicked (top right corner)

#3 divs thata re clockable one loans then mortgage then credit card

#clickig on loans will redicrect to loans page 


@app.route("/loans")
def Loans():
    return "Loans Page"

# loans page  also has a botton taht redirects to accout page when clicked (top right corner)

#witha  div with loan image 

#then another abot loan options with text info instead



@app.route("/logout")
def Logout():
    session.clear()
    return redirect(url_for("Login"))


if __name__ == "__main__":
    app.run(port= 8080, debug=True)
    