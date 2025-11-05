import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Cab Aggregator", layout="wide")
st.title("Cab Aggregator — Demo UI")

# --- Globals ---
BACKEND = st.sidebar.text_input("Backend URL", value="http://127.0.0.1:8000")
st.sidebar.info("To test the 'nearest driver' logic, register a driver, log in as them, and use the 'Driver Panel' to set their location.")

# --- API Helper ---

def get_auth_headers():
    token = st.session_state.get("token")
    if not token:
        st.error("You must be logged in to perform this action.")
        return None
    return {"Authorization": f"Bearer {token}"}

# (This is the robust function from our previous fix)
def api_request(method, endpoint, **kwargs):
    url = f"{BACKEND}{endpoint}"
    try:
        r = requests.request(method, url, timeout=10, **kwargs)
        r.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        
        # Check if response is not empty before decoding
        if r.text:
            return r.json()
        return None # Handle empty successful responses
        
    except requests.exceptions.HTTPError as err:
        # Don't assume the error is JSON. Just print the raw text.
        st.error(f"HTTP Error: {err.response.text}")
    
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to backend at {url}. Is the backend server running?")
    
    except requests.exceptions.JSONDecodeError:
        st.error("Error: Received a non-JSON response from the backend.")
        
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
    
    return None

# --- Auth Pages ---


# --- API Helper ---
# (This is the robust function from our previous fix)
def api_request(method, endpoint, **kwargs):
    url = f"{BACKEND}{endpoint}"
    try:
        r = requests.request(method, url, timeout=10, **kwargs)
        r.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        
        # Check if response is not empty before decoding
        if r.text:
            return r.json()
        return None # Handle empty successful responses
        
    except requests.exceptions.HTTPError as err:
        # Don't assume the error is JSON. Just print the raw text.
        st.error(f"HTTP Error: {err.response.text}")
    
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to backend at {url}. Is the backend server running?")
    
    except requests.exceptions.JSONDecodeError:
        st.error("Error: Received a non-JSON response from the backend.")
        
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
    
    return None

