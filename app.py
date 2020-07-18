import itsdangerous
from flask import Flask, render_template, json, request, redirect, url_for, flash,session,abort, jsonify
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
import cv2
from matplotlib import pyplot as plt
from flask_avatars import Avatars

from werkzeug.utils import secure_filename
UPLOAD_FOLDER = '../ESignature-Management-System/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg','svg', 'jfif'}

import smtplib
import os
from passlib.hash import sha256_crypt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
fromaddr = "youremailid@gmail.com"
msg = MIMEMultipart()

app = Flask(__name__, static_url_path='/static')
avatars = Avatars(app)



app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'username'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'calpers_users'
app.secret_key='hello'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024*1024
ts = itsdangerous.URLSafeTimedSerializer(app.config["SECRET_KEY"])
mysql = MySQL(app)

Bootstrap(app)


@app.route('/',methods=['GET','POST'])
def login():
    if request.method == "POST":
        return render_template('index.html',message="User created successfully")
    return render_template('index.html')


@app.route('/homepage')
def home():
    return render_template('home_page.html') 


@app.route('/profilepage',methods=['GET','POST'])
def profile():
    cursor1 = mysql.connection.cursor()
    username = session['user']
    email = session['email']
    image = cursor1.execute("select Name,Imagepath,Preferredname,defaultsign from Image_path where username=%s", [username])
    images = cursor1.fetchall()
    cursor1.execute("select Firstname,Lastname,Orgname from user_details where Username=%s", [username])
    details = cursor1.fetchall()
    if image is not 0:

        names = images[0][0].split(",")
        imagepath = images[0][1].split(",")
        preferredname = images[0][2]
        defaultsign = images[0][3]
        firstname = details[0][0]
        lastname = details[0][1]
        orgname = details[0][2]
        session['names'] = names
        session['imagepath'] = imagepath
        session['firstname'] = firstname
        session['lastname'] = lastname
        session['orgname'] = orgname
        session['defaultsign'] = defaultsign

        print(names)
        print(imagepath)
        return render_template('profile_page.html',name=names,email=email,imagepath=imagepath,prename=preferredname)
    else:
        return render_template('profile_page.html', name=' ', email=email,imagepath=' ', prename=' ')


@app.route('/editprofile',methods=['GET','POST'])
def editprofile():

    cursor1 = mysql.connection.cursor()
    email=request.form['ta1']
    firstname=request.form['fta1']
    lastname = request.form['lta1']
    orgname=request.form['ota1']
    username=session['user']
    currentemail=session['email']

    if request.method == 'POST':

        cursor1.execute("update calpers_users.user_details set Firstname = %s, Lastname = %s, Orgname = %s where user_details.Username = %s",[firstname,lastname,orgname,username])
        mysql.connection.autocommit(True)

        cursor1.execute("update calpers_users.user_details set Email_id = %s where user_details.Email_id = %s",[email,currentemail])
        mysql.connection.autocommit(True)

        cursor1.execute("select Email_id,Firstname,Lastname,Orgname from calpers_users.user_details where user_details.Username = %s",[username])
        result=cursor1.fetchall()

        email=result[0][0]
        firstname=result[0][1]
        lastname=result[0][2]
        orgname=result[0][3]
        defaultsign=request.form.getlist('radio')

        cursor1.execute("update calpers_users.Image_path set defaultsign = %s where username = %s",[defaultsign,username])
        mysql.connection.autocommit(True)

        cursor1.execute("select defaultsign from calpers_users.Image_path where username = %s",[username])
        defaultsign1=cursor1.fetchone()[0]

        session['firstname'] = firstname
        session['lastname'] = lastname
        session['orgname'] = orgname
        session['email']=email

        session['defaultsign']=defaultsign1
        return redirect(url_for("profile"))


@app.route('/reset-password')
def resetpassword():
    return render_template('reset_password.html')


