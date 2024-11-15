from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer,Loan
from .serializers import CustomerSerializer,LoanSerializer,LoanEligibilityRequestSerializer,LoanEligibilityResponseSerializer
from django.db.models import Sum

from datetime import datetime
from decimal import Decimal
from django.db.models import Max
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from django.http import JsonResponse
from CreditApprovalSystem.tasks import register_customers_from_file,bulk_loan_upload_task
import os


def start_customer_registration(request):
    register_customers_from_file.delay()
    print("Hello")
    return JsonResponse({'status': 'Customer registration task started'})

def start_bulk_loan_upload(request):
    try:
        bulk_loan_upload_task.delay()
        return JsonResponse({'status': 'Bulk loan upload task started successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'Failed to start the task: {str(e)}'}, status=500)

class RegisterCustomerView(APIView):
    def post(self, request):
        data = request.data
        monthly_salary = data.get('monthly_income')
        if data.get('approved_limit'):
            approved_limit = data.get('approved_limit')
        else:
            approved_limit = round(36 * monthly_salary, -5)  
        customer = Customer.objects.create(
            customer_id = data.get('customer_id'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            age=data.get('age'),
            monthly_salary=monthly_salary,
            approved_limit=approved_limit,
            phone_number=data.get('phone_number')
        )
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MakeLoanAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoanSerializer(data=request.data)
        if serializer.is_valid():

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


def calculate_credit_score(customer):
    current_year = datetime.now().year
    score = 0
    
    # 1. Past Loans Paid on Time (increment score for loans paid on time)
    loans_paid_on_time = Loan.objects.filter(customer_id=customer, emi_paid_on_time=True)
    score += loans_paid_on_time.count() * 5  # Example: 5 points per loan paid on time
    
    # 2. Number of loans taken in the past
    score += Loan.objects.filter(customer_id=customer).count() * 3  # Example: 3 points per loan
    
    # 3. Loan activity in the current year (if loan is taken or EMI paid)
    loans_current_year = Loan.objects.filter(customer_id=customer, start_date__year=current_year)
    score += loans_current_year.count() * 2  # Example: 2 points per loan in the current year
    
    # 4. Loan Approved Volume
    total_loan_volume = Loan.objects.filter(customer_id=customer).aggregate(Sum('loan_amount'))['loan_amount__sum']
    if total_loan_volume:
        score += total_loan_volume / 100000  # Example: 1 point per 100K loan volume
    
    # 5. If sum of current loans exceeds approved limit, score becomes 0
    total_current_loans = loans_current_year.aggregate(Sum('loan_amount'))['loan_amount__sum']
    if total_current_loans and total_current_loans > customer.approved_limit:
        score = 0
    
    return score

def get_monthly_installment(loan_amount, interest_rate, tenure):
    rate = interest_rate / (12 * 100)  
    emi = (loan_amount * rate * (1 + rate) ** tenure) / ((1 + rate) ** tenure - 1)
    return emi

class LoanEligibilityCheckView(APIView):
    def post(self, request):
        serializer = LoanEligibilityRequestSerializer(data=request.data)
        if serializer.is_valid():
            customer_id = serializer.validated_data['customer_id']
            loan_amount = serializer.validated_data['loan_amount']
            interest_rate = serializer.validated_data['interest_rate']
            tenure = serializer.validated_data['tenure']

            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

            credit_score = calculate_credit_score(customer)

            total_current_emis = Loan.objects.filter(customer_id=customer).aggregate(Sum('monthly_repayment'))['monthly_repayment__sum']
            if total_current_emis and total_current_emis > Decimal('0.5') * customer.monthly_salary:
                approval = False
            else:
                approval = True

            if credit_score > 50:
                if interest_rate <= 12:
                    interest_rate = 12
            elif 50 > credit_score > 30:
                if interest_rate <= 12:
                    interest_rate = 12
            elif 30 > credit_score > 10:
                if interest_rate <= 16:
                    interest_rate = 16
            else:
                approval = False  
            monthly_installment = get_monthly_installment(loan_amount, interest_rate, tenure)


            response_data = {
                'customer_id': customer_id,
                'approval': approval,
                'interest_rate': interest_rate,
                'corrected_interest_rate': interest_rate if approval else interest_rate,
                'tenure': tenure,
                'monthly_installment': monthly_installment,
            }

            return Response(response_data)


        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ViewLoanDetails(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(loan_id=loan_id)

            is_approved = loan.loan_amount > 0  

            response_data = {
                "loan_id": loan.loan_id,
                "customer": {
                    "id": loan.customer_id.customer_id,
                    "first_name": loan.customer_id.first_name,
                    "last_name": loan.customer_id.last_name,
                    "phone_number": loan.customer_id.phone_number,
                    "age": loan.customer_id.age,
                },
                "loan_amount": float(loan.loan_amount),
                "interest_rate": float(loan.interest_rate),
                "is_approved": is_approved,
                "monthly_installment": float(loan.monthly_repayment),
                "tenure": loan.tenure,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Loan.DoesNotExist:
            return Response({"error": "Loan not found."}, status=status.HTTP_404_NOT_FOUND)

class ViewCustomerLoans(APIView):
    def get(self, request, customer_id):
        loans = Loan.objects.filter(customer_id=customer_id)

        if not loans.exists():
            return Response({"error": "No loans found for this customer."}, status=status.HTTP_404_NOT_FOUND)

        loan_data = []
        for loan in loans:
            is_approved = loan.loan_amount > 0  
            repayments_left = loan.tenure - (loan.tenure - loan.monthly_repayment)  

            loan_data.append({
                "loan_id": loan.loan_id,
                "loan_amount": float(loan.loan_amount),
                "is_approved": is_approved,
                "interest_rate": float(loan.interest_rate),
                "monthly_installment": float(loan.monthly_repayment),
                "repayments_left": repayments_left
            })

        return Response(loan_data, status=status.HTTP_200_OK)
    
class CreateLoanView(APIView):
    def post(self, request):
        serializer = LoanEligibilityRequestSerializer(data=request.data)
        if serializer.is_valid():
            customer_id = serializer.validated_data['customer_id']
            loan_amount = serializer.validated_data['loan_amount']
            interest_rate = serializer.validated_data['interest_rate']
            tenure = serializer.validated_data['tenure']
            
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response({"message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

            eligibility_check_view = LoanEligibilityCheckView()
            eligibility_data = eligibility_check_view.post(request)
            if not eligibility_data.data['approval']:
                return Response({
                    "loan_id": None,
                    "customer_id": customer_id,
                    "loan_approved": False,
                    "message": "Loan not approved due to eligibility criteria",
                    "monthly_installment": None
                }, status=status.HTTP_400_BAD_REQUEST)

            monthly_installment = eligibility_data.data['monthly_installment']
            corrected_interest_rate = eligibility_data.data['corrected_interest_rate']
            
            max_loan_id = Loan.objects.aggregate(Max('loan_id'))['loan_id__max'] or 0
            new_loan_id = max_loan_id + 1

            start_date = timezone.now()

            # Here I have made certain Assumptions:
            # 1. The start date is suppose to be of the current time when the create-loan is getting hit
            # 2. For the end date I have assumed the tenure is in months and have added the tenure number of months to the end date.
            # 3. I have given a default value to the emi_paid_on_time as 1.
            loan = Loan.objects.create(
                loan_id=new_loan_id,
                customer_id=customer,
                loan_amount=Decimal(loan_amount),
                interest_rate=Decimal(corrected_interest_rate),
                monthly_repayment=Decimal(monthly_installment),
                tenure=tenure,
                start_date=start_date,
                end_date=start_date + relativedelta(months=tenure),
                emi_paid_on_time = 1,
            )

            return Response({
                "loan_id": loan.loan_id,
                "customer_id": customer_id,
                "loan_approved": True,
                "message": "Loan approved",
                "monthly_installment": float(monthly_installment)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)