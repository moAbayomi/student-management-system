def calculate_totals(self):
    # 1. Start with the base fee from the FeeStructure
    base_total = self.get_base_fee_sum() 
    
    # 2. Calculate Discount Total
    discount_total = 0
    for d in self.discounts.all():
        if d.type == "PERCENTAGE":
            discount_total += (base_total * (d.value / 100))
        else:
            discount_total += d.value
            
    # 3. Final Calculation
    self.total_amount = base_total - discount_total
    self.balance = self.total_amount - self.paid_amount
    self.save()