@app.route('/index',methods=['GET','POST'])
def showlogin():

    cursor2= mysql.connection.cursor()
    try:
        if request.method=="POST":
            session.pop('user',None)

        username = request.form['inputUsername1']
        password= request.form['inputPassword1']


        if username and password:

            exists=cursor2.execute("select Pwd,Email_id from user_details where user_details.Username=%s ",[username])

            userdetail=cursor2.fetchall()
            if exists != 0:
                match=sha256_crypt.verify(password,userdetail[0][0])

            else:
                match=0

            if match:
                session['loggedin']= True
                session['user']=username
                session['email']=userdetail[0][1]
               
                if 'user' in session:
                    pass

                return render_template('home_page.html')

            else:
                flash('USERNAME OR PASSWORD INCORRECT')
                return render_template('index.html',message='failure')


        else:
            return json.dumps({'html':'<span>Enter the required fields</span>'})


    except Exception as e:
        return json.dumps({'error':str(e)})
    finally:
        cursor2.close()

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('user', None)
    session.pop('loggedin', None)
    session.pop('firstname', None)
    session.pop('lastname', None)
    session.pop('orgname', None)
    session.pop('defaultsign', None)
    session.pop('filename',None)
    session.pop('file_path',None)
   # Redirect to login page
    return redirect(url_for('login'))


@app.route('/signup')
def signup():
    dropdown=['What was the first name of your first pet?','Where was your mother born','What was your first car','What was your school\'s name?','Where were you born?']
    return render_template('signup.html',dropdown=dropdown)


@app.route('/showsignup', methods=['GET','POST'])
def showsignup():
    cursor1 = mysql.connection.cursor()
    try:

        _username = request.form['inputUsername']
        _pwd = request.form['inputPassword']
        _email = request.form['inputEmail']
        _que1 = request.form['dropdown']
        _ans1 = request.form['dropdown-answer']
        password1 = sha256_crypt.hash(_pwd)

        cursor1.execute("select 1 from user_details where user_details.Username=%s",[_username])
        data=cursor1.fetchall()

        cursor1.execute("select 1 from user_details where user_details.Email_id=%s", [_email])
        emaildata=cursor1.fetchall()


        if _username and _pwd and _email and _que1 and _ans1:

            if len(data) is 0 and len(emaildata) is 0:

                cursor1.execute("insert into user_details(Username,Pwd,Email_id,SecQue1,Ans1) values (%s,%s,%s,%s,%s)",[_username,password1,_email,_que1,_ans1])

                mysql.connection.commit()
                flash(u'Account created', 'success')
                return redirect(url_for("login"))

            else:
                flash(u'ACCOUNT ALREADY EXISTS. TRY LOGGIN IN', 'failure')

                return redirect(url_for("signup"))

        else:
            return json.dumps({'html':'<span>Enter the required fields</span>'})
    except Exception as e:
        return json.dumps({'error':str(e)})
    finally:
        cursor1.close()


@app.route('/confirm/<token>', methods=["GET", "POST"])
def confirm_email(token):
    cursor3 = mysql.connection.cursor()
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except:
        abort(404)
    user=cursor3.execute("select * from user_details where user_details.Email_id=%s ", [email])
    if user is not 0:

        session['sessionemail']=email
        return render_template('reset_password.html')

    else:
        abort(404)


@app.route('/passwordreset',methods=["GET", "POST"])
def passwordreset():
    cursor5 = mysql.connection.cursor()
    if 'sessionemail' in session:
        email=session['sessionemail']
        pwd2 = request.form['inputPassword1']
        password22 = sha256_crypt.hash(pwd2)

        sql="update calpers_users.user_details set Pwd = (%s) where user_details.Email_id = (%s)"
        cursor5.execute(sql,(password22, email))
        mysql.connection.autocommit(True)
        flash("Password changed")

        user2=cursor5.fetchall()

        cursor5.close()
        session.pop('sessionemail', None)
        return redirect(url_for("login"))
    else:
        abort(404)


@app.route('/forgotpwd')
def forgotpwd():
    dropdown=['What was the first name of your first pet?','Where was your mother born','What was your first car','What was your school\'s name?','Where were you born?']
    return render_template('forgot_password.html',dropdown=dropdown)
    

@app.route('/forgotpassword',methods=["GET", "POST"])
def forgotpassword():
    cursor4 = mysql.connection.cursor()
    _email = request.form['inputEmail1']
    _que1 = request.form['dropdown']
    _ans1 = request.form['dropdown1']
    if _email and _que1 and _ans1:
        exists=cursor4.execute("select Username from user_details where user_details.Email_id=%s and user_details.SecQue1=%s and user_details.Ans1=%s", [_email,_que1,_ans1])
        user=cursor4.fetchall()
        if exists is 0:
            flash(u'Details are incorrect', 'failure')
            return redirect(url_for("forgotpwd"))

    
    if user is not 0:
        toaddr = _email
        token = ts.dumps(_email, salt='email-confirm-key')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg['Subject'] = "Reset password link"
        body = "Hi "  + user[0][0] + " This is link for resetting the pwd        " + confirm_url
        msg.attach(MIMEText(body, 'plain'))
        email = smtplib.SMTP('smtp.gmail.com', 587)
        email.starttls()
        email.login(fromaddr, "email_id_password")
        message = msg.as_string()
        email.sendmail(fromaddr, toaddr, message)
        email.quit()
        flash(u'Details verified. An email had been sent to you to reset the password','success')
        return render_template('index.html', message="User created successfully")
    else:
        abort(404)


