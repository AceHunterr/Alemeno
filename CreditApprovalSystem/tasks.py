from celery import shared_task
import pandas as pd
from django.test import RequestFactory
import requests
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

@shared_task
def register_customers_from_file():
    file_path = "customer_data.xlsx"
    
    def load_customer_data(file_path):
        data = pd.read_excel(file_path)
        data.columns = data.columns.str.strip()
        return data

    def register_customer(row):
        from api.views import RegisterCustomerView  
        payload = {
            'customer_id': row["Customer ID"],
            "first_name": row["First Name"],
            "last_name": row["Last Name"],
            "age": row["Age"],
            "monthly_income": row["Monthly Salary"],
            "phone_number": row["Phone Number"],
            "approved_limit": row["Approved Limit"]
        }
        
        # Simulate a request to pass to the view
        request = RequestFactory().post("/api/register", data=payload)
        view = RegisterCustomerView.as_view()

        try:
            response = view(request)
            if response.status_code != 201:
                print(f"Failed to register customer {row['First Name']} {row['Last Name']}: {response.data}")
        except Exception as e:
            print(f"Error registering customer {row['First Name']} {row['Last Name']}: {e}")

    # Load data and process each customer
    customer_data = load_customer_data(file_path)
    for _, row in customer_data.iterrows():
        register_customer(row)




def load_loan_data(file_path):
    data = pd.read_excel(file_path)
    return data

def format_date(date_str):
    if isinstance(date_str, pd.Timestamp):
        date_str = date_str.date()  

    try:
        return datetime.strptime(str(date_str), '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return None

@shared_task
def bulk_loan_upload_task():
    file_path = "loan_data_orig.xlsx"
    try:
        loan_data = load_loan_data(file_path)
        
        def register_loan(row):
            from api.views import MakeLoanAPIView
            payload = {
                'customer_id': row["Customer ID"],  
                'loan_id': row["Loan ID"],  
                'loan_amount': row["Loan Amount"], 
                'tenure': row["Tenure"],
                'interest_rate': row["Interest Rate"],
                'monthly_repayment': row["Monthly payment"],
                'emi_paid_on_time': row["EMIs paid on Time"],
                'start_date': format_date(row["Date of Approval"]),
                'end_date': format_date(row["End Date"])
            }
            logger.info(f"Uploading payload: {payload}")
            
            request = RequestFactory().post("/api/make-loan/", data=payload)
            view = MakeLoanAPIView.as_view()

            try:
                response = view(request)
                if response.status_code == 201:
                    logger.info(f"Successfully registered loan for Customer ID: {row['Customer ID']}, Loan ID: {row['Loan ID']}")
                else:
                    logger.error(f"Failed to register loan for Loan ID {row['Loan ID']}: {response.data}")
            except Exception as e:
                logger.error(f"Error registering loan for Loan ID {row['Loan ID']}: {e}")
        
        for _, row in loan_data.iterrows():
            register_loan(row)
            
    except Exception as e:
        logger.error(f"Error processing loan data file {file_path}: {e}")