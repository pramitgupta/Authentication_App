from flask import Flask, render_template, request, redirect, flash, url_for
import pandas as pd
from github import Github
from io import StringIO
import random
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# ----------------- GitHub Configuration -----------------
GITHUB_TOKEN = "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"  # Replace with your token
REPO_NAME = "pramitgupta/Authentication_App"  # Format: username/repo-name
CSV_FILE = "users.csv"
BRANCH = "main"  # Update if your default branch is different

# ----------------- Global OTP Store -----------------
otp_store = {}

# Initialize GitHub connection
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def normalize_mobile(val):
    """Convert mobile values to a clean string. If numeric, remove decimal parts."""
    try:
        if pd.isna(val):
            return ""
        if isinstance(val, (int, float)) and not math.isnan(val):
            return str(int(val))
        return str(val).strip()
    except Exception as e:
        return str(val).strip()

# ----------------- Routes -----------------
@app.route('/')
def index():
    return render_template('index.html')

# ----- Sign Up Endpoints -----
@app.route('/signup/generate_otp', methods=['POST'])
def signup_generate_otp():
    mobile = request.form.get('mobile', '').strip()
    otp = random.randint(100000, 999999)
    otp_store[mobile] = otp
    print(f"Signup OTP for {mobile}: {otp}")
    flash(f"OTP generated for {mobile}. Check the server console.", "info")
    return redirect(url_for('index'))

@app.route('/signup/verify', methods=['POST'])
def signup_verify():
    mobile = request.form.get('mobile', '').strip()
    otp_entered = request.form.get('otp', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if mobile not in otp_store:
        flash("Please generate an OTP first.", "warning")
        return redirect(url_for('index'))
    
    if str(otp_store[mobile]) != str(otp_entered):
        flash("Incorrect OTP. Please try again.", "danger")
        return redirect(url_for('index'))
    
    # OTP verified; remove it from the store.
    del otp_store[mobile]
    
    try:
        content = repo.get_contents(CSV_FILE, ref=BRANCH)
        df = pd.read_csv(StringIO(content.decoded_content.decode()))
        if "mobile" in df.columns:
            df["mobile"] = df["mobile"].apply(normalize_mobile)
            
        # Check if mobile or username already exists.
        if mobile in df["mobile"].values:
            flash("Mobile number already registered!", "danger")
            return redirect(url_for('index'))
        if username in df["username"].values:
            flash("Username already exists!", "danger")
            return redirect(url_for('index'))
        
        # Append new user record; CSV must have columns: username, password, mobile.
        new_user = pd.DataFrame([[username, password, mobile]], columns=["username", "password", "mobile"])
        df = pd.concat([df, new_user], ignore_index=True)
        
        # Update GitHub file.
        repo.update_file(
            path=CSV_FILE,
            message="Add new user",
            content=df.to_csv(index=False),
            sha=content.sha,
            branch=BRANCH
        )
        flash("Signup successful! Please proceed to login with the same credentials.", "success")
    except Exception as e:
        flash(f"Error during signup: {str(e)}", "danger")
    
    return redirect(url_for('index'))

# ----- Login Endpoints -----
@app.route('/login/generate_otp', methods=['POST'])
def login_generate_otp():
    mobile = request.form.get('mobile', '').strip()
    password = request.form.get('password', '').strip()
    
    try:
        content = repo.get_contents(CSV_FILE, ref=BRANCH)
        df = pd.read_csv(StringIO(content.decoded_content.decode()))
        if "mobile" in df.columns:
            df["mobile"] = df["mobile"].apply(normalize_mobile)
        
        # Check if mobile and password match.
        user = df[(df["mobile"] == mobile) & (df["password"] == password)]
        if user.empty:
            flash("Invalid mobile number or password.", "danger")
            return redirect(url_for('index'))
        
        otp = random.randint(100000, 999999)
        otp_store[mobile] = otp
        print(f"Login OTP for {mobile}: {otp}")
        flash(f"OTP generated for {mobile}. Check the server console.", "info")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    
    return redirect(url_for('index'))

@app.route('/login/verify', methods=['POST'])
def login_verify():
    mobile = request.form.get('mobile', '').strip()
    otp_entered = request.form.get('otp', '').strip()
    
    try:
        if mobile not in otp_store:
            flash("Please generate an OTP first.", "warning")
            return redirect(url_for('index'))
        if str(otp_store[mobile]) != str(otp_entered):
            flash("Incorrect OTP. Please try again.", "danger")
            return redirect(url_for('index'))
        del otp_store[mobile]
        flash("Login successful!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
