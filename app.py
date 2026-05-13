from flask import Flask, request, redirect, url_for, session, render_template
import sqlalchemy as sa 
from sqlalchemy.orm import declarative_base, Session 
import random
import datetime

#flask app setup
app = Flask(__name__) 
app.secret_key = 'bankkey'

#database setup
Base = declarative_base() 
db = sa.create_engine("sqlite:///bank.db")

#different database classes with their relevant attributes
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

#creaing database instances
Base.metadata.create_all(db)

@app.route("/")
def home():
    return render_template('login.html')


@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with Session(db) as s:
            user = s.query(User).filter_by(username = username, password = password).first()

        if user:
           session['username']= user.username
           return redirect(url_for("accounts"))
        else:
           return "Username not found"
                #return to register should be implemneted here or forgot pass
        


@app.route("/reset", methods = ['GET','POST'])
def reset():
    #loads page using GET
    if request.method == 'GET':
        return render_template('reset.html')
    
    if request.method == 'POST':
        #reads username, new pass and confirmation form HTML form.
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        #compares the new pass to repeated pass to ensure correctness.
        if new_password == confirm_password:
            with Session(db) as s:
                #queries User table by username and updates its password.
                user_query = s.query(User).filter_by(username = username).first()
                user_query.password = new_password
                s.commit()
        else:
            return "Passwords do not match"

    return redirect(url_for('login'))



@app.route("/accounts")
def accounts():

    if 'username' in session:
        username = session['username']
        with Session(db) as s:
            user = s.query(User).filter_by(username = username).first()
            accounts = s.query(Account).filter_by(user_id = user.id).all()
        
        for account in accounts:
            acc_str = str(account.account_number) 
            account.formatted_number = f"{acc_str[:4]} {acc_str[4:]}"

        return render_template('accounts.html', accounts=accounts, username=username)
    else:
        return redirect(url_for("login"))
    


#imports account_id in the route
@app.route("/account/<int:account_id>")
def account(account_id):
    #checks if username is in session (aka logged in).
    if 'username' in session: 
        #reads username from session.
        username = session['username'] 

        #opens database connection.
        with Session(db) as s: 

            #queries to find transactions by account.
            account = s.query(Account).filter_by(id = account_id).first()
            user_transactions = s.query(Transaction).filter_by(account_id = account.id).all()

            return render_template('accounts_summary.html', account=account, transactions=user_transactions, username=username)
    else:
        #if user isnt logged in we redirect to login route.
        return redirect(url_for("login"))
    


#uses GET and POST methods to send and recieve data form forms.
@app.route("/payments", methods = ['GET','POST'])
def payments():
    #checks if user is logged in.
    if 'username' in session:
        username = session['username']

        with Session(db) as s:
            user = s.query(User).filter_by(username=username).first()
            payees = s.query(Payee).filter_by(user_id=user.id).all()
            accounts = s.query(Account).filter_by(user_id=user.id).all()
        
        #displays the return string when this webpage is visited.
        if request.method == 'GET':
            return render_template('payments.html', payees=payees, accounts=accounts)

        #using POST to send payee_id and amount info to the databse.
        if request.method == 'POST':
            payee_id = request.form.get('payee_id')
            amount = request.form.get('amount')

            #thsi opens database connection.
            with Session(db) as s:
                #querying payee_id, username and user_id to find account info in order to process payment
                payee = s.query(Payee).filter_by(id = payee_id).first()
                user = s.query(User).filter_by(username = username).first()
                account = s.query(Account).filter_by(user_id = user.id).first()
                
                #checking if theres enough balance to process payment
                if float(account.balance) > float(amount):
                    account.balance = account.balance - float(amount)

                    s.add(Transaction(
                        account_id=account.id,
                        description=f"Payment to {payee.name}",
                        amount=-float(amount),
                        date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                     ))
                    s.commit() 

                    #storing the info via a dictionary
                    session['payment_info'] = {
                        'payee_name':payee.name,
                        'amount':amount,
                        'remaining_balance': account.balance}
                    
                    #returning successful payment confirmation message 
                    return redirect(url_for("payment_success"))
                else:
                    return "Insufficeint funds"
    else:
        #if user is not logged in, hes redirected to login page        
        return redirect(url_for("login"))



@app.route("/payment_success")
def payment_success():
    #retrieves information from dictionary in the payments route to display confirmation message. 
    payment_info = session.get('payment_info')
    return render_template('payments_success.html', payment_info=payment_info)
    


@app.route("/add_payee", methods = ['GET','POST'])
def add_payee():
    #loads the new payee page
    if request.method == 'GET':
        return render_template('add_payee.html')
    
    #reads the payee info form the form.
    if request.method == 'POST':
        name = request.form.get('name')
        account_number = request.form.get('account_number')
        bank = request.form.get('bank')
        sort_code = request.form.get('sort_code')

        #opens db connection in order to save new payee.
        with Session(db) as s:
            username = session['username']
            user = s.query(User).filter_by(username =  username).first()
            #adds new payee to the database.
            new_payee = Payee(user_id = user.id, name = name, account_number = account_number, bank = bank, sort_code = sort_code)
            s.add(new_payee)
            s.commit()

            return redirect(url_for('payee_added'))
        
    else:
        return "Payee Couldn't be added"
    

@app.route("/payee_added")
def payee_added():
    return render_template('payee_added.html')



@app.route("/products")
def products():
    #creating a product dictonary where data can be stored
    products_dict = [
        {'name':'loans', 'description':'Flexible loan options from 2.7% APR'},
        {'name':'mortgages', 'description':'Current mortgages offer £40k-150k with 15 yeras packback period'},
        {'name':'credit_cards', 'description':'Currently offering credit cards with 6% interest rate for 1 year, then back to 3.5%, £750 credit limit, offer valid for 2 months'}
    ]

    #converts each product nam einto a display friendly label
    for product in products_dict:
        product['display_name'] = product['name'].replace('_',' ').title()

    return render_template('products.html', products=products_dict)



@app.route("/loans")
def loans():
    #creates a loan/loan options dictionary
    loans_dict = [
        {'name':'Loan', 'description':'Flexible loans can be found below starting from 2.7% APR'},
        {'name':'Loan Options', 'description':'starter £0-10k from 2.7% APR | inter £10-35k from 4.7% APR | advanced £35-60k from 7.4% APR'
         }
    ]


    for loan in loans_dict:
        if '|' in loan['description']:
            loan['tiers'] = [tier.strip() for tier in loan['description'].split('|')]
    return render_template('loans.html', loans=loans_dict)



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(port= 8080, debug=True)
    