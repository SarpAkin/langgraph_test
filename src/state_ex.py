from typing import Dict, Any, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. Define the State
# This structure passes data between your nodes.
class OrderState(TypedDict):
    item_id: str
    quantity: int
    price_per_unit: float
    is_digital: bool
    
    # Tracked/Modified by nodes
    in_stock: bool
    total_cost: float
    status: str

# 2. Define the Nodes (Regular Python Functions)
def validate_inventory(state: OrderState) -> Dict[str, Any]:
    print("--- Validating Inventory ---")
    # Simulating a database check
    # Let's pretend "item_404" is out of stock, others are available
    if state["item_id"] == "item_404":
        return {"in_stock": False, "status": "Inventory Check Failed"}
    
    initial_total = state["quantity"] * state["price_per_unit"]
    return {"in_stock": True, "total_cost": initial_total}

def apply_discount(state: OrderState) -> Dict[str, Any]:
    print("--- Processing Pricing & Discounts ---")
    current_total = state["total_cost"]
    
    # If the order is over $100, give a 10% discount
    if current_total > 100.0:
        print("    High-value order detected. Applying 10% discount!")
        current_total *= 0.9
        
    return {"total_cost": current_total, "status": "Pricing Finalized"}

def ship_package(state: OrderState) -> Dict[str, Any]:
    print("--- Dispatching Physical Shipping ---")
    return {"status": f"Shipped physical item to logistics. Charged: ${state['total_cost']:.2f}"}

def digital_delivery(state: OrderState) -> Dict[str, Any]:
    print("--- Generating Download Link ---")
    return {"status": f"Email sent with digital key. Charged: ${state['total_cost']:.2f}"}

def reject_order(state: OrderState) -> Dict[str, Any]:
    print("--- Rejecting Order ---")
    return {"status": "Order Rejected: Item Out of Stock"}

# 3. Define Conditional Routing Functions
# These determine the next step by looking at the current state.
def route_stock_check(state: OrderState) -> Literal["apply_discount", "reject_order"]:
    if state["in_stock"]:
        return "apply_discount"
    return "reject_order"

def route_delivery_type(state: OrderState) -> Literal["digital_delivery", "ship_package"]:
    if state["is_digital"]:
        return "digital_delivery"
    return "ship_package"

# 4. Construct the Graph
builder = StateGraph(OrderState)

# Add Nodes
builder.add_node("validate_inventory", validate_inventory)
builder.add_node("apply_discount", apply_discount)
builder.add_node("ship_package", ship_package)
builder.add_node("digital_delivery", digital_delivery)
builder.add_node("reject_order", reject_order)

# Add Edges & Conditional Edges
builder.add_edge(START, "validate_inventory")

# First Conditional Edge: Inventory Validation -> Discount or Rejection
builder.add_conditional_edges(
    "validate_inventory",
    route_stock_check,
    {
        "apply_discount": "apply_discount",
        "reject_order": "reject_order"
    }
)

# Second Conditional Edge: Discount -> Delivery Routing
builder.add_conditional_edges(
    "apply_discount",
    route_delivery_type,
    {
        "digital_delivery": "digital_delivery",
        "ship_package": "ship_package"
    }
)

# Normal Edges to Terminal Node
builder.add_edge("ship_package", END)
builder.add_edge("digital_delivery", END)
builder.add_edge("reject_order", END)

# Compile the Graph
order_pipeline = builder.compile()


initial_state_a = {
    "item_id": "item_404",
    "quantity": 2,
    "price_per_unit": 80.0,
    "is_digital": False
}

result_a = order_pipeline.invoke(initial_state_a)
print(f"Final Status: {result_a['status']}\n")