@app.route('/signupload')
def upload_signature_here():
    if 'user' in session:

        return render_template('signature_upload.html')
    return render_template('index.html',message="Not Logged in")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads')
def upload_file():
    cursor1 = mysql.connection.cursor()
    file_path = session['file_path']
    name=session['filename']
    username = session['user']
    prename = request.args['preferred']
    cursor1.execute("select * from Image_path where username=%s",[username])
    exists=cursor1.fetchall()
    cursor1.execute("select Preferredname from Image_path where username=%s", [username])
    if not exists :
        cursor1.execute("insert into Image_path (Name,Imagepath, username, Preferredname) values(%s,%s,%s,%s)",[name, file_path, username, prename])
        mysql.connection.commit()

    else:
        cursor1.execute("update Image_path set Name=concat(Name,',',%s) where username=%s",[name,username])
        cursor1.execute("update Image_path set Imagepath=concat(Imagepath,',',%s) where username=%s",[file_path,username])
        cursor1.execute("update Image_path set Preferredname=concat(Preferredname,',',%s) where username=%s", [prename, username])
    mysql.connection.commit()
    return render_template('signature_upload.html',message="upload")


@app.route('/uploads/<filename>',methods=['GET', 'POST'])
def uploaded_file(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/mlalgo', methods=['GET', 'POST'])
def detect_signature():
    file_path = ''
    filename = 'edge.jpg'
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            session['filename'] = filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = app.config['UPLOAD_FOLDER'] + filename
            session['file_path']=file_path

    image = cv2.imread(file_path)
    b, g, r = cv2.split(image)  # get b,g,r
    rgb_img = cv2.merge([r, g, b])  # switch it to rgb

    # Denoising
    dst = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)

    b, g, r = cv2.split(dst)
    rgb_dst = cv2.merge([r, g, b])

    cv2.imwrite(app.config['UPLOAD_FOLDER'] + filename, rgb_dst)

    img = cv2.imread(app.config['UPLOAD_FOLDER'] + filename, 0)
    edges = cv2.Canny(img, 80, 100)

    plt.subplot(121), plt.imshow(img, cmap='gray')
    plt.title('Original Image'), plt.xticks([]), plt.yticks([])
    plt.subplot(122), plt.imshow(edges, cmap='gray')
    plt.title('Edge Image'), plt.xticks([]), plt.yticks([])

    crop_img = cv2.subtract(255, edges)
    cv2.imwrite(app.config['UPLOAD_FOLDER'] + filename, crop_img)

    return render_template('signature_upload.html', message ="success")


@app.route('/draw_signature')
def draw_signature():
    if 'user' in session:
        return render_template('draw_signature.html')
    return render_template('index.html',message="Not Logged in")


@app.route('/draw', methods=['GET','POST'])
def draw_sign():
    if request.method == "POST":
        image_data = request.form['image_data']
        prename = request.form['d_preferredname']
        cursor1 = mysql.connection.cursor()
        username = session['user']

        cursor1.execute("select * from draw_sign where username=%s", [username])
        exists = cursor1.fetchall()
        cursor1.execute("select prefferdname from draw_sign where username=%s", [username])
        if not exists:
            cursor1.execute("insert into draw_sign (image, username, prefferdname) values(%s,%s,%s)", [image_data, username, prename])
            mysql.connection.commit()
            return render_template('draw_signature.html', message="upload")

        else:
            cursor1.execute("update draw_sign set image=concat(image,',',%s) where username=%s", [image_data, username])
            cursor1.execute("update draw_sign set prefferdname=concat(prefferdname,',',%s) where username=%s",[prename, username])
            mysql.connection.commit()
            return render_template('draw_signature.html', message="upload")


if __name__ == '__main__':
    app.run(debug=True)
