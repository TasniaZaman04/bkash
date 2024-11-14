# from flask import Flask, redirect, request, jsonify, session, url_for
# import requests

# app = Flask(__name__)
# app.secret_key = 'a_secure_random_string'  # Set a secret key for session management

# # Credentials and URLs
# BASE_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta/tokenized/checkout"
# APP_KEY = "0vWQuCRGiUX7EPVjQDr0EUAYtc"
# APP_SECRET = "jcUNPBgbcqEDedNKdvE4G1cAK7D3hCjmJccNPZZBq96QIxxwAMEx"
# USERNAME = "01770618567"
# PASSWORD = "D7DaC<*E*eG"

# # Global variable for storing agreement ID
# global_agreement_id = None

# # Helper function to obtain OAuth token
# def grant_token():
#     print("Obtaining OAuth token...")
#     url = f"{BASE_URL}/token/grant"
#     headers = {'username': USERNAME, 'password': PASSWORD, 'Content-Type': 'application/json'}
#     data = {"app_key": APP_KEY, "app_secret": APP_SECRET}
#     response = requests.post(url, headers=headers, json=data)
#     if response.ok:
#         print("Token acquired successfully.")
#         return response.json().get("id_token")
#     else:
#         print("Error obtaining token:", response.text)
#         return None

# # Route to create an agreement
# @app.route('/bind_create_agreement', methods=['POST'])
# def bind_create_agreement():
#     global global_agreement_id
#     token = grant_token()
#     if not token:
#         return jsonify({"error": "Could not obtain token"}), 500

#     headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#     data = {"mode": "0001", "payerReference": session.get("user_reference")}
#     response = requests.post(f"{BASE_URL}/agreement/create", headers=headers, json=data)
#     response_data = response.json()
#     print("Create agreement response:", response_data)
#     if response_data.get("status") == "Success":
#         global_agreement_id = response_data["agreement_id"]
#         return jsonify({"message": "Agreement created successfully", "agreement_id": global_agreement_id})
#     else:
#         return jsonify({"error": "Failed to create agreement", "details": response_data})

# # Route to execute an agreement
# @app.route('/bind_execute_agreement', methods=['POST'])
# def bind_execute_agreement():
#     global global_agreement_id
#     if not global_agreement_id:
#         return jsonify({"error": "No agreement ID found"}), 400

#     token = grant_token()
#     headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#     data = {"agreement_id": global_agreement_id, "payerReference": session.get("user_reference")}
#     response = requests.post(f"{BASE_URL}/agreement/execute", headers=headers, json=data)
#     print("Execute agreement response:", response.json())
#     return response.json()

# # Route to cancel an agreement
# @app.route('/bind_cancel_agreement', methods=['POST'])
# def bind_cancel_agreement():
#     global global_agreement_id
#     if not global_agreement_id:
#         return jsonify({"error": "No agreement ID found"}), 400

#     token = grant_token()
#     headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#     response = requests.post(f"{BASE_URL}/agreement/cancel/{global_agreement_id}", headers=headers)
#     response_data = response.json()
#     print("Cancel agreement response:", response_data)
#     if response_data.get("status") == "Success":
#         global_agreement_id = None
#         return jsonify({"message": "Agreement canceled successfully"})
#     else:
#         return jsonify({"error": "Failed to cancel agreement", "details": response_data})

# # Route to handle bind payment
# @app.route('/bind_payment/<int:product_id>', methods=['POST'])
# def bind_payment(product_id):
#     global global_agreement_id
#     token = grant_token()
#     if not token:
#         return jsonify({"error": "Could not obtain token"}), 500

#     url = f"{BASE_URL}/create"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "X-App-Key": APP_KEY,
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }

#     # Check agreement status
#     print(f"Using agreement ID: {global_agreement_id} for product {product_id}")
#     data = {
#         "mode": "0011",
#         "payerReference": "01619777282",
#         "callbackURL": url_for('payment_status', product_id=product_id, _external=True),
#         "amount": "15" if global_agreement_id else "20",  # Discounted price if agreement exists
#         "currency": "BDT",
#         "intent": "sale",
#         "merchantInvoiceNumber": f"BindInv{product_id}"
#     }

#     response = requests.post(url, headers=headers, json=data)
#     print("Bind payment response:", response.json())
#     if response.ok:
#         payment_url = response.json().get("bkashURL")
#         return jsonify({"redirect_url": payment_url})
#     return jsonify({"error": "Error creating payment"}), 500

# # Payment status route
# @app.route('/payment_status/<int:product_id>')
# def payment_status(product_id):
#     payment_id = request.args.get("paymentID")
#     token = grant_token()
#     if not token or not payment_id:
#         return "Error: Payment ID or token missing.", 500

#     url = f"{BASE_URL}/payment/status"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "X-App-Key": APP_KEY,
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }
#     data = {"paymentID": payment_id}
#     response = requests.post(url, headers=headers, json=data)

#     print("Payment status response:", response.json())
#     if response.ok:
#         payment_details = response.json()
#         user_id = session.setdefault('user_id', id(session))
#         payment_details_store.setdefault(user_id, []).append(payment_details)
#         return redirect(url_for('home'))
#     return "Error retrieving payment status.", 500

# if __name__ == '__main__':
#     app.run(debug=True)



