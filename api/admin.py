# admin.py

from django.contrib import admin
from .models import Customer,Loan

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'first_name', 'last_name', 'phone_number', 'monthly_salary', 'approved_limit')
    list_editable = ('phone_number', 'monthly_salary', 'approved_limit')
    search_fields = ('first_name', 'last_name', 'phone_number')
    list_filter = ('age',)

class LoanAdmin(admin.ModelAdmin):
    list_display = ("loan_id","customer_id","loan_amount")

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Loan, LoanAdmin)
