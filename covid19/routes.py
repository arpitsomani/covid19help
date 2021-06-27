import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from covid19 import app, db, bcrypt, mail
from covid19.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             PostForm, RequestResetForm, ResetPasswordForm)
from covid19.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import pandas as pd
pd.set_option('max_rows',20)
import folium
import numpy as np
import cv2
import imutils
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import  img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from imutils.video import VideoStream


@app.route("/")
@app.route("/home",methods=['GET', 'POST'])
def home():
    cntry ='India'
    if request.method == 'POST':
        cntry = request.form.get("country")

    citylist = []
    users = User.query.all()

    for user in users:
        if user.city not in citylist:
            citylist.append(user.city)
    
    citylist.sort()
    #CONF_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    #DEAD_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
    #RECV_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'

    covid_conf_ts = pd.read_csv('data_files/time_series_covid19_confirmed_global.csv')
    covid_dead_ts = pd.read_csv('data_files/time_series_covid19_deaths_global.csv')
    covid_recv_ts = pd.read_csv('data_files/time_series_covid19_recovered_global.csv')
    covid_conf=covid_conf_ts[['Lat','Long','5/20/21']]
    covid_conf=covid_conf.dropna()

    m=folium.Map(location=[20.593684,78.96288], zoom_start=3, tiles="cartodbpositron",min_zoom = 1.5, max_zoom=5)

    def circle_maker(x):
        folium.Circle(location=[x[0],x[1]],radius=float(x[2]/30),
                      color="lightred",fill_color="red",
                      fill_opacity=0.5,
                     popup='confirmed cases:{}'.format(x[2])).add_to(m)

    covid_conf.apply(lambda x:circle_maker(x),axis=1)
        
    def get_overall_total(df):
        return df.iloc[:,-1].sum()

    conf_overall_total = get_overall_total(covid_conf_ts)
    dead_overall_total = get_overall_total(covid_dead_ts)
    recv_overall_total = get_overall_total(covid_recv_ts)

    def get_cntry_total(df,cntry):
        return df[df['Country/Region']==cntry].iloc[:,-1].sum()

    
    conf_cntry_total = get_cntry_total(covid_conf_ts,cntry)
    dead_cntry_total = get_cntry_total(covid_dead_ts,cntry)
    recv_cntry_total = get_cntry_total(covid_recv_ts,cntry)
    

    def get_country_list():
        return covid_conf_ts['Country/Region'].unique()

    def create_dropdown_list(cntry_list):
        dropdown_list = []
        for cntry in sorted(cntry_list):
            dropdown_list.append(cntry)
        return dropdown_list

    countries=create_dropdown_list(get_country_list())
    html_map=m._repr_html_()

    return render_template('home.html',count=len(citylist) ,citylist=citylist,countries=countries,cntry=cntry,cmap=html_map,
    conf_overall_total=conf_overall_total,dead_overall_total=dead_overall_total,recv_overall_total=recv_overall_total,
    conf_cntry_total=conf_cntry_total,dead_cntry_total=dead_cntry_total,recv_cntry_total=recv_cntry_total)

@app.route('/resources', methods=['GET', 'POST'])
def resources():
    if request.method == 'POST':
        city = request.form.get("city")
        resources = request.form.get("resources")

        list1 = []
        list2 = []
        list3 = []
        list4 = []
        list5 = []
        list6 = []

        results = User.query.all()
        
        for result in results:
            if (city in result.city) is True:
                if (resources in result.resources) is True:
                    list1.append(result.city)
                    list2.append(result.username)
                    list3.append(result.address)
                    list4.append(result.resources)
                    list5.append(result.contact)
                    list6.append(result.email)

 
        lister = []
        lister.append(list1), lister.append(list2), lister.append(list3), lister.append(list4),lister.append(list5),lister.append(list6)

        if (lister[0]==[]):
            flash('No Such Resources Found in This City!, Please Check Again Soon', 'danger')
        
        return render_template("resources.html", count=len(list1), result1=lister)


