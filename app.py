
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_connection


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# Allow Android app to communicate with Flask
CORS(app)


# ============================================================
# HOME / API STATUS
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "Online Products System API is running"
    }), 200


# ============================================================
# CUSTOMER REGISTRATION
# ============================================================

@app.route("/api/customer/register", methods=["POST"])
def register_customer():

    connection = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "No registration data received"
            }), 400

        # ----------------------------------------------------
        # GET DATA
        # ----------------------------------------------------

        name = str(data.get("name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        email = str(data.get("email", "")).strip()
        password = str(data.get("password", ""))
        notification_phone = str(
            data.get("notification_phone", "")
        ).strip()

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        if not name:

            return jsonify({
                "success": False,
                "message": "Name is required"
            }), 400

        if not phone:

            return jsonify({
                "success": False,
                "message": "Phone is required"
            }), 400

        if not password:

            return jsonify({
                "success": False,
                "message": "Password is required"
            }), 400

        if len(password) < 6:

            return jsonify({
                "success": False,
                "message": "Password must contain at least 6 characters"
            }), 400

        # ----------------------------------------------------
        # DATABASE CONNECTION
        # ----------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # CHECK EXISTING PHONE
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM customers
            WHERE phone = %s
            LIMIT 1
            """,
            (phone,)
        )

        existing_customer = cursor.fetchone()

        if existing_customer:

            return jsonify({
                "success": False,
                "message": "A customer with this phone already exists"
            }), 409

        # ----------------------------------------------------
        # CHECK EMAIL
        # ----------------------------------------------------

        if email:

            cursor.execute(
                """
                SELECT id
                FROM customers
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )

            existing_email = cursor.fetchone()

            if existing_email:

                return jsonify({
                    "success": False,
                    "message": "A customer with this email already exists"
                }), 409

        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        password_hash = generate_password_hash(password)

        # ----------------------------------------------------
        # INSERT CUSTOMER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO customers
            (
                name,
                email,
                phone,
                password_hash,
                notification_phone
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                name,
                email if email else None,
                phone,
                password_hash,
                notification_phone if notification_phone else None
            )
        )

        connection.commit()

        customer_id = cursor.lastrowid

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "message": "Customer registered successfully",
            "customer": {
                "id": customer_id,
                "name": name,
                "email": email,
                "phone": phone,
                "notification_phone": notification_phone
            }
        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Customer registration failed",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CUSTOMER LOGIN
# ============================================================

