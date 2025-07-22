from flask import Flask, jsonify, request

from product.src.utils.mysqlutil import MySQLUtil

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Flask App"

@app.route('/api/jd_product', methods=['POST'])
def add_jd_product():
    data = request.get_json()
    if not data or 'sku_url' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    # Initialize MySQLUtil here (replace with your actual database credentials)
    db = MySQLUtil()
    success = db.insert_jd_product(data['sku_code'], data['sku_name'], data['price'])
    db.disconnect()
    
    if success:
        return jsonify({"message": "Product added successfully"}), 201
    else:
        return jsonify({"error": "Failed to add product"}), 500

def new_flask():
    return app