@app.route("/trends")
def trends():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=6)
    content =Post.query.order_by(Post.date_posted.desc()).first()
    text=content.content
    from textblob import TextBlob
    def get_sentiment(text):
        blob = TextBlob(text)
        sentiment_polarity = blob.sentiment.polarity
        sentiment_subjectivity = blob.sentiment.subjectivity
        if sentiment_polarity > 0:
            sentiment_label = 'Positive'
        elif sentiment_polarity < 0:
            sentiment_label = 'Negative'
        else:
            sentiment_label = 'Neutral'
        result = {'polarity':sentiment_polarity,'subjectivity':sentiment_subjectivity,'sentiment':sentiment_label}
        return result

    senti=get_sentiment(text)
    return render_template('trends.html', posts=posts, senti=senti)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password,
                    city=form.city.data,address=form.address.data,resources=form.resources.data,
                    contact=form.contact.data,volunteer=form.volunteer.data,feedback=form.feedback.data)        
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    users = User.query.filter_by(volunteer='Yes').paginate(page=page, per_page=3)
    return render_template('register.html', title='Register', form=form, users=users)

@app.route("/maskdetect", methods=['GET', 'POST'])
def maskdetect():
    if request.method == 'POST':
        def detectMask(image, face, mask):
            (x, y) = image.shape[:2]
            blob = cv2.dnn.blobFromImage(image, 1.0, (224, 224),
                                        (104.0, 177.0, 123.0))    
            face.setInput(blob)
            detection = face.forward()
            print(detection.shape)
            faces = []
            locs = []
            preds = []
    
            for i in range(0, detection.shape[2]):
                confi = detection[0, 0, i, 2]
        
                if confi > 0.5:
                    box = detection[0, 0, i, 3:7] * np.array([y, x, y, x])
                    (startX, startY, endX, endY) = box.astype("int")            
                    (startX, startY) = (max(0, startX), max(0, startY))
                    (endX, endY) = (min(y-1, endX), min(x-1, endY))
                    face = image[startY:endY, startX:endX]
                    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                    face = cv2.resize(face, (224, 224))
                    face = img_to_array(face)
                    face = preprocess_input(face)
                    faces.append(face)
                    locs.append((startX, startY, endX, endY))
            
            if len(faces) > 0:
                faces = np.array(faces, dtype="float32")
                preds = mask.predict(faces, batch_size=32)
        
            return (locs, preds)

        prototxtPath = r"data_files/deploy.prototxt"
        weightsPath = r"data_files/res10_300x300_ssd_iter_140000.caffemodel"
        faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)
        maskNet = load_model("data_files/mask_detector.model")

        def probability(label):
            label = "{}: {:.2f}%".format(label, max(mask, withoutmask) * 100)
            return label
    
        cap = VideoStream(src=0).start()

        while True:
            image = cap.read()
            image = imutils.resize(image, width=400)
            (locs, preds) = detectMask(image, faceNet, maskNet)
    
            for (box, pred) in zip(locs, preds):
                (startX, startY, endX, endY) = box
                (mask, withoutmask) = pred
                label = "With Mask" if mask > withoutmask else "Without Mask"
                color = (0, 255, 0) if label == "With Mask" else (0, 0, 255)
        
                label = probability(label)
                cv2.putText(image, label, (startX, startY-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
                cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)
        
            cv2.imshow("Frame", image)
            key = cv2.waitKey(1) & 0xFF
    
            if key == ord("q"):
                break

        cv2.destroyAllWindows()
        cap.stop()
        return render_template('maskdetect.html', title='AI Predicts',label=label)
    return render_template('maskdetect.html', title='AI Predicts')

@app.route("/about")
def about():
    return render_template('about.html', title='About Us')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
     
    page = request.args.get('page', 1, type=int)
    users = User.query.filter_by(feedback='').paginate(page=page, per_page=2)        
    return render_template('login.html', title='Login', form=form, users=users)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.city = form.city.data
        current_user.address = form.address.data
        current_user.contact = form.contact.data
        current_user.resources = form.resources.data
        current_user.volunteer = form.volunteer.data
        current_user.feedback = form.feedback.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.contact.data = current_user.contact
        form.resources.data = current_user.resources
        form.volunteer.data = current_user.volunteer
        form.feedback.data = current_user.feedback
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('trends'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('trends'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=9)
    return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def error_500(error):
    return render_template('500.html'), 405