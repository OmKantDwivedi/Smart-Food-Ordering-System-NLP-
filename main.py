from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

# Move this before function definitions to prevent NameError
inprogress_order = {}

@app.post("/")  # Accept POST requests
async def handle_request(request: Request):
    payload = await request.json()

    # Extract intent and parameters
    intent = payload["queryResult"]["intent"]["displayName"]
    parameters = payload["queryResult"].get("parameters", {})  # Use .get() to prevent KeyError
    output_contexts = payload["queryResult"].get("outputContexts", [])

    # Ensure output_contexts is not empty before accessing index 0
    if not output_contexts:
        return JSONResponse(content={"fulfillmentText": "Session information missing."})

    session_id = generic_helper.extract_session_id(output_contexts[0].get('name', ""))

    # Intent handler dictionary
    intent_handler_dict = {
        "track.order - context: ongoing-tracking": track_order,
        "order.add - context: ongoing-order": add_to_order,
        "Order.complete - context: ongoing-order": complete_order,
        "order.remove - context: ongoing-order": remove_from_order
    }

    # Safely get the handler function
    handler_function = intent_handler_dict.get(intent)

    if handler_function:
        return handler_function(parameters, session_id)
    else:
        return JSONResponse(content={"fulfillmentText": "Intent not recognized."})
    
def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_order:
        return JSONResponse(content={
            "fulfillmentText":"I'm having a trouble finding your order. Sorry! Can you place a new order."
        })
    current_order = inprogress_order[session_id]
    food_items= parameters["food-item"]

    removed_items =[]
    no_such_items =[]

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]
    if len(removed_items) > 0:
        fulfillment_text =f'removed{",".join(removed_items)} from your order'
    
    if len(no_such_items) > 0:
        fulfillment_text = f'Your current order does not have {",". join(no_such_items)}'
    
    if len(current_order.keys()) == 0:
        fulfillment_text += "Your order is empty!"
    else:
        order_str =generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f"Here is what left in your order: {order_str} "
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def add_to_order(parameters: dict, session_id: str):
    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't understand. Can you please specify food items and quantities clearly?"
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_order:
            current_food_dict = inprogress_order[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_order[session_id] = current_food_dict
        else:
            inprogress_order[session_id] = new_food_dict
        
        order_str = generic_helper.get_str_from_food_dict(inprogress_order[session_id])

        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_order:
        fulfillment_text = "I'm having trouble finding your order. Sorry! Can you place a new order?"
    else:
        order = inprogress_order[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. Please place a new order again."
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome! We have placed your order. Here is your order ID: #{order_id}. Your order total is {order_total}, which you can pay at the time of delivery!"

        del inprogress_order[session_id]  # ✅ Remove order after processing

    return JSONResponse(content={"fulfillmentText": fulfillment_text})  # ✅ Missing return statement added

def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()
    success = False  # ✅ Track if any insertions are successful

    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(food_item, quantity, next_order_id)
    
        if rcode != -1:  # ✅ At least one successful insertion
            success = True

    if not success:
        return -1  # ✅ Return failure only if all items fail

    db_helper.insert_order_tracking(next_order_id, "in progress")
    return next_order_id

def track_order(parameters: dict, session_id: str):
    # Safely get order_id from parameters
    order_id = parameters.get("order_id")

    if not order_id:
        return JSONResponse(content={"fulfillmentText": "Order ID is in-transit."})

    try:
        order_id = int(order_id)  # Ensure it's an integer
    except (ValueError, TypeError):  # ✅ Handle non-string or None cases
        return JSONResponse(content={"fulfillmentText": "Invalid Order ID format."})

    # Fetch order status from the database
    order_status = db_helper.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for Order ID {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with Order ID {order_id}"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})




