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

# ----------------- Helper Function -----------------
def normalize_value(val):
    """Convert values to a clean string. If numeric, remove decimal parts."""
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

# ----- Login Endpoint -----
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    try:
        # Retrieve user data from GitHub
        content = repo.get_contents(CSV_FILE, ref=BRANCH)
        df = pd.read_csv(StringIO(content.decoded_content.decode()))
        
        # Normalize username if necessary
        if "username" in df.columns:
            df["username"] = df["username"].apply(normalize_value)
        
        # Check if username and password match.
        user = df[(df["username"] == username) & (df["password"] == password)]
        if user.empty:
            flash("Invalid username or password.", "danger")
        else:
            flash("Login successful!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    
    return redirect(url_for('index'))

# ----- Sign Up Endpoint -----
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    try:
        # Retrieve user data from GitHub
        content = repo.get_contents(CSV_FILE, ref=BRANCH)
        df = pd.read_csv(StringIO(content.decoded_content.decode()))
        
        # Normalize username if necessary
        if "username" in df.columns:
            df["username"] = df["username"].apply(normalize_value)
        
        # Check if the username already exists.
        if username in df["username"].values:
            flash("Username already exists!", "danger")
            return redirect(url_for('index'))
        
        # Append new user record; CSV must have columns: username, password.
        new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
        df = pd.concat([df, new_user], ignore_index=True)
        
        # Update the CSV file in GitHub.
        repo.update_file(
            path=CSV_FILE,
            message="Add new user",
            content=df.to_csv(index=False),
            sha=content.sha,
            branch=BRANCH
        )
        flash("Signup successful! Please proceed to login.", "success")
    except Exception as e:
        flash(f"Error during signup: {str(e)}", "danger")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
