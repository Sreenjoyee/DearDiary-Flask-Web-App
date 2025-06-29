from flask import render_template, url_for, flash, redirect, request,abort
from flaskblog import app,db,bcrypt
from flaskblog.models import User, Post
from flaskblog.forms import RegistrationForm, LoginForm, UpdateForm, PostForm, RequestResetForm, ResetPasswordForm
from flask_login import login_user,current_user, logout_user, login_required
from sqlalchemy import or_
import os
import requests

  
@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)  
    per_page = 5
    if current_user.is_authenticated:
       posts_query = Post.query.filter(
            or_(
                Post.is_private == False,
                Post.author == current_user
            )
        ).order_by(Post.date_posted.desc())
    else:
        posts_query = Post.query.filter_by(is_private=False).order_by(Post.date_posted.desc())

    posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('home.html', posts=posts)


@app.route('/about') 
def about():
    return render_template('about.html',title='About') 


@app.route('/register',methods=['GET','POST']) 
def register():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form=RegistrationForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account is created! You can now login.','success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form) 

@app.route('/login',methods=['GET','POST'])  
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page=request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash("Login unsuccessful please provide the correct email and password", 'danger')
    return render_template('login.html',title='Login',form=form)

@app.route('/logout')  
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account',methods=['GET','POST'])  
@login_required
def account():
    form = UpdateForm()
    if form.validate_on_submit():
        current_user.username= form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash("Your account was updated successfully", 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username 
        form.email.data = current_user.email 
    return render_template('account.html',title='Account', form =form)

@app.route('/post/new',methods=['GET','POST'])  
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post=Post(title=form.title.data,content=form.content.data,is_private=form.is_private.data, author = current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html',title='New Post', form =form, legend='New Post')


@app.route('/post/<int:post_id>')
def post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.is_private and post.author != current_user:
        abort(403)
    return render_template('post.html',title=post.title,post=post)

@app.route('/post/<int:post_id>/update',methods=['GET','POST'])
@login_required
def update_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form=PostForm()
    
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        post.is_private=form.is_private.data
        db.session.commit()
        flash("Your post has been updated!", 'success')
        return redirect(url_for('post',post_id=post.id))
    
    elif request.method == 'GET':
        form.title.data=post.title
        form.content.data=post.content
        form.is_private.data = post.is_private

    return render_template('create_post.html',title='Update Post', form =form, legend='Update Post')

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)  
    user=User.query.filter_by(username=username).first_or_404()
    per_page = 5

    posts_query = Post.query.filter_by(author=user).order_by(Post.date_posted.desc())

    if current_user.is_authenticated:
        if current_user != user:  
            posts_query = posts_query.filter(Post.is_private == False)
    else:
        posts_query = posts_query.filter_by(is_private=False)
    
    posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('reset_token', token=token, _external=True)

    payload = {
        "sender": {"name": "Dear Diary", "email": os.getenv("EMAIL_USER")},
        "to": [{"email": user.email}],
        "subject": "Reset Your Password",
        "textContent": f"""To reset your password, click the link below:\n{reset_url}\n\nIf you didn't request this, ignore this email."""
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": os.getenv("BREVO_API_KEY")
    }

    response = requests.post("https://api.brevo.com/v3/smtp/email", 
                             json=payload, headers=headers)

    if response.status_code == 429:
        flash("Email limit reached. Please try resetting your password tomorrow.", "info")
        return False

    if response.status_code != 201:
        print("Brevo Error:", response.status_code, response.text)
        flash("An error occurred while sending the email. Please try again later.", "info")
        return False

    return True


@app.route('/reset_password',methods=['GET','POST'])  
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form= RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        success=send_reset_email(user)
        if success:
            flash("An email has been sent with instructions to reset your password.",'info')
        return redirect(url_for('login'))

    return render_template('reset_request.html', title='Reset Request', form=form)

@app.route('/reset_password/<string:token>',methods=['GET','POST'])  
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    user=User.verify_reset_token(token)

    if user is None:
        flash('That is an invalid or expired token', 'danger')
        return redirect(url_for('reset_request'))
    
    form=ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashed_password
        db.session.commit()
        flash(f'Your password was reset succesfully!','success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
    
