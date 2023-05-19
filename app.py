from flask import Flask, request, jsonify, make_response
from flask_mail import Message, Mail
from flask_cors import CORS, cross_origin
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import gspread

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ['APPCONFIGSECRETKEY']
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ["EMAIL_SENDER"]
app.config['MAIL_PASSWORD'] = os.environ["EMAIL_PASSWORD"]
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Initialize Mail after config setup
mail = Mail(app)

# TODO: Select proper origin for DEV or PROD
# DEV CORS
# cors = CORS(app, resources={r'/*': {'origins': '*'}})
# PROD CORS
# cors = CORS(app, resources={r'/*': {'origins': [os.environ['CORS_ORIGIN_PROD']]}})


# Get blogs from Google Sheet
GOOGLE_SERVICE_ACCOUNT_CREDENTIALS = {
    "type": "service_account",
    "project_id": "website-lending",
    "private_key_id": os.environ["PRIVATE_KEY_ID"],
    "private_key": f"-----BEGIN PRIVATE KEY-----\n{os.environ['PRIVATE_KEY']}\nTu9CBYrbpTIYIuY3R3oNYDMezD3+QUfrUe6Dy4pkkwVDUX1pne3eIVtEhuI3wZmt\nTxGZFHUtPpCxgFslKmgk4DK7qVSdj5Wy451EY5+81/1jF3mZ7TEBkXhjrt93+Pn3\ndRU3GTpkWy7gFvr+iv5oCEoF6aFmrxhqS5LiO/HtMaN6d05mmwgqiWo/vZgRlJDt\ncXugjtVRMED/fsG9GZAt55xEEFVyTF+xf7VhY1J9gl15cUnbFyigr+XC1gaVef+Z\noVdE5JRtnirQfvLj7gYwHV2WxBt6BIx3nG7qM4TNm75HbeiPfIhQwecFhdNkTKb2\nd+CDwlXdAgMBAAECggEADf4pnl9I2Nfws21z03IJCKcsih6feBu3IJRTDnVL0iTE\nBMhL9jAOhTE6e5RcMsvi7XcLeyqOMwlVRhiR4TwZRertzC8hX+2Kr/xYnpPVMgsN\n56PaSxpIBs/AizhzMAajmeeO+agFQxzTrrrzYZjNuOLu8QjMAPMX0+YZqCUAjIPh\n4XrrKN68y19WPw2hYijXNRfpDahbtVO3eyPku+/ShK1huYRAHdNdgcmGyZ7oUsrj\neP8btlJiz1JSuwat8SESSdZBV2woaqiMGfWiV83qZ2CQVlsNqQtEvzUQFZbKcDei\neGkl9x6Qwi7KhnLaQaCYYOwtmCPDHbvyRUyLVIMEQQKBgQDVeClC/zilntQ3YWl5\nLPC6FVaz7LY2QbGoWrpS7X/BnH0+ehmH1NRnwDRt3T/ON/87dSILL5z3LjIp/0vk\nPe7hIHQWT/MSVrgJpsnJcby1w3v4Gpa8yz/iaofsnxTgeSLkJXA4LETi/1nH7LXP\nUC/g/1yaFcBB8FoDSIT2hxkaWQKBgQDTrnTdi93uali+VcRTcf3wfxWRKNAPowqm\nZ2JhHHreRGPaunMKkRQ2IsircBfhlHsFGYQptp2IuRE5nopDsHS/+5dnXO8/dtnO\nJGz5RaAOwkvdrq1gTcknGVxRM8oqh12h4VGk8MH+s5KjzpQxEp1EZcSjew35L2c5\nSF6Qtt7fJQKBgA1XdTy6ts+jHaBYdj8cj+8RZlnYcYrykCf1g6+rKFDxduJwvye+\nJYhWevBi45n/5fPRXk9UqnrIaFo3moapWES5woeid46t3NK9md79PM4faaAYCVPD\nYDrGbbhcOPHOoF+h92GLYsLNMs9L/BD48gUd8KuwsFNusjGCVs0RpIABAoGAf163\nvx8L2QtwfoaI7VTn4a/2QDP4jZAjNmF61sgWPmuUUeZilncZXEGt0UpPdFKtezIR\nTjAttjj1XmBA/d3NQj+WqIFJDDztbZaJY6w7VOYgVDFo7Uugv8AIxmuNN+3fryou\nwDqF4EYY9Cu3C5gRvTgnC99dVxTo3ZToIdeHX2kCgYAyZvLJzff4GXKdWRzwQOih\n0JhpT/bQHzRDvViM1tsKbfMqN7yih3DlM7fNNH0ps3g5tQfAwA+/pgqsM/GObHrw\nUzopTvTZ7+8Q8viVBxB6UKjMlpjxUysKu+GFC3b5m1ofFeS4CvHMgqWWf2yna5wz\nBdS1ZoX1Kn9Rcdvn6lUaMQ==\n-----END PRIVATE KEY-----\n",
    "client_email": "website-lending@website-lending.iam.gserviceaccount.com",
    "client_id": os.environ["CLIENT_ID"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/website-lending%40website-lending.iam.gserviceaccount.com"
}

service_acc = gspread.service_account_from_dict(GOOGLE_SERVICE_ACCOUNT_CREDENTIALS)
gsheet_file = service_acc.open("electricien-nimes")

# Switching to MySQL DB
mydb = mysql.connector.connect(
    host=os.environ.get('MYSQLHOST'),
    user=os.environ.get('MYSQLUSER'),
    password=os.environ.get('MYSQLPASSWORD'),
    database=os.environ.get('MYSQLDATABASE')
)
cursor = mydb.cursor(buffered=True, dictionary=True)

get_blogs_query = """ 
SELECT * FROM blog
"""

cursor.execute(get_blogs_query)
blogs = cursor.fetchall()


@app.route('/get-blogs')
@cross_origin(origins='https://electricien-nimes.com/')
def get_blogs():
    # blog_worksheet = gsheet_file.worksheet("blogs")
    # blog_data = blog_worksheet.get_all_records()
    return jsonify(blogs), 200


@app.route('/contact', methods=['POST'])
@cross_origin(allow_headers=['Content-Type'], origins=['https://electricien-nimes.com/contact', 'https://electricien-nimes.com/contact/'])
def contact():
    # get contact form data
    form_data = request.get_json()
    name = form_data["name"]
    email = form_data["email"]
    phone = form_data["phone"]
    service = form_data["service"]
    timeframe = form_data["timeframe"]
    budget = form_data["budget"]
    message = form_data["message"]
    today = datetime.today().strftime("%d/%m/%Y %H:%M:%S")

    # update google sheet
    contacts_worksheet = gsheet_file.worksheet("contacts")
    worksheet_rows = len(contacts_worksheet.get_all_values())
    new_data = [today, name, email, phone, service, timeframe, budget, message]
    for col in range(1, len(new_data) + 1):
        contacts_worksheet.update_cell(worksheet_rows + 1, col, str(new_data[col - 1]))

    # send email notification
    html = f"Electricien Nîmes - Nouveau message!<br>" \
           f"<br>" \
           f"Date : {today}<br>" \
           f"Nom : {name}<br>" \
           f"Email : {email}<br>" \
           f"Téléphone : {phone}<br>" \
           f"Service : {service}<br>" \
           f"Délais : {timeframe}<br>" \
           f"Budget : {budget}<br>" \
           f"Message : {message}<br><br>" \
           f"Voir https://docs.google.com/spreadsheets/d/1PDZtqhsUVgdv83s_uAGr3Z_ElT4_dfMtBocGqSq9SxM/edit#gid=330549784"
    msg = Message(
        subject='Electricien Nîmes - Nouveau message!',
        html=html,
        sender=('Contact - Electricien Nîmes', app.config['MAIL_USERNAME']),
        recipients=[os.environ["EMAIL_RECIPIENT_1"], os.environ["EMAIL_RECIPIENT_2"]]
    )
    mail.send(msg)
    return "success", 200


if __name__ == "__main__":
    # TODO: Select proper run for DEV or PROD
    # app.run(port=8000, debug=True)
    app.run()
