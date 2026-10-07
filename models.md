## school models
### school
-> name
-> slug
-> tagline
-> about

-> logo
-> favicon
-> hero_image
-> primary_color
-> secondary_color
-> address
-> phone
-> email
-> website
-> principal_name
-> has_payments
-> created_at
-> timezone
-> grading_system
-> pass_mark

### AcademicSession
session_status = [
PLANNING  =  "PLANNING", "Planning/Admission"
ACTIVE  =  "ACTIVE", "Active"
ARCHIVED  =  "ARCHIVED", "Archived"
]
-> school(School)
-> name
-> start_year
-> end_year
-> start_date
-> end_date
-> status(session_status)
-> is_current

### AcademicTerm
term_choices = [
FIRST  =  "FIRST", "First Term"
SECOND  =  "SECOND", "Second Term"
THIRD  =  "THIRD", "Third Term"
]
-> session(AcademicSession)
-> term_type(term_choices)
-> grading_deadline // date
-> next_term_begins // date
-> start_date
-> end_date
-> is_current
-> result_published

### ActivityLog
category = [
ACADEMIC  =  "ACADEMIC", "Academic (Grades/Attendance)"
FINANCE  =  "FINANCE", "Finance (Fees/Payments)"
USER  =  "USER", "User Management (Enrollment/Profiles)"
SYSTEM  =  "SYSTEM", "System (Settings/Announcements)"
]
-> actor(User)
-> action
-> category(category)
-> description
-> ip_address
-> timestamp

### Announcement
target = [
ALL  =  "ALL", "Everyone
TEACHERS  =  "TEACHERS", "Teachers Only"
STUDENTS  =  "STUDENTS", "Students & Parents"
ADMINS  =  "ADMINS", "Admins Only"
]
-> school(School)
-> author(User)
-> title
-> content
-> audience(target)
-> pinned
-> is_active
-> created_at
-> updated_at
-> expiry_date


## user and profiles

### base User model
-> first_name
-> middle_name
-> last_name
-> username
-> email
-> phone_number
-> role
-> address
-> profile_picture
-> gender
-> state_of_origin
-> religion
-> is onboarded
-> created_at
-> uploaded_at

### TeacherProfile model. 
-> user(User)
-> status // ACTIVE, ON_LEAVE, PENDING_REVIEW etc
-> onboarding_token
-> onboarding_token_expires_at
-> employee_id
-> dob
->qualification
->years_of_exp
-> date_joined
->department //JUNIOR, SCIENCE, ARTS, COMMERCIAL
-> subjects
-> max_weekly_hours
-> assigned_class_arm
-> roles
-> can_login_portal
-> can_upload_results
-> can_mark_attendance
-> can_post_announcements
-> created_at
-> updated_at

### StudentProfile model.
-> user(User)
-> status // ACTIVE, PENDING_REVIEW, GRADUATED, SUSPENDED etc
-> date_of_birth
-> subjects
-> admission_number
-> onboarding_token
-> onboarding_token_expires_at
-> class_arm
-> admission_type
-> entry_term
-> previous_school
-> previous_class
-> fee_plan

-> guardian_first_name
-> guardian_last_name
-> guardian_relationship
-> guardian_phone
-> guardian_email
-> guardian_occupation
-> guardian_nin
-> guardian_address
-> emergency_contact_name
-> emergency_contact_phone
-> blood_group
-> genotype
-> disability
-> allergies
-> medical_conditions
-> admin_notes

## academics

### Class
_level = [
	JSS1  =  'JSS1', 'Junior Secondary School 1'
	JSS2  =  'JSS2', 'Junior Secondary School 2'
	JSS3  =  'JSS3', 'Junior Secondary School 3'
	SSS1  =  'SSS1', 'Senior Secondary School 1'
	SSS2  =  'SSS2', 'Senior Secondary School 2'
	SSS3  =  'SSS3', 'Senior Secondary School 3'
]
-> name(Level.choices)
-> core_subjects(Subject)

### ClassArm
-> class_level // JSS1, SSS2 etc
-> name // A, B, Gold etc
-> class_teacher(TeacherProfile)

### Subject
_category_choices = [
	('JNR_CORE', 'Junior Core'),
	('SNR_CORE', 'Senior Core'),
	('JUNIOR', 'Junior Secondary'),
	('SCIENCE', 'Senior Science'),
	('ARTS', 'Senior Arts'),
	('COMMERCIAL', 'Senior Commercial'),
	('VOCATIONAL_TRADE', 'Vocational Trade')
]
-> name // Chemisty, Social Studies etc
-> code
-> cateory(_category_choices)

### SubjectAssignment
-> class_arm // JSS2A
-> subject // Social Studies
-> session // 2026/2027
-> teacher(TeacherProfile)
// unique_together(class_arm, subject, session)

### StudentSubjectChoice
-> student(StudentProfile)
-> subject(Subject)
-> session

### Result
-> student
-> subject_assignment(SubjectAssignment)
-> term(AcademicTerm)
-> total_score
-> grade
-> remark

### GradeComponent
-> name
-> max_score
-> is_exam

### ResultEntry
-> result
-> component
-> score

### ReportCard
-> student
-> term
-> class_arm
-> total_obtained
-> total_attainable
-> average
-> position
-> days_present
-> days_absent
-> days_school_opened
-> form_teacher_comment
-> principal_comment
-> punctuality
-> neatness
-> honesty
-> self_control
-> handwriting
-> sports

-> is_locked

### DailyAttendance
_status = [
	(PRESENT, 'Present'),
	(ABSENT, 'Absent'),
	(EXCUSED, 'Excused'),
	(LATE, 'Late')
]
-> student(StudentProfile)
-> class_arm(ClassArm)
-> date
-> term(AcademicTerm)
-> status
-> remarks
-> updated_by


### Period
-> name
-> start_time
-> end_time
-> is_academic

###TimeTableSlot
-> day
-> period(Period)
-> class_arm
-> subject_assignment(SubjectAssignment)

## Fees
### FeeCategory
-> name
-> description

### FeeStructure
-> category(FeeCategory)
-> class_level(Class)
-> session(AcademicSession)
-> amount

### StudentInvoice
-> student(StudentProfile)
-> term
-> total_amount
-> paid_amount
-> balance
-> is_fully_paid

### PaymentRecord
payment_methods = [
[('CASH', 'Cash'), ('TRANSFER', 'Bank Transfer'), ('ONLINE', 'Online Paystack/Flutterwave')]
]
-> invoice(StudentInvoice)
-> amount_paid
-> date_paid
-> method(payment_methods)
-> reference_number
-> received_by

### InvoiceItem
-> invoice(StudentInvoice)
-> amount

### Discount
type = [
PERCENTAGE  =  "PERCENTAGE", "Percentage (%)"
FIXED  =  "FIXED", "Fixed Amount (₦)"
]

-> name
-> type
-> choices(type)
-> value
-> invoice(StudentInvoice)
-> approved_by
-> reason
-> created_at


## Notification

### Notification
priority = [
INFO  =  "INFO", "Information"
WARNING  =  "WARNING", "Warning"
URGENT  =  "URGENT", "Urgent/Critical"
]
-> recipient(User)
-> title
-> message
-> link
-> priority(priority)
-> is_read
-> created_at