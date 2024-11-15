from django.db import models

class Customer(models.Model):
    customer_id = models.IntegerField(unique=True, primary_key=True)  
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    age = models.IntegerField()
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2)
    approved_limit = models.IntegerField()
    current_debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

class Loan(models.Model):
    loan_id = models.IntegerField(unique=True, primary_key=True)  
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=4, decimal_places=2)
    monthly_repayment = models.DecimalField(max_digits=10, decimal_places=2)
    emi_paid_on_time = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
