from flask import Flask, request, jsonify, render_template, redirect, url_for
import requests

app = Flask(__name__)

# Global variables to store the agreement ID and payment details
agreement_id_global = None
payment_details_global = {}

# Credentials
USERNAME = "01770618567"
PASSWORD = "D7DaC<*E*eG"
APP_KEY = "0vWQuCRGiUX7EPVjQDr0EUAYtc"
APP_SECRET = "jcUNPBgbcqEDedNKdvE4G1cAK7D3hCjmJccNPZZBq96QIxxwAMEx"

# API URLs
GRANT_TOKEN_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta/tokenized/checkout/token/grant"
CREATE_PAYMENT_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta/tokenized/checkout/create"
EXECUTE_PAYMENT_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta/tokenized/checkout/execute"

@app.route('/')
def index():
    products = [
        {"name": "Product 1", "price": 10, "image": "static/images (1).jpg"},
        {"name": "Product 2", "price": 20, "image": "static/images (2).jpg"}
    ]
    return render_template('index.html', products=products, agreement_id=agreement_id_global)

@app.route('/create_agreement', methods=['POST'])
def create_agreement():
    # Step 1: Grant Token
    token_response = requests.post(
        GRANT_TOKEN_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "username": USERNAME,
            "password": PASSWORD
        },
        json={
            "app_key": APP_KEY,
            "app_secret": APP_SECRET
        }
    )
    
    if token_response.status_code != 200:
        return jsonify({"error": "Failed to grant token", "details": token_response.json()}), token_response.status_code
    
    # Get the token from the response
    token_data = token_response.json()
    id_token = token_data["id_token"]
    
    # Step 2: Create Agreement
    agreement_response = requests.post(
        CREATE_PAYMENT_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": id_token,
            "X-App-Key": APP_KEY
        },
        json={
            "mode": "0000",
            "callbackURL": url_for('callback', _external=True),
            "payerReference": "01619777282"
        }
    )

    if agreement_response.status_code != 200:
        return jsonify({"error": "Failed to create agreement", "details": agreement_response.json()}), agreement_response.status_code
    
    # Extract the bkashURL and paymentID
    agreement_data = agreement_response.json()
    bkash_url = agreement_data.get("bkashURL")
    payment_id = agreement_data["paymentID"]

    # Store the payment_id globally for the callback
    global agreement_id_global
    agreement_id_global = payment_id

    return jsonify({"bkashURL": bkash_url})

@app.route('/create_payment', methods=['POST'])
def create_payment():
    # Step 1: Grant Token
    id_token = grant_token()
    if not id_token:
        return jsonify({"error": "Failed to grant token"}), 500

    # Payload setup based on agreement existence
    payment_payload = {
        "mode": "0001" if agreement_id_global else "0011",
        "payerReference": "01619777282",
        "callbackURL": url_for('callback', _external=True),
        "amount": "20",
        "currency": "BDT",
        "intent": "sale",
        "merchantInvoiceNumber": "Inv1"
    }
    if agreement_id_global:
        payment_payload["agreementID"] = agreement_id_global

    # Step 2: Create Payment
    payment_response = requests.post(
        CREATE_PAYMENT_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": id_token,
            "X-App-Key": APP_KEY
        },
        json=payment_payload
    )

    if payment_response.status_code != 200:
        return jsonify({"error": "Failed to create payment", "details": payment_response.json()}), payment_response.status_code
    payment_data = payment_response.json()
    print("Payment Data:", payment_data)  # Log to confirm keys

    # Extract bkashURL and paymentID from the response
    payment_data = payment_response.json()
    bkash_url = payment_data.get("bkashURL")
    payment_id = payment_data["paymentID"]
    payment_info = {
        
        "paymentID": payment_data["paymentID"],
        "mode": payment_payload["mode"],
        # Attempt to fetch createTime or use a fallbackd
        "paymentcreatetime": payment_data.get("createTime", "Unavailable"),
        "amount": payment_payload["amount"],
        "currency": payment_payload["currency"],
        "intent": payment_payload["intent"],
        "merchantinvoice": payment_payload["merchantInvoiceNumber"],
        "transactionstatus": "Initiated",
        "verificationstatus": "completed",
        "payerreference": payment_payload["payerReference"],
        "payertype": "Customer",
        "statuscode": payment_data.get("statusCode", "0000"),
        "statusmessage": payment_data.get("statusMessage", "Successful")
    }
        # Store payment details globally
    payment_details_global[payment_id] = payment_info

    # Redirect to bkash URL for approval
    bkash_url = payment_data.get("bkashURL")
    return jsonify({"bkashURL": bkash_url})

    

   
@app.route('/callback')
def callback():
    status = request.args.get('status')
    payment_id = request.args.get('paymentID')

    if status == "success":
        result = execute_agreement(payment_id)
        if result.status_code == 200:
            agreement_id = result.get_json().get("agreementID")
            global agreement_id_global
            agreement_id_global = agreement_id  # Save the agreement ID globally
            return render_template("callback_success.html", agreementID=agreement_id)
        else:
            return jsonify({"error": "Failed to execute agreement"}), result.status_code
    else:
        return render_template('callback_error.html')

def execute_agreement(payment_id):
    token_response = requests.post(
        GRANT_TOKEN_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "username": USERNAME,
            "password": PASSWORD
        },
        json={
            "app_key": APP_KEY,
            "app_secret": APP_SECRET
        }
    )

    if token_response.status_code != 200:
        return jsonify({"error": "Failed to grant token", "details": token_response.json()}), token_response.status_code

    token_data = token_response.json()
    id_token = token_data["id_token"]

    execute_response = requests.post(
        EXECUTE_PAYMENT_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": id_token,
            "X-App-Key": APP_KEY
        },
        json={"paymentID": payment_id}
    )

    if execute_response.status_code != 200:
        return jsonify({"error": "Failed to execute agreement", "details": execute_response.json()}), execute_response.status_code

    execute_data = execute_response.json()
    agreement_id = execute_data.get("agreementID")

    global agreement_id_global
    agreement_id_global = agreement_id

    return jsonify({"message": "Agreement executed successfully", "agreementID": agreement_id})

@app.route('/delete_agreement_id', methods=['POST'])
def delete_agreement_id():
    global agreement_id_global
    agreement_id_global = None
    return jsonify({"message": "Agreement ID deleted successfully"})

@app.route('/payment_details', methods=['GET'])
def payment_details():
    if payment_details_global:
        # Retrieve the latest payment by accessing the last key in the dictionary
        latest_payment_id = list(payment_details_global.keys())[-1]
        payment_info = payment_details_global[latest_payment_id]
        return render_template('payment_details.html', payment_details=payment_info)
    else:
        return render_template('payment_details.html', payment_details={})


# Helper function for getting the grant token
def grant_token():
    token_response = requests.post(
        GRANT_TOKEN_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "username": USERNAME,
            "password": PASSWORD
        },
        json={
            "app_key": APP_KEY,
            "app_secret": APP_SECRET
        }
    )

    if token_response.status_code != 200:
        return None

    token_data = token_response.json()
    return token_data.get("id_token")

if __name__ == '__main__':
    app.run(debug=True)
