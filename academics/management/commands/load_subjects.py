from django.core.management.base import BaseCommand
from academics.models import Subject
from schools.models import School

class Command(BaseCommand):
    help = 'Bulk loads the entire Nigerian Secondary Curriculum'

    def handle(self, *args, **kwargs):
        school = School.objects.first()
        
        if not school:
            self.stdout.write(self.style.ERROR("No School found! Create a school record first."))
            return
        # Format: 'Category': [('Name', 'Code'), ...]
        curriculum = {
            'JNR_CORE': [
                ('Mathematics', 'MTH1'), ('English Language', 'ENG1'), 
                ('Civic Education', 'CIV1'), ('Computer Studies', 'COM1')
            ],
            'SNR_CORE': [
                ('General Mathematics', 'MTH3'), ('English Language', 'ENG3'), 
                ('Civic Education', 'CIV3'), ('Economics', 'ECO3'),
                ('Data Processing', 'DAP3')
            ],
            'JUNIOR': [
                ('Basic Science', 'BSC'), ('Basic Technology', 'BTE'), 
                ('Social Studies', 'SOS'), ('Agricultural Science', 'AGR'),
                ('Business Studies', 'BUS'), ('Home Economics', 'HEC'),
                ('Fine Arts', 'ART'), ('French', 'FRN'), ('P.H.E', 'PHE'),
                ('Christian Religious Studies', 'CRS'), ('Islamic Religious Studies', 'IRS'),
                ('Yoruba', 'YOR'), ('Igbo', 'IGB'), ('Hausa', 'HAU'),
                ('Security Education', 'SEC'), ('History', 'HIS'),
                ('Music', 'MUS'), ('Arabic', 'ARA')
            ],
            'SCIENCE': [
                ('Physics', 'PHY'), ('Chemistry', 'CHM'), 
                ('Biology', 'BIO'), ('Further Mathematics', 'FMT'),
                ('Geography', 'GEO'), ('Technical Drawing', 'TDR'),
                ('Foods and Nutrition', 'FNT'), ('Agricultural Science (Senior)', 'AGR-S'),
                ('Animal Husbandry', 'ANI'), ('Fisheries', 'FIS')
            ],
            'ARTS_HUMANITIES': [
                ('Literature in English', 'LIT-S'), ('Government', 'GOV'), 
                ('History (Senior)', 'HIS-S'), ('Christian Religious Studies (Senior)', 'CRS-S'),
                ('Islamic Religious Studies (Senior)', 'IRS-S'), ('Visual Arts', 'VAR'),
                ('Yoruba (Senior)', 'YOR-S'), ('Igbo (Senior)', 'IGB-S'), ('Hausa (Senior)', 'HAU-S'),
                ('Music (Senior)', 'MUS-S'), ('Arabic (Senior)', 'ARA-S'), ('French (Senior)', 'FRN-S')
            ],
            'COMMERCIAL': [
                ('Financial Accounting', 'ACC'), ('Commerce', 'CME'), 
                ('Office Practice', 'OFP'), ('Marketing', 'MKT'),
                ('Insurance', 'INS'), ('Store Management', 'STM'),
                ('Book Keeping', 'BKK')
            ],
            'VOCATIONAL_TRADE': [
                ('Catering Craft Practice', 'CCP'), ('Garment Making', 'GMK'), 
                ('Dyeing & Bleaching', 'DBL'), ('Printing Craft Practice', 'PCP'),
                ('Cosmetology', 'COS'), ('Photography', 'PHO'),
                ('Painting & Decorating', 'PDE'), ('Leather Goods Manufacture', 'LGM'),
                ('GSM Phone Maintenance', 'GSM'), ('Welding & Fabrication', 'WAF'),
                ('Carpentry & Joinery', 'CAJ'), ('Electrical Installation', 'EIN')
            ]
        }

        created_count = 0
        for category, subjects in curriculum.items():
            for name, code_prefix in subjects:
                # We'll use a standard format: CODE101 for Junior, CODE301 for Senior
                suffix = "101" if category in ['JNR_CORE', 'JUNIOR'] else "301"
                final_code = f"{code_prefix}{suffix}"

                obj, created = Subject.objects.get_or_create(
                    name=name,
                    school=school,
                    defaults={
                        'code': final_code,
                        'category': category
                    }
                )
                if created:
                    created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {created_count} subjects to the Library!'))