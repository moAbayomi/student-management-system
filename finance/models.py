from django.db import models
from django.conf import settings
# Create your models here.

class FeeCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

class FeeStructure(models.Model):
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    class_level = models.ForeignKey('academics.Class', on_delete=models.CASCADE)
    session = models.ForeignKey('schools.AcademicSession', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)


    class Meta:
        unique_together = ('category', 'class_level', 'session')


class StudentInvoice(models.Model):
    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE)
    term = models.ForeignKey('schools.AcademicTerm', on_delete=models.CASCADE)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_fully_paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.balance = self.total_amount - self.paid_amount
        self.is_fully_paid = self.balance <= 0
        super().save(*args, **kwargs)


class PaymentRecord(models.Model):
    invoice = models.ForeignKey(StudentInvoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)
    
    # Nigerian Context: Tracking payment methods is vital for reconciliation
    PAYMENT_METHODS = [('CASH', 'Cash'), ('TRANSFER', 'Bank Transfer'), ('ONLINE', 'Online Paystack/Flutterwave')]
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Teller no or Transfer Ref")
    
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(StudentInvoice, on_delete=models.CASCADE, related_name='items')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2) # Snapshot of the price at that moment

    def __str__(self):
        return f"{self.fee_structure.category.name} - {self.amount}"


class Discount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage (%)"
        FIXED = "FIXED", "Fixed Amount (₦)"

    name = models.CharField(max_length=100) 
    type = models.CharField(max_length=15, choices=DiscountType.choices, default=DiscountType.FIXED)
    value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Enter percentage or flat amount")
    
    invoice = models.ForeignKey(StudentInvoice, on_delete=models.CASCADE, related_name='discounts')
    
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.invoice.student}"