@app.route("/api/customer/login", methods=["POST"])
def login_customer():

    connection = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "No login data received"
            }), 400

        # ----------------------------------------------------
        # GET LOGIN DATA
        # ----------------------------------------------------

        name = str(data.get("name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        password = str(data.get("password", ""))

        # ----------------------------------------------------
        # VALIDATE INPUT
        # ----------------------------------------------------

        if not name:

            return jsonify({
                "success": False,
                "message": "Name is required"
            }), 400

        if not phone:

            return jsonify({
                "success": False,
                "message": "Phone is required"
            }), 400

        if not password:

            return jsonify({
                "success": False,
                "message": "Password is required"
            }), 400

        # ----------------------------------------------------
        # DATABASE CONNECTION
        # ----------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # FIND CUSTOMER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                phone,
                password_hash,
                notification_phone
            FROM customers
            WHERE name = %s
            AND phone = %s
            LIMIT 1
            """,
            (
                name,
                phone
            )
        )

        customer = cursor.fetchone()

        # ----------------------------------------------------
        # CUSTOMER NOT FOUND
        # ----------------------------------------------------

        if not customer:

            return jsonify({
                "success": False,
                "message": "Invalid name or phone"
            }), 401

        # ----------------------------------------------------
        # CHECK PASSWORD
        # ----------------------------------------------------

        password_hash = customer.get("password_hash")

        if not password_hash:

            return jsonify({
                "success": False,
                "message": "Customer password is not configured"
            }), 500

        if not check_password_hash(password_hash, password):

            return jsonify({
                "success": False,
                "message": "Invalid password"
            }), 401

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "message": "Login successful",
            "customer": {
                "id": customer["id"],
                "name": customer["name"],
                "email": customer.get("email"),
                "phone": customer["phone"],
                "notification_phone":
                    customer.get("notification_phone")
            }
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Login failed",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GET PRODUCTS
# ============================================================

@app.route("/api/products", methods=["GET"])
def get_products():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM products
            ORDER BY id DESC
            """
        )

        products = cursor.fetchall()

        return jsonify({
            "success": True,
            "products": products
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Failed to load products",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CREATE ORDER
# ============================================================

@app.route("/api/orders", methods=["POST"])
def create_order():

    connection = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "No order data received"
            }), 400

        customer_id = data.get("customer_id")
        product_id = data.get("product_id")
        quantity = data.get("quantity")

        # ----------------------------------------------------
        # VALIDATE NUMBERS
        # ----------------------------------------------------

        try:

            customer_id = int(customer_id)
            product_id = int(product_id)
            quantity = int(quantity)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": (
                    "customer_id, product_id and quantity "
                    "must be valid numbers"
                )
            }), 400

        if customer_id <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid customer_id"
            }), 400

        if product_id <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid product_id"
            }), 400

        if quantity <= 0:

            return jsonify({
                "success": False,
                "message": "Quantity must be greater than zero"
            }), 400

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # CHECK CUSTOMER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM customers
            WHERE id = %s
            LIMIT 1
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if not customer:

            return jsonify({
                "success": False,
                "message": "Customer not found"
            }), 404

        # ----------------------------------------------------
        # CHECK PRODUCT
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM products
            WHERE id = %s
            LIMIT 1
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if not product:

            return jsonify({
                "success": False,
                "message": "Product not found"
            }), 404

        # ----------------------------------------------------
        # CHECK STOCK
        # ----------------------------------------------------

        stock = product.get("stock", 0)

        try:
            stock = int(stock)
        except (ValueError, TypeError):
            stock = 0

        if stock < quantity:

            return jsonify({
                "success": False,
                "message": "Insufficient product stock"
            }), 400

        # ----------------------------------------------------
        # GET PRODUCT PRICE
        # ----------------------------------------------------

        price = product.get("price")

        if price is None:

            return jsonify({
                "success": False,
                "message": "Product price is not configured"
            }), 500

        total_amount = float(price) * quantity

        # ----------------------------------------------------
        # CREATE ORDER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO orders
            (
                customer_id,
                status
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                customer_id,
                "pending"
            )
        )

        order_id = cursor.lastrowid

        # ----------------------------------------------------
        # CREATE ORDER ITEM
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO order_items
            (
                order_id,
                product_id,
                quantity,
                price
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                order_id,
                product_id,
                quantity,
                price
            )
        )

        # ----------------------------------------------------
        # UPDATE STOCK
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE products
            SET stock = stock - %s
            WHERE id = %s
            """,
            (
                quantity,
                product_id
            )
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order": {
                "id": order_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "quantity": quantity,
                "price": float(price),
                "total_amount": total_amount,
                "status": "pending"
            }
        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to create order",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# SAVE DELIVERY LOCATION
# ============================================================

@app.route("/api/delivery-location", methods=["POST"])
def save_delivery_location():

    connection = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "No delivery location data received"
            }), 400

        customer_id = data.get("customer_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        address = data.get("address", "")

        # ----------------------------------------------------
        # VALIDATE CUSTOMER
        # ----------------------------------------------------

        try:
            customer_id = int(customer_id)
        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Invalid customer_id"
            }), 400

        if customer_id <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid customer_id"
            }), 400

        if latitude is None or longitude is None:

            return jsonify({
                "success": False,
                "message": "Latitude and longitude are required"
            }), 400

        try:

            latitude = float(latitude)
            longitude = float(longitude)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Invalid latitude or longitude"
            }), 400

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # CHECK CUSTOMER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM customers
            WHERE id = %s
            LIMIT 1
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if not customer:

            return jsonify({
                "success": False,
                "message": "Customer not found"
            }), 404

        # ----------------------------------------------------
        # SAVE LOCATION
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO delivery_locations
            (
                customer_id,
                latitude,
                longitude,
                address
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                customer_id,
                latitude,
                longitude,
                address
            )
        )

        connection.commit()

        location_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Delivery location saved successfully",
            "delivery_location": {
                "id": location_id,
                "customer_id": customer_id,
                "latitude": latitude,
                "longitude": longitude,
                "address": address
            }
        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to save delivery location",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CREATE CUSTOMER MESSAGE
# ============================================================

@app.route("/api/messages", methods=["POST"])
def create_message():

    connection = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "No message data received"
            }), 400

        customer_id = data.get("customer_id")
        message = str(data.get("message", "")).strip()

        # ----------------------------------------------------
        # VALIDATE CUSTOMER ID
        # ----------------------------------------------------

        try:
            customer_id = int(customer_id)
        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Invalid customer_id"
            }), 400

        if customer_id <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid customer_id"
            }), 400

        if not message:

            return jsonify({
                "success": False,
                "message": "Message is required"
            }), 400

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # CHECK CUSTOMER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM customers
            WHERE id = %s
            LIMIT 1
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if not customer:

            return jsonify({
                "success": False,
                "message": "Customer not found"
            }), 404

        # ----------------------------------------------------
        # INSERT MESSAGE
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO messages
            (
                customer_id,
                message
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                customer_id,
                message
            )
        )

        connection.commit()

        message_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Message sent successfully",
            "data": {
                "id": message_id,
                "customer_id": customer_id,
                "message": message
            }
        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to send message",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CREATE CUSTOMER FEEDBACK
# ============================================================

@app.route("/api/feedback", methods=["POST"])
def create_feedback():

    connection = None
    cursor = None

    try:

        # ----------------------------------------------------
        # GET JSON DATA
        # ----------------------------------------------------

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "No feedback data received"
            }), 400

        # ----------------------------------------------------
        # GET FIELDS
        # ----------------------------------------------------

        customer_id = data.get("customer_id")
        order_id = data.get("order_id")
        rating = data.get("rating")
        comment = data.get("comment")

        # ----------------------------------------------------
        # CHECK REQUIRED FIELDS
        # ----------------------------------------------------

        if customer_id is None:

            return jsonify({
                "success": False,
                "message": "customer_id is required"
            }), 400

        if order_id is None:

            return jsonify({
                "success": False,
                "message": "order_id is required"
            }), 400

        if rating is None:

            return jsonify({
                "success": False,
                "message": "rating is required"
            }), 400

        # ----------------------------------------------------
        # CONVERT NUMERIC VALUES
        # ----------------------------------------------------

        try:

            customer_id = int(customer_id)
            order_id = int(order_id)
            rating = int(rating)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": (
                    "customer_id, order_id and rating "
                    "must be valid numbers"
                )
            }), 400

        # ----------------------------------------------------
        # VALIDATE CUSTOMER ID
        # ----------------------------------------------------

        if customer_id <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid customer_id"
            }), 400

        # ----------------------------------------------------
        # VALIDATE ORDER ID
        # ----------------------------------------------------

        if order_id <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid order_id"
            }), 400

        # ----------------------------------------------------
        # VALIDATE RATING
        # ----------------------------------------------------

        if rating < 1 or rating > 5:

            return jsonify({
                "success": False,
                "message": "Rating must be between 1 and 5"
            }), 400

        # ----------------------------------------------------
        # CLEAN COMMENT
        # ----------------------------------------------------

        if comment is None:
            comment = ""
        else:
            comment = str(comment).strip()

        # ----------------------------------------------------
        # CONNECT DATABASE
        # ----------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # CHECK CUSTOMER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                name
            FROM customers
            WHERE id = %s
            LIMIT 1
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if not customer:

            return jsonify({
                "success": False,
                "message": "Customer not found"
            }), 404

        # ----------------------------------------------------
        # CHECK ORDER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                customer_id,
                status
            FROM orders
            WHERE id = %s
            LIMIT 1
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if not order:

            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        # ----------------------------------------------------
        # CHECK ORDER BELONGS TO CUSTOMER
        # ----------------------------------------------------

        if int(order["customer_id"]) != customer_id:

            return jsonify({
                "success": False,
                "message": (
                    "This order does not belong "
                    "to this customer"
                )
            }), 403

        # ----------------------------------------------------
        # CHECK ORDER STATUS
        # ----------------------------------------------------

        if str(order["status"]).lower() != "delivered":

            return jsonify({
                "success": False,
                "message": (
                    "Feedback can only be submitted "
                    "for delivered orders"
                )
            }), 400

        # ----------------------------------------------------
        # CHECK EXISTING FEEDBACK
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                verification_status
            FROM feedback
            WHERE customer_id = %s
            AND order_id = %s
            LIMIT 1
            """,
            (
                customer_id,
                order_id
            )
        )

        existing_feedback = cursor.fetchone()

        if existing_feedback:

            return jsonify({
                "success": False,
                "message": (
                    "Feedback has already been "
                    "submitted for this order"
                ),
                "feedback": {
                    "id": existing_feedback["id"],
                    "verification_status":
                        existing_feedback["verification_status"]
                }
            }), 409

        # ----------------------------------------------------
        # INSERT FEEDBACK
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO feedback
            (
                customer_id,
                order_id,
                rating,
                comment,
                verification_status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                customer_id,
                order_id,
                rating,
                comment,
                "pending"
            )
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        connection.commit()

        feedback_id = cursor.lastrowid

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback": {
                "id": feedback_id,
                "customer_id": customer_id,
                "order_id": order_id,
                "rating": rating,
                "comment": comment,
                "verification_status": "pending"
            }
        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to submit feedback",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RUN FLASK SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

