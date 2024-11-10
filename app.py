# Modify the provided code to include global storage for `agreement_id` and adjust payment behavior based on its existence.


from flask import Flask, render_template, redirect, url_for, jsonify, request, session
import requests

app = Flask(__name__)
app.secret_key = 'a_secure_random_string'  # Set a secret key for session management

# Credentials and URLs from the JSON file
BASE_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta/tokenized/checkout"
APP_KEY = "0vWQuCRGiUX7EPVjQDr0EUAYtc"
APP_SECRET = "jcUNPBgbcqEDedNKdvE4G1cAK7D3hCjmJccNPZZBq96QIxxwAMEx"
USERNAME = "01770618567"
PASSWORD = "D7DaC<*E*eG"

# Global variable for storing agreement ID
global_agreement_id = None

# Store payment details temporarily, with a list for each session
payment_details_store = {}

@app.route('/')
def home():
    products = [
        {'name': 'Product 1', 'price': '20', 'image': 'static/images (1).jpg', 'id': 1},
        {'name': 'Product 2', 'price': '35', 'image': 'static/images (2).jpg', 'id': 2},
    ]
    # Check if payment details are available in the session
    payment_history = payment_details_store.get(session.get('user_id'), [])
    return render_template('home.html', products=products, payment_history=payment_history)

# Helper function to obtain OAuth token
def grant_token():
    url = f"{BASE_URL}/token/grant"
    headers = {'username': USERNAME, 'password': PASSWORD, 'Content-Type': 'application/json'}
    data = {"app_key": APP_KEY, "app_secret": APP_SECRET}
    response = requests.post(url, headers=headers, json=data)
    return response.json().get("id_token") if response.ok else None

# New: Agreement functionalities

# Route to create an agreement
@app.route('/create_agreement', methods=['POST'])
def create_agreement():
    global global_agreement_id  # Access the global variable
    token = grant_token()
    if not token:
        return "Error: Could not obtain token.", 500
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "mode": "0001",
        "payerReference": session.get("user_reference"),
    }
    response = requests.post(f"{BASE_URL}/agreement/create", headers=headers, json=data)
    response_data = response.json()
    if response_data.get("status") == "Success":
        global_agreement_id = response_data["agreement_id"]  # Store agreement ID globally
        return jsonify({"message": "Agreement created successfully", "agreement_id": response_data["agreement_id"]})
    else:
        return jsonify({"error": "Failed to create agreement", "details": response_data})

# Route to execute an agreement
@app.route('/execute_agreement', methods=['POST'])
def execute_agreement():
    global global_agreement_id
    if not global_agreement_id:
        return jsonify({"error": "No global agreement ID found"}), 400
    token = grant_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "agreement_id": global_agreement_id,
        "payerReference": session.get("user_reference"),
    }
    response = requests.post(f"{BASE_URL}/agreement/execute", headers=headers, json=data)
    return response.json()

# Route to query an agreement's status
@app.route('/query_agreement', methods=['GET'])
def query_agreement():
    global global_agreement_id
    if not global_agreement_id:
        return jsonify({"error": "No global agreement ID found"}), 400
    token = grant_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{BASE_URL}/agreement/status/{global_agreement_id}", headers=headers)
    return response.json()

# Route to cancel an agreement
@app.route('/cancel_agreement', methods=['POST'])
def cancel_agreement():
    global global_agreement_id
    if not global_agreement_id:
        return jsonify({"error": "No global agreement ID found"}), 400
    token = grant_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/agreement/cancel/{global_agreement_id}", headers=headers)
    response_data = response.json()
    if response_data.get("status") == "Success":
        global_agreement_id = None  # Clear the global agreement ID
        return jsonify({"message": "Agreement canceled successfully"})
    else:
        return jsonify({"error": "Failed to cancel agreement", "details": response_data})

# Payment route to create a payment
@app.route('/buy/<int:product_id>')
def create_payment(product_id):
    global global_agreement_id
    token = grant_token()
    if not token:
        return "Error: Could not obtain token.", 500

    url = f"{BASE_URL}/create"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-App-Key": APP_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Check if agreement exists for different payment process
    if global_agreement_id:
        data = {
            "mode": "0011",
            "payerReference": "01619777282",
            "callbackURL": url_for('payment_status', product_id=product_id, _external=True),
            "amount": "15" if product_id == 1 else "30",  # Discounted price for agreement holders
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": f"Inv{product_id}"
        }
    else:
        data = {
            "mode": "0011",
            "payerReference": "01619777282",
            "callbackURL": url_for('payment_status', product_id=product_id, _external=True),
            "amount": "20" if product_id == 1 else "35",  # Regular price without agreement
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": f"Inv{product_id}"
        }

    response = requests.post(url, headers=headers, json=data)

    if response.ok:
        payment_url = response.json().get("bkashURL")
        return redirect(payment_url)
    return "Error creating payment.", 500

# Payment status route
@app.route('/payment_status/<int:product_id>')
def payment_status(product_id):
    payment_id = request.args.get("paymentID")
    token = grant_token()
    if not token or not payment_id:
        return "Error: Payment ID or token missing.", 500

    url = f"{BASE_URL}/payment/status"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-App-Key": APP_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {"paymentID": payment_id}
    response = requests.post(url, headers=headers, json=data)

    if response.ok:
        payment_details = response.json()
        user_id = session.setdefault('user_id', id(session))
        payment_details_store.setdefault(user_id, []).append(payment_details)
        return redirect(url_for('home'))
    return "Error retrieving payment status.", 500

# Payment details route
@app.route('/payment_details')
def payment_details():
    user_id = session.get('user_id')
    payment_history = payment_details_store.get(user_id, [])
    return render_template('payment_details.html', payment_history=payment_history)

if __name__ == '__main__':
    app.run(debug=True)


# Saving this updated code to a new file for download
global_agreement_file_path = '/mnt/data/app_with_global_agreement_id.py'
with open(global_agreement_file_path, 'w') as final_file_with_global:
    final_file_with_global.write(updated_code_with_global_agreement_id)

global_agreement_file_path
