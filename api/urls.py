from django.urls import path
from .views import RegisterCustomerView,MakeLoanAPIView,LoanEligibilityCheckView,ViewLoanDetails,ViewCustomerLoans,CreateLoanView
# start_bulk_upload
from .views import start_customer_registration,start_bulk_loan_upload


urlpatterns = [
    path('register', RegisterCustomerView.as_view(), name='register'),
    path('make-loan/', MakeLoanAPIView.as_view(), name='make-loan'),
    path('check-eligibility', LoanEligibilityCheckView.as_view(), name='check-eligibility'),
    path('view-loan/<int:loan_id>/', ViewLoanDetails.as_view(), name='view-loan'),
    path('view-loans/<int:customer_id>/', ViewCustomerLoans.as_view(), name='view-customer-loans'),
    path('create-loan/', CreateLoanView.as_view(), name='create-loan'),

    path('bulk-upload-customer/', start_customer_registration, name='bulk-upload-customer'),
    path('start-bulk-loan-upload/', start_bulk_loan_upload, name='start_bulk_loan_upload'),


]
