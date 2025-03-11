from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app.forms.auth import LoginForm, SignupForm
from app.models.user import User
from app.utils.email import send_verification_email
from app.utils.tokens import verify_token
import re
from pymongo.errors import ConnectionFailure
from datetime import datetime

bp = Blueprint('auth', __name__)

def is_valid_username(username):
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def is_valid_password(password):
    # At least 8 characters, with at least one uppercase, lowercase, number, and special character
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))

def is_safe_url(target):
    """Check if the URL is safe to redirect to"""
    if not target:
        return False
    ref_url = urlparse(target)
    return not ref_url.netloc and ref_url.path.startswith('/')

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = SignupForm()
    
    # Debug form submission
    if request.method == 'POST':
        print("\n=== Form Submission Debug ===")
        print("Form Data:", request.form.to_dict())
        print("Files:", request.files)
        print("Form Errors:", form.errors)
        print("CSRF Token Present:", form.csrf_token.current_token is not None)
        print("Form Validated:", form.validate())
        print("===========================\n")
    
    if form.validate_on_submit():
        try:
            print("\n=== MongoDB Connection Debug ===")
            # Verify MongoDB connection
            try:
                current_app.db.command('ismaster')
                print("MongoDB connection is valid")
                print("Available collections:", current_app.db.list_collection_names())
            except Exception as e:
                print(f"MongoDB connection error: {str(e)}")
                flash('Database connection error', 'error')
                return render_template('auth/signup.html', form=form)

            print("\n=== User Creation Debug ===")
            print(f"Creating user with username: {form.username.data} and email: {form.email.data}")
            
            # Create user object
            user = User(
                username=form.username.data,
                email=form.email.data,
                is_verified=False
            )
            user.set_password(form.password.data)
            
            # Debug print user object
            user_dict = user.to_dict()
            print("User object created:", user_dict)
            
            print("\n=== MongoDB Insert Debug ===")
            try:
                # Verify users collection exists
                if 'users' not in current_app.db.list_collection_names():
                    print("Creating users collection...")
                    current_app.db.create_collection('users')
                
                # Insert user
                result = current_app.db.users.insert_one(user_dict)
                print(f"Insert result: {result.inserted_id}")
                
                # Verify insertion
                inserted_user = current_app.db.users.find_one({'_id': result.inserted_id})
                print(f"Verification query result: {inserted_user}")
                
                if inserted_user:
                    print("User successfully created and verified")
                    
                    # Send verification email
                    try:
                        send_verification_email(user)
                        flash('Registration successful! Please check your email to verify your account.', 'success')
                    except Exception as e:
                        print(f"Error sending verification email: {str(e)}")
                        flash('Account created but there was an error sending the verification email.', 'warning')
                    
                    return redirect(url_for('auth.login'))
                else:
                    print("ERROR: User verification failed after insert")
                    flash('Error creating account', 'error')
                    return render_template('auth/signup.html', form=form)
                    
            except Exception as e:
                print(f"MongoDB insert error: {str(e)}")
                flash('Error creating account', 'error')
                return render_template('auth/signup.html', form=form)
                
        except Exception as e:
            print(f"General error: {str(e)}")
            flash('Error creating account', 'error')
            return render_template('auth/signup.html', form=form)
    else:
        if request.method == 'POST':
            print("\n=== Form Validation Failed ===")
            print("Form errors:", form.errors)
            print("=============================\n")
    
    return render_template('auth/signup.html', form=form)

@bp.route('/verify/<token>')
def verify_email(token):
    email = verify_token(token)
    if not email:
        flash('The verification link is invalid or has expired.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.get_by_email(email)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.index'))
    
    if user.is_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('main.index'))
    
    # Update user verification status
    current_app.db.users.update_one(
        {'_id': user._id},
        {'$set': {'is_verified': True}}
    )
    
    flash('Your email has been verified. Thank you!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.is_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('main.index'))
    
    try:
        send_verification_email(current_user)
        flash('A new verification email has been sent.', 'success')
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        flash('Error sending verification email.', 'error')
    
    return redirect(url_for('main.index'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to get user by email first, then username
        identifier = form.identifier.data
        user = User.get_by_email(identifier) or User.get_by_username(identifier)
        
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.index')
            return redirect(next_page)
        flash('Invalid username/email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index')) 