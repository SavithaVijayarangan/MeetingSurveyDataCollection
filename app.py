from flask import Flask, redirect, request, session, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from msal import ConfidentialClientApplication
import SurveyResult
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Azure AD Configuration
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
AUTHORITY = 'https://login.microsoftonline.com/YOUR_TENANT_ID'
SCOPE = ['openid', 'profile', 'email']

# MSAL Configuration
app.config["MSAL_CLIENT_ID"] = CLIENT_ID
app.config["MSAL_CLIENT_SECRET"] = CLIENT_SECRET
app.config["MSAL_AUTHORITY"] = AUTHORITY

#db configuration
app.config["SQLALCHEMY_DATABASE_URI"] = 'mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))
    return "Welcome, {}!".format(session["user"]["preferred_username"])

@app.route("/login")
def login():
    if not session.get("user"):
        auth_context = ConfidentialClientApplication(
            app.config["MSAL_CLIENT_ID"],
            authority=app.config["MSAL_AUTHORITY"],
            client_credential=app.config["MSAL_CLIENT_SECRET"]
        )
        auth_url, _ = auth_context.get_authorization_request_url(
            scopes=SCOPE,
            redirect_uri=url_for("authorized", _external=True)
        )
        return redirect(auth_url)
    return redirect(url_for("index"))

@app.route("/authorized")
def authorized():
    if not session.get("user"):
        auth_context = ConfidentialClientApplication(
            app.config["MSAL_CLIENT_ID"],
            authority=app.config["MSAL_AUTHORITY"],
            client_credential=app.config["MSAL_CLIENT_SECRET"]
        )
        token = auth_context.acquire_token_by_authorization_code(
            request.args["code"],
            scopes=SCOPE,
            redirect_uri=url_for("authorized", _external=True)
        )
        if "error" in token:
            return "Authentication failed: {}".format(token["error_description"])
        user_info = requests.get(
            app.config["MSAL_AUTHORITY"] + "/v2.0/me",
            headers={"Authorization": "Bearer " + token["access_token"]}
        ).json()
        session["user"] = user_info
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/survey")
def survey():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("survey.html")

@app.route("/submit_survey", methods=["POST"])
def submit_survey():
    if not session.get("user"):
        return redirect(url_for("login"))

    # Retrieve survey answers from the form
    question1 = request.form.get("question1")
    question2 = request.form.get("question2")
    question3 = request.form.get("question3")
    user_id = session["user"]["preferred_username"]

    # Create a new SurveyResult instance and add it to the database
    survey_result = SurveyResult(question1=question1, question2=question2, question3=question3, user_id=user_id)
    db.session.add(survey_result)
    db.session.commit()

    return "Thank you for completing the survey!"

if __name__ == "__main__":
    app.run(ssl_context="adhoc", debug=False, port=4000)