# --- Auth Pages ---
def show_auth_pages():
    st.header("1. Authentication")
    
    login_tab, signup_tab = st.tabs(["Login", "Signup"])
    
    with login_tab:
        login_method = st.radio("Login with:", ("Password", "OTP"), key="login_method")
        
        if login_method == "Password":
            with st.form("login_pass_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.form_submit_button("Login"):
                    data = api_request("post", "/auth/login", json={"email": email, "password": password})
                    if data:
                        st.success("Logged in!")
                        st.session_state["token"] = data["access_token"]
                        st.session_state["email"] = email
                        st.experimental_rerun() # <-- FIX 1
                        
        if login_method == "OTP":
            email_otp = st.text_input("Email", key="login_email_otp")
            if st.button("Request Login OTP"):
                data = api_request("post", "/auth/login/otp_request", json={"email": email_otp})
                if data:
                    st.success("OTP sent! Check console (it's 123456).")
                    st.session_state.otp_login_email = email_otp
            
            if "otp_login_email" in st.session_state:
                with st.form("login_otp_form"):
                    otp = st.text_input("OTP")
                    if st.form_submit_button("Login with OTP"):
                        data = api_request("post", "/auth/login/otp_verify", json={"email": st.session_state.otp_login_email, "otp": otp})
                        if data:
                            st.success("Logged in!")
                            st.session_state["token"] = data["access_token"]
                            st.session_state["email"] = st.session_state.otp_login_email
                            del st.session_state.otp_login_email
                            st.experimental_rerun() # <-- FIX 2

    with signup_tab:
        if "user_to_verify" not in st.session_state:
            st.session_state.user_to_verify = None
            
        if not st.session_state.user_to_verify:
            with st.form("register_form"):
                name = st.text_input("Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                role = st.selectbox("Role", ["passenger", "driver", "admin"])
                if st.form_submit_button("Register"):
                    data = api_request("post", "/auth/register", json={"name":name,"email":email,"password":password,"role":role})
                    if data:
                        st.success("Registered! Check console for OTP (it's 123456).")
                        st.session_state.user_to_verify = email
                        st.experimental_rerun() # <-- FIX 3
        else:
            with st.form("verify_form"):
                st.info(f"Verifying: {st.session_state.user_to_verify}")
                otp = st.text_input("OTP")
                if st.form_submit_button("Verify Account"):
                    data = api_request("post", "/auth/verify_otp", json={"email": st.session_state.user_to_verify, "otp": otp})
                    if data:
                        st.success("Account verified! You can now login.")
                        st.session_state.user_to_verify = None
                        st.experimental_rerun() # <-- FIX 4

# --- Passenger Pages ---
def show_passenger_pages():
    st.header("2. Passenger Panel")
    book_tab, history_tab = st.tabs(["Book a Ride", "My Trips"])
    
    with book_tab:
        st.subheader("Book a Ride")
        with st.form("booking_form"):
            st.info("Using coordinates for robust geo-fencing. Example: Bangalore (12.97, 77.59) to Koramangala (12.93, 77.62)")
            col1, col2 = st.columns(2)
            pickup = col1.text_input("Pickup Location Name", "Bangalore")
            pickup_lat = col1.number_input("Pickup Latitude", value=12.9716, format="%.4f")
            pickup_lon = col1.number_input("Pickup Longitude", value=77.5946, format="%.4f")
            
            drop = col2.text_input("Drop Location Name", "Koramangala")
            drop_lat = col2.number_input("Drop Latitude", value=12.9345, format="%.4f")
            drop_lon = col2.number_input("Drop Longitude", value=77.6244, format="%.4f")
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Get Fare Estimate"):
                payload = {"pickup_lat": pickup_lat, "pickup_lon": pickup_lon, "drop_lat": drop_lat, "drop_lon": drop_lon}
                data = api_request("post", "/rides/estimate_fare", json=payload)
                if data:
                    st.success(f"Estimated Fare: ₹{data['estimated_fare']} ({data['distance_km']} km)")

            if c2.form_submit_button("Book Now"):
                headers = get_auth_headers()
                if headers:
                    payload = {
                        "email": st.session_state.get("email"),
                        "pickup": pickup, "drop": drop,
                        "pickup_lat": pickup_lat, "pickup_lon": pickup_lon,
                        "drop_lat": drop_lat, "drop_lon": drop_lon
                    }
                    data = api_request("post", "/rides/book", headers=headers, json=payload)
                    if data:
                        st.success(f"Ride booked! Ride ID: {data['ride_id']}")
                        st.json(data)

    with history_tab:
        st.subheader("My Trip History")
        if st.button("Show History"):
            headers = get_auth_headers()
            if headers:
                data = api_request("get", f"/rides/history/{st.session_state.get('email')}", headers=headers)
                if data:
                    st.session_state.trips = data
        
        if "trips" in st.session_state:
            for trip in st.session_state.trips:
                with st.expander(f"Trip {trip['id']}: {trip['pickup']} to {trip['drop']} ({trip['status']})"):
                    st.json(trip)
                    if trip['status'] == 'completed':
                        col1, col2 = st.columns(2)
                        if col1.button("View Receipt", key=f"rcpt_{trip['id']}"):
                            receipt = api_request("get", f"/payments/receipt/{trip['id']}", headers=get_auth_headers())
                            if receipt:
                                st.json(receipt)
                        
                        rating = col2.slider("Rate Driver", 1, 5, 5, key=f"rate_{trip['id']}")
                        if col2.button("Submit Rating", key=f"submit_{trip['id']}"):
                            r = api_request("post", "/rides/rate", headers=get_auth_headers(), json={"ride_id": trip['id'], "rating": rating})
                            if r:
                                st.success("Rating submitted!")

# --- Driver Pages ---
def show_driver_pages():
    st.header("3. Driver Panel")
    loc_tab, doc_tab = st.tabs(["Update Location", "Upload Documents"])
    
    with loc_tab:
        st.subheader("Update My Location")
        with st.form("driver_loc_form"):
            lat = st.number_input("My Latitude", value=12.9716, format="%.4f")
            lon = st.number_input("My Longitude", value=77.5946, format="%.4f")
            if st.form_submit_button("Update Location"):
                headers = get_auth_headers()
                if headers:
                    data = api_request("put", "/driver/location", headers=headers, json={"latitude": lat, "longitude": lon})
                    if data:
                        st.success("Location updated!")
    
    with doc_tab:
        st.subheader("Upload Documents")
        with st.form("doc_upload_form", clear_on_submit=True):
            doc_type = st.selectbox("Document Type", ["License", "VehicleRC", "Insurance"])
            uploaded_file = st.file_uploader("Choose a file (PDF)", type=["pdf"])
            if st.form_submit_button("Upload"):
                headers = get_auth_headers()
                if headers and uploaded_file:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    data = {"email": st.session_state.get("email"), "doc_type": doc_type}
                    # Use params for form-data, not json
                    resp = api_request("post", "/auth/upload_docs", headers=headers, data=data, files=files)
                    if resp:
                        st.success("Document uploaded!")

# --- Admin Pages ---
def show_admin_pages():
    st.header("4. Admin Panel")
    st.warning("You must be logged in as an Admin to use these features.")
    
    rep_tab, driver_tab, user_tab, log_tab = st.tabs(["Reports", "Driver Management", "User Management", "Audit Log"])

    with rep_tab:
        st.subheader("System Reports")
        if st.button("Get General Report"):
            data = api_request("get", "/admin/reports", headers=get_auth_headers())
            if data:
                st.json(data)
        
        if st.button("Get Peak Hours Report"):
            data = api_request("get", "/admin/reports/peak_hours", headers=get_auth_headers())
            if data:
                st.bar_chart(pd.DataFrame.from_dict(data, orient='index', columns=['ride_count']))

    with driver_tab:
        st.subheader("Driver Approval")
        if st.button("Fetch Pending Drivers"):
            data = api_request("get", "/admin/pending_drivers", headers=get_auth_headers())
            if data:
                st.session_state.pending_drivers = data
        
        if "pending_drivers" in st.session_state:
            for driver in st.session_state.pending_drivers:
                with st.container():
                    st.write(f"**Driver:** {driver['driver_name']} ({driver['driver_email']})")
                    st.write(f"**Doc:** {driver['doc_type']} (ID: {driver['doc_id']})")
                    if st.button("Approve", key=f"approve_{driver['doc_id']}"):
                        res = api_request("post", f"/admin/approve_driver/{driver['doc_id']}", headers=get_auth_headers())
                        if res:
                            st.success("Approved!")
                            del st.session_state.pending_drivers
                            st.experimental_rerun() # <-- FIX 5

    with user_tab:
        st.subheader("Block User")
        user_id_to_block = st.number_input("User ID to Block", min_value=1, step=1)
        if st.button("Block User", type="primary"):
            data = api_request("post", f"/admin/block_user/{user_id_to_block}", headers=get_auth_headers())
            if data:
                st.success(f"User {data['user_email']} blocked.")

    with log_tab:
        st.subheader("System Audit Log")
        if st.button("View Audit Log"):
            data = api_request("get", "/admin/audit_logs", headers=get_auth_headers())
            if data:
                st.dataframe(pd.DataFrame(data).sort_values(by="timestamp", ascending=False))

# --- Main App Logic ---
if "token" in st.session_state:
    st.sidebar.success(f"Logged in as: {st.session_state.get('email')}")
    if st.sidebar.button("Logout"):
        del st.session_state.token
        del st.session_state.email
        if "trips" in st.session_state: del st.session_state.trips
        st.experimental_rerun() # <-- FIX 6 (This was the line from your error)
    
    st.sidebar.markdown("---")
    page = st.sidebar.selectbox("Go to", ["Passenger Panel", "Driver Panel", "Admin Panel"])
    
    if page == "Passenger Panel":
        show_passenger_pages()
    elif page == "Driver Panel":
        show_driver_pages()
    elif page == "Admin Panel":
        show_admin_pages()
else:
    show_auth_pages()