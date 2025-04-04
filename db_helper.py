import mysql.connector

def get_order_status(order_id: int):
    try:
        # Establish a new database connection
        with mysql.connector.connect(
            host="localhost",
            user="root",
            password="OMdw@$123",
            database="pandeyji_eatery"
        ) as cnx:
            with cnx.cursor(dictionary=True) as cursor:  # Use dictionary cursor for better readability
                # Execute query
                query = "SELECT status FROM order_tracking WHERE order_id = %s"
                cursor.execute(query, (order_id,))
                result = cursor.fetchone()  # Fetch single record

                # Check if result exists
                if result:
                    return result.get("status", "Order ID not found")  # Safer access
                return "Order ID not found"

    except mysql.connector.Error as err:
        print(f"Database error: {err}")  # Log the actual MySQL error
        return "Database error occurred"

def insert_order_item(food_item, quantity, order_id):
    try:
        with mysql.connector.connect(
            host="localhost",
            user="root",
            password="OMdw@$123",
            database="pandeyji_eatery"
        ) as cnx:
            with cnx.cursor() as cursor:
                # Call the stored procedure
                cursor.callproc('insert_order_item', (food_item, quantity, order_id))
                cnx.commit()
                print("Order item inserted successfully")
                return 1  # Success

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")
        return -1  # Failure

    except Exception as e:
        print(f"An error occurred: {e}")
        return -1  # Failure

def get_next_order_id():
    try:
        with mysql.connector.connect(
            host="localhost",
            user="root",
            password="OMdw@$123",
            database="pandeyji_eatery"
        ) as cnx:
            with cnx.cursor() as cursor:
                query = "SELECT MAX(order_id) FROM orders"
                cursor.execute(query)
                result = cursor.fetchone()[0]

                # Return the next order ID
                return 1 if result is None else result + 1

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return -1  # Return -1 if there is an error

def get_total_order_price(order_id):
    try:
        with mysql.connector.connect(
            host="localhost",
            user="root",
            password="OMdw@$123",
            database="pandeyji_eatery"
        ) as cnx:
            with cnx.cursor() as cursor:
                query = "SELECT get_total_order_price(%s)"
                cursor.execute(query, (order_id,))
                result = cursor.fetchone()

                return result[0] if result else 0  # Return total price or 0 if no result

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return -1  # Return -1 if an error occurs

def insert_order_tracking(order_id, status):
    try:
        with mysql.connector.connect(
            host="localhost",
            user="root",
            password="OMdw@$123",
            database="pandeyji_eatery"
        ) as cnx:
            with cnx.cursor() as cursor:
                insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
                cursor.execute(insert_query, (order_id, status))
                cnx.commit()

                print("Order tracking inserted successfully")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return -1

