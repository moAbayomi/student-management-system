from django.db.models import Sum
from .models import ClassArm, Class

class AcademicsManagementService:
    @staticmethod
    def get_stats():
        class_arms = ClassArm.objects.all()
        all_classes = Class.objects.all()
        return {
            'class_arms': class_arms,
            'all_classes': all_classes,
            'total_class_arms': class_arms.count()
        }

def update_result_total(result):
    total = result.entries.aggregate(Sum('score'))['score__sum'] or 0
    result.total_score = total
    
    result.grade, result.remark = get_grade_and_remark(total)
    
    result.save()

def get_grade_and_remark(total_score):

    if total_score is 'None':
         return '', ''

    if total_score > 100:
        raise ValueError("Total score cannot exceed 100.")
    # A1 (75–100), B2 (70–74), B3 (65–69), C4 (60–64), C5 55–59), C6 (50–54), D7 (45–49), E8 (40–44), F9 (0–39)
    if total_score >= 75:
        return 'A1', 'Excellent'
    elif total_score >= 70:
        return 'B2', 'Very Good'
    elif total_score >= 65:
        return 'B3', 'Good'
    elif total_score >= 60:
        return 'C4', 'Upper Credit'
    elif total_score >= 55:
        return 'C5', 'Credit'
    elif total_score >= 50:
        return 'C6', 'Lower Credit'
    elif total_score >= 45:
        return 'D7', 'Pass'
    elif total_score >= 40:
        return 'E8', 'Weak Pass'
    else:
        return 'F9', 'Fail'