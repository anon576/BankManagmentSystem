import ast
from email.mime.application import MIMEApplication
import pytz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from datetime import datetime
from flask import Flask, flash, jsonify,redirect,render_template, send_file,session,request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import hashlib
import qrcode
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText


app = Flask(__name__)
app.secret_key = "sskey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BankSystem.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True,nullable = False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    acno = db.Column(db.String, unique=False)
    pancard = db.Column(db.String, unique= False)
    adharcard = db.Column(db.String, unique=False)
    adress = db.Column(db.String, unique=False)
    actype= db.Column(db.String, unique=False)
    email = db.Column(db.String)
    phoneno = db.Column(db.String, unique=False,nullable = True)
    dob = db.Column(db.String, default=datetime.utcnow)
    Balance = db.Column(db.Integer, unique=False,nullable = True)
    branch = db.Column(db.String, unique=False,nullable = True)

    manager = db.Column(db.String, unique=False,nullable = True)
    # Define the one-to-many relationship with Post
    subadmin = db.relationship('SubAdmin', backref='author', lazy=True)

    coordinator = db.relationship('Coordinator', backref='author', lazy=True)

    campus = db.relationship('Branch', backref='author', lazy=True)

    ArchivedCampus = db.relationship('TransactionDetails', backref='author', lazy=True)

class SubAdmin(db.Model):
    sno = db.Column(db.Integer, primary_key=True,nullable = True)
    name = db.Column(db.String)
    loginid =db.Column(db.String, unique=True)
    password = db.Column(db.String, unique=False)
    branch = db.Column(db.String,unique=False,nullable=True)
    date = db.Column(db.String,unique=False,nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)



class Coordinator(db.Model):
    sno = db.Column(db.Integer, primary_key=True,nullable = True)
    name = db.Column(db.String)
    loginid =db.Column(db.String, unique=True)
    password = db.Column(db.String, unique=False)
    campus = db.Column(db.String,unique=False,nullable = True)
    date = db.Column(db.String,unique=False,nullable = True)

    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)

class Branch(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    ifsc = db.Column(db.String, nullable=True)
    noofemployee = db.Column(db.String, nullable=True)
    date = db.Column(db.String, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
 
class TransactionDetails(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    acno = db.Column(db.String, nullable=True)
    history = db.Column(db.String, nullable=True)
    date = db.Column(db.String, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
 


@app.route("/")
def home():
    user = session.get('user')
    if user and user == 'admin':
        dept = []
        ca = Branch.query.all()
        

        zp = zip(ca,dept)
        return render_template("index.html",zp=zp,campus = ca)
    
    return  redirect("/login")


@app.route("/subadmin",methods = ['GET','POST'])
def subadmin():
    user = session.get('user')
    if user and user == 'admin':

        if request.method == 'POST':
            role = request.form['role']
            name = request.form['name']
            id = request.form['id']
            password = request.form['password']

            if role == 'subadmin':
                sadmin = SubAdmin(name = name,loginid = id,password = password)
            else:
                sadmin = Coordinator(name = name,loginid = id,password = password)

            db.session.add(sadmin)
            db.session.commit()

            return redirect("/subadmin")
        return render_template("subadmin.html")
    return  redirect("/login")


@app.route("/createCampus", methods=['GET', 'POST'])
def camp():
    sa = SubAdmin.query.all()
    co = Coordinator.query.all()
    ba = Branch.query.all()
    user = session.get('user')
    id = SubAdmin.query.filter(SubAdmin.loginid == user).first()
    if user and (user == 'admin' or user == id.loginid):

        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            pancard = request.form['pancard']
            adharcard = request.form['adharcard']
            actype = request.form['type']
            adress = request.form['adress']
            dat = request.form['date']
            deposit = request.form['depo']
            mno = request.form['mno']
            ac = f"{mno[0:5]}{adharcard[0:5]}"
            # manager = request.form['admin_id']
            branch = request.form['campus']
            hash_value = hashlib.sha256(f"{name}{ac}{branch}".encode()).hexdigest()
            id = Branch.query.filter(Branch.name== branch).first()

            admitcardpath=createADmit(ac,name,pancard,email,dat,branch,id.ifsc,adress,actype,hash_value)
            send_email(email,admitcardpath)
            l = []
            l = str(l)
            add = TransactionDetails(name = name,acno = ac,history = l)
            ca = Customer(name = name,pancard=pancard,adharcard=adharcard,adress=adress,email=email, phoneno = mno,Balance = deposit ,acno = ac,branch = branch)
            db.session.add(add)
            db.session.add(ca)
            db.session.commit()
            # db.session.add(ad)
            # db.session.commit()
            # updateCampus(campus)
            return redirect("/createCampus")

        
        s = []
        c = []
        for a in sa:
            s.append(a.loginid)
            
            # Check if a file was uploaded
        for b in co:
            c.append(b.loginid)

        return render_template("campus.html",campus = ba,subadmin = str(s),coordinator = str(c) )
    
    
    return  redirect("/login")


@app.route("/addCampus",methods = ['GET','POST'])
def addcamp():
    user = session.get('user')
    if user and user == 'admin':

        if request.method == "POST":
            name = request.form['name']
            date = request.form['date']
            ifsc= request.form['pack']
            e = request.form['no']
          
            c = Branch(name = name,date = date,ifsc = ifsc,noofemployee=e)
            db.session.add(c)
            db.session.commit()
            return redirect("/addCampus")

        return render_template("addcampus.html")
    return  redirect("/login")

def send_email(receiver_email,pdf_path):
    subject = f"Pass book0  for Stream Bank"
    body = f"Dear"

    message = MIMEMultipart()
    message["From"] = "21070442@ycce.in"  # Replace with your email address
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Attach the PDF file to the email
    with open(pdf_path, "rb") as pdf_file:
        pdf_attachment = MIMEApplication(pdf_file.read(), name=os.path.basename(pdf_path))
        message.attach(pdf_attachment)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    try:
        # Connect to the SMTP server with TLS
        
        server.starttls()

        # Log in to the SMTP server with your email credentials
        server.login("21070442@ycce.in", "eaewfhklfijlhfuj")  # Replace with your email and password

        # Send the email
        server.sendmail("", receiver_email, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection to the SMTP server
        server.quit()



@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/login")

@app.route("/login",methods= ['GET','POST'])
def login():
    if request.method == "POST":
        admin = request.form['admin']
        password = request.form['password']

        if admin == "admin" and password == "password":
            session['user'] = admin
            return redirect("/")
        else:
            id = SubAdmin.query.filter(SubAdmin.loginid == admin).first()
            if id == None:
                return redirect("/login")
            elif id.loginid == admin and id.password == password:
                session["user"] = admin
                return redirect("/createCampus")
        
    return render_template("login.html")


def createADmit(ac,name,pancard,email,dob,branchname,ifsc,adress,actype,hashvalue):
    pdf_file = f"admitcards/{ac}.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    # Set font sizes
    title_font_size = 20
    info_font_size = 15

    # Set starting positions
    x = 50
    y = 740  # Start from the top of the page


    left_x = 20 # Adjust as needed
    right_x = letter[0] - 20  # Adjust as needed
    top_y = letter[1] - 20 # Adjust as needed
    bottom_y = 20  # Adjust as needed

    c.line(left_x, top_y, right_x, top_y)
    c.line(left_x, bottom_y, right_x, bottom_y)
    c.line(left_x, top_y, left_x, bottom_y)
    c.line(right_x, top_y, right_x, bottom_y) 
    fields = [
        ('Stream Banking, Nagpur PVT LTV MSME', ''),
        ('Account No', ac),
        ('Account Type', actype),
        ('Full Name', name),
        ('Pancard', pancard),
        ('Email', email),
        ('Date of Birth ', dob),
        ('Branch', branchname),
        ('IFSC ',ifsc),
        ('Adress ', adress),
    ]
   
    # Iterate through fields and add them to the PDF
    for field_name, field_value in fields:
        if field_name == 'Stream Banking, Nagpur PVT LTV MSME':
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.black)
            c.drawString(200, y, "By Codestream Foundation")
            y-=19
            font_size = title_font_size
            font_color = colors.blue
            c.setFont("Helvetica", font_size)
            c.setFillColor(font_color)
            c.drawString(x+50, y, f'{field_name}')
            y -= 16
            c.setFont("Helvetica-Oblique", 13)
            c.setFillColor(colors.red)
            c.drawString(x, y, "(An Autonomous Bank Institution affiliated to Reserved Bank of India)")
            y-=16
            c.setFont("Helvetica", 13)
            c.setFillColor(colors.brown)
            c.drawString(200, y, "(National Level Bank)")
            y-=19
             # Adjust position below the last field
            #  c.line(left_x, top_y, right_x, top_y)
            c.line(left_x, y+10, right_x, y+10)
            y-=30
            c.setFont("Helvetica-Bold", font_size)
            c.setFillColor(colors.blue)
            c.drawString(x, y, f'Passbook')
            y -= 40 


        else:
            font_size = info_font_size
            font_color = colors.black 
            c.setFont("Helvetica", font_size)
            c.setFillColor(font_color)
            c.drawString(x, y, f'{field_name}  :       {field_value}')
            y -= 30  
        
        # Adjust the vertical position for the next field
    c.setFont("Helvetica-Bold", font_size)
    c.setFillColor(colors.blue)
    c.drawString(x, y, "General Guidelines:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, ''' You must have an active bank account with the respective bank. You may need to visit the bank branch to open an account if you don't already have one.'''
)
    y-=15
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''1.The passbook will be used to record your transactions. You may need to update it regularly by visiting the bank or using online banking services to track your account activity.)'''
)
    y-=15
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''2.  Keep your passbook safe and up to date. You'll need to present it for updating whenever you make a deposit or withdrawal at the bank.'''
)
    y-=15
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''3.Candidate found indulging in any malpractice/ falsified information during our process'''
)
    y-=20

    c.setFont("Helvetica-Bold", font_size-5)
    c.setFillColor(colors.gray)
    c.drawString(x, y, "Specifically for communication assessment::")
    y-=20
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''1.Be aware of the bank's policies and procedures regarding passbooks, including any charges for lost passbooks or updating the passbook '''
)
    y-=15
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''jack – 3.5mm having microphone'''
)
    y-=15

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''2.Some banks may require additional identification documents, especially if you're a new customer.'''
)
    y-=20

    c.setFont("Helvetica-Bold", font_size-5)
    c.setFillColor(colors.gray)
    c.drawString(x, y, "About Gadgets:")
    y-=20

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''1. The Online Test of Avaali Solutions Pvt Ltd. is scheduled as per details given the attached list. Students will report'''
)
    y-=15

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''for the Online Test as per the date, time & venue mentioned. No deviation is permitted.'''
)
    y-=15

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''2. Students to report at the allotted Lab 30 mins prior to Test Time.'''
)
    y-=15

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''3. Students will be in College Uniform.'''
)
    y-=15

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''4. Carry OWN LAPTOP with resume saved on Desktop. Carry College ID Card Aadhar Card.'''
)
    y-=15

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, '''5. No Electronic Gadgets allowed during the Online Test'''
)
    y-=15

    # Generate QR code
    qr_data = hashvalue
    qr = qrcode.make(qr_data)
    qr.save('qrcode.png')

    # Draw the QR code onto the PDF
    c.drawImage('qrcode.png', x + 375, 455, width=150, height=150)
    c.setFont("Helvetica", 15)
    c.setFillColor(colors.black)
    c.drawString(x+400, 450, f'{branchname}')

    # Save the PDF document
    c.save()
    # Create a PDF document
    print('Your ID Card has been successfully created as "ID_Card.pdf"')

    return pdf_file

@app.route("/deposit", methods=['GET', 'POST'])
def deposit():
    user = session.get('user')
    if user:
        if request.method == 'POST':
            acno = request.form['acno']
            amount = float(request.form['amount'])
            
            # Fetch the customer's account using acno
            customer = Customer.query.filter(Customer.acno == acno).first()
            if customer:
                # Update the balance with the deposited amount
                customer.Balance += amount
                db.session.commit()
                return "Amount deposited successfully."
            else:
                return "Account not found."
        
        return render_template("deposit.html")
    return redirect("/login")

@app.route("/transfer", methods=['GET', 'POST'])
def transfer():
    user = session.get('user')
    if user:
        if request.method == 'POST':
            from_acno = request.form['from_acno']
            to_acno = request.form['to_acno']
            amount = float(request.form['amount']) 
            

             # Convert amount to float
            
            # Fetch the sender and receiver's accounts using acno
            sender = Customer.query.filter(Customer.acno == from_acno).first()
            receiver = Customer.query.filter(Customer.acno == to_acno).first()
            
            if sender and receiver:
                if float(sender.Balance) >= amount:
                    sender.Balance -= amount
                    receiver.Balance += amount
                    db.session.commit()
                    sender = TransactionDetails.query.filter(TransactionDetails.acno == from_acno).first()
                    receiver = TransactionDetails.query.filter(TransactionDetails.acno == to_acno).first()
                    if sender:
                        transataion = {
                            "Sender":from_acno,
                            "Receiver":to_acno,
                            "Amount":amount
                        }
                        t = str(transataion)
                        a = sender.history
                        a = list(a)
                        a.append(t)

                    if receiver:
                        transataion = {
                            "Sender":from_acno,
                            "Receiver":to_acno,
                            "Amount":amount
                        }
                        t = str(transataion)
                        a = sender.history
                        a = list(a)
                        a.append(t)
                    db.session.commit()
                    return "Money transferred successfully."
                else:
                    return "Insufficient balance in the sender's account."
            else:
                return "Account not found."
            
        return render_template("transfer.html")
    return redirect("/login")





@app.route("/customer/<acno>")
def get_customer(acno):
    user = session.get('user')
    if user:
        customer = Customer.query.filter(Customer.acno == acno).first()
        if customer:
            # Render a template to display customer data
            return render_template("customer.html", customer=customer)
        else:
            return "Customer not found."
    return redirect("/login")



@app.route("/t/<string:acno>")
def transaction_history(acno):
    user = session.get('user')
    if user:
        customer = Customer.query.filter(Customer.acno == acno).first()
        if customer:
            a = TransactionDetails.query.filter(Customer.acno == acno).first()
            t = a.history
            t = list(t)

            # Render a template to display transaction history
            return render_template("transaction_history.html", customer=customer,t = t )
        else:
            return "Customer not found."
    return redirect("/login")

@app.route("/veiwStats/<string:cam>")
def viewStats(cam):
    user = session.get('user')
    if user and user == 'admin':
        a = Customer.query.filter(Customer.branch == cam).all()
        print(a)
        
        # print(departments)
        return render_template("stats.html",a = a)
    
    return  redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)  # Run the app in debug mode for detailed error messages
