import streamlit as st
import pandas as pd
from datetime import datetime
from db_helper import *
from invoice import create_pdf        

st.set_page_config(page_title="FRESH Sales Manager", layout="wide")
create_tables()

# Initialize Session States
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "cart" not in st.session_state: st.session_state.cart = []

# --- Authentication ---
if not st.session_state.logged_in:
    t1, t2 = st.tabs(["Login", "Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In", width='stretch'):
            user = login_user(u, p)
            if user:
                st.session_state.logged_in, st.session_state.username, st.session_state.user_role = True, user[1], user[3]
                st.rerun()
            else: st.error("Invalid Login")
    with t2:
        nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
        nr = st.selectbox("Role", ["Staff", "Admin"])
        if st.button("Register"):
            if register_user(nu, np, nr): st.success("Created!")
    st.stop()

# --- Sidebar ---
st.sidebar.title(f"User: {st.session_state.username}")
menu = ["Dashboard", "Inventory", "Customers", "New Sale"]
if st.session_state.user_role == "Admin": menu.append("Logs")
choice = st.sidebar.radio("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.cart = []
    st.rerun()

# --- Inventory ---
if choice == "Inventory":
    st.title("📦 Inventory")

    @st.dialog("Edit Product")
    def edit_p(p):
        nc = st.text_input("Code", p[1])
        nn = st.text_input("Name", p[2])
        ncp = st.number_input("Cost", value=p[3])
        nsp = st.number_input("Sell", value=p[4])
        nst = st.number_input("Stock", value=p[5])
        if st.button("Update"):
            update_product(st.session_state.username, p[0], nc, nn, ncp, nsp, nst)
            st.rerun()

    with st.expander("Add Product"):
        with st.form("ap"):
            c1, c2 = st.columns(2)
            code, name = c1.text_input("Code"), c2.text_input("Name")
            cp, sp, stock = st.number_input("Cost Price"), st.number_input("Selling Price"), st.number_input("Stock")
            if st.form_submit_button("Save"):
                add_product(st.session_state.username, code, name, cp, sp, stock); st.rerun()

    for p in get_products():
        cols = st.columns([1, 3, 2, 1, 1])
        cols[0].write(f"`{p[1]}`")
        cols[1].write(p[2])
        cols[2].write(f"Rs.{p[4]} (Qty: {p[5]})")
        if cols[3].button("📝", key=f"e_{p[0]}"): edit_p(p)
        if st.session_state.user_role == "Admin" and cols[4].button("🗑️", key=f"d_{p[0]}"):
            delete_product(st.session_state.username, p[0], p[2]); st.rerun()

# --- Customers ---
elif choice == "Customers":
    st.title("👥 Customers")

    @st.dialog("Edit Customer")
    def edit_c(c):
        nn = st.text_input("Name", c[1])
        nco = st.text_input("Contact", c[2])
        if st.button("Update"):
            update_customer(st.session_state.username, c[0], nn, nco)
            st.rerun()

    with st.expander("Add Customer"):
        with st.form("ac"):
            cn, cc = st.text_input("Name"), st.text_input("Contact")
            if st.form_submit_button("Save"):
                add_customer(st.session_state.username, cn, cc); st.rerun()

    for c in get_customers():
        cols = st.columns([3, 3, 1, 1])
        cols[0].write(c[1])
        cols[1].write(c[2])
        if cols[2].button("📝", key=f"ec_{c[0]}"): edit_c(c)
        if st.session_state.user_role == "Admin" and cols[3].button("🗑️", key=f"dc_{c[0]}"):
            delete_customer(st.session_state.username, c[0], c[1]); st.rerun()

# --- POS (New Sale) ---
elif choice == "New Sale":
    st.title("🛒 Point of Sale")
    prods, custs = get_products(), get_customers()
    
    if prods and custs:
        c_sel = st.selectbox("Customer", [c[1] for c in custs])
        p_sel = st.selectbox("Product", [f"{p[1]} | {p[2]}" for p in prods])
        item = next(p for p in prods if f"{p[1]} | {p[2]}" == p_sel)
        qty = st.number_input("Quantity", 1, item[5])

        if st.button("Add to Cart", width='stretch'):
            st.session_state.cart.append({
                "id": item[0], "code": item[1], "name": item[2], 
                "qty": qty, "total": item[4] * qty * 1.18 # 18% GST added
            })
            st.toast("Added!")

        if st.session_state.cart:
            st.subheader("Current Cart")
            
            # Create a header row for the cart
            h_cols = st.columns([1, 2, 1, 1, 1])
            h_cols[0].write("**Code**")
            h_cols[1].write("**Name**")
            h_cols[2].write("**Qty**")
            h_cols[3].write("**Total (inc. GST)**")
            h_cols[4].write("**Action**")

            # Iterate through cart with index to allow deletion
            for idx, item in enumerate(st.session_state.cart):
                cols = st.columns([1, 2, 1, 1, 1])
                cols[0].write(item["code"])
                cols[1].write(item["name"])
                cols[2].write(str(item["qty"]))
                cols[3].write(f"₹{item['total']:.2f}")
                
                # Delete button for each specific row
                if cols[4].button("❌", key=f"del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()

            st.divider()
            
            # Checkout Section
            if st.button("Finish & Download Invoice", type="primary", width='stretch'):
                inv_id = f"F-{datetime.now().strftime('%H%M%S')}"
                date_s = datetime.now().strftime("%d %b %Y")
                
                pdf_data = []
                for entry in st.session_state.cart:
                    gross_u = entry["total"] / entry["qty"]
                    net_u = gross_u / 1.18
                    pdf_data.append([entry["code"], entry["name"], entry["qty"], net_u, gross_u, entry["total"]])
                    add_sale(st.session_state.username, entry["id"], entry["name"], entry["qty"], entry["total"], datetime.now().strftime("%Y-%m-%d"))
                
                path = create_pdf(inv_id, date_s, c_sel, pdf_data)
                with open(path, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=f"{inv_id}.pdf")
                
                # Clear cart and refresh
                st.session_state.cart = []
                st.success("Sale completed successfully!")
                
# --- Dashboard & Logs ---
# --- Dashboard & Analytics ---
elif choice == "Dashboard":
    st.title("📈 Business Intelligence Dashboard")
    data = get_sales_analytics()
    
    if data:
        df = pd.DataFrame(data, columns=["Date", "Item", "Qty", "Revenue", "Cost"])
        df["Profit"] = df["Revenue"] - df["Cost"]
        
        # 1. Key Metrics Row
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"₹{df['Revenue'].sum():,.2f}")
        col2.metric("Total Profit", f"₹{df['Profit'].sum():,.2f}", 
                    delta=f"{(df['Profit'].sum()/df['Revenue'].sum())*100:.1f}% Margin")
        
        # 2. Sales Prediction Logic
        from prediction import predict_sales
        raw_sales = get_connection().execute("SELECT * FROM sales").fetchall()
        prediction = predict_sales(raw_sales)
        
        if isinstance(prediction, (int, float)):
            col3.metric("Next Day Forecast", f"₹{prediction:,.2f}", help="Linear Regression Prediction")
        else:
            col3.info("Prediction: Collect more data (5+ sales)")

        # 3. Visualizations
        tab_rev, tab_stock = st.tabs(["Revenue Trends", "Inventory Status"])
        
        with tab_rev:
            st.subheader("Daily Revenue Performance")
            chart_data = df.groupby("Date")[["Revenue", "Profit"]].sum()
            st.line_chart(chart_data)

        with tab_stock:
            st.subheader("Low Stock Alerts")
            prods = get_products()
            # Filter products with stock less than 10
            low_stock = [p for p in prods if p[5] < 10]
            if low_stock:
                for p in low_stock:
                    st.warning(f"⚠️ {p[2]} (Code: {p[1]}) is low on stock: {p[5]} remaining")
            else:
                st.success("All items are well-stocked!")
    else:
        st.info("No sales data available yet to generate insights.")
        
# --- Logs (Add this at the end of app.py) ---
elif choice == "Logs":
    st.title("📜 System Logs")
    if st.session_state.user_role == "Admin":
        logs = get_logs()
        if logs:
            log_df = pd.DataFrame(logs, columns=["ID", "Timestamp", "User", "Action", "Details"])
            # Updated with the new width parameter
            st.dataframe(log_df, width='stretch') 
        else:
            st.info("No logs found.")
    else:
        st.error("Access Denied: Admins only.")
