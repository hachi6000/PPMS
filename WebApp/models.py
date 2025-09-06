from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string
from datetime import date
from django.contrib.auth.models import User
import os

# Create your models here.
class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    
    
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.username
      

class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100, default='Unknown')
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    password = models.CharField(max_length=100)
    user_role = models.CharField(max_length=100)  # ✅ Removed unique=True
    is_validated = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    validated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='validated_accounts'
    )
    barangay = models.ForeignKey('Barangay', on_delete=models.SET_NULL, null=True, blank=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_notif_read = models.BooleanField(default=False)

    # 👇 New field
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    @property
    def computed_age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - (
                (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
            )
        return None

def announcement_image_upload_path(instance, filename):
    """Generate upload path for announcement images"""
    return f'announcements/{filename}'

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to=announcement_image_upload_path, blank=True, null=True, help_text="Upload an image for this announcement")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'webapp_announcement'
    
    def __str__(self):
        return self.title
    
    def delete(self, *args, **kwargs):
        """Delete associated image file when announcement is deleted"""
        if self.image:
            try:
                if os.path.isfile(self.image.path):
                    os.remove(self.image.path)
            except:
                pass
        super().delete(*args, **kwargs)

class BNS(models.Model):
    bns_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=100)
    barangay = models.ForeignKey('Barangay', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class BHW(models.Model):
    bhw_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=100)
    barangay = models.ForeignKey('Barangay', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.email

class Midwife(models.Model):
    midwife_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=100)
    barangay = models.ForeignKey('Barangay', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.email
    
class Nurse(models.Model):
    nurse_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=100)
    barangay = models.ForeignKey('Barangay', on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.email    

class Barangay(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    assigned_bhw = models.CharField(max_length=100, blank=True, null=True)
    health_center = models.CharField(max_length=100, blank=True, null=True)
    zone_number = models.CharField(max_length=50, blank=True, null=True)
    date_established = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

    @property
    def computed_age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - (
                (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
            )
        return None
    
class Parent(models.Model):
    parent_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)  # Optional: can be kept for historical record
    birthdate = models.DateField(blank=True, null=True)
    registered_preschoolers = models.ManyToManyField('Preschooler', blank=True, related_name='parents')
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=100)
    barangay = models.ForeignKey('Barangay', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    must_change_password = models.BooleanField(default=True)
    

    def __str__(self):
        return self.full_name

    @property
    def computed_age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - (
                (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
            )
        return None

class Preschooler(models.Model):
    preschooler_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=10)
    birth_date = models.DateField()
    age = models.IntegerField()
    address = models.CharField(max_length=255, blank=True, null=True)
    parent_id = models.ForeignKey(Parent, on_delete=models.CASCADE, blank=True, null=True)
    bhw_id = models.ForeignKey(BHW, on_delete=models.CASCADE, blank=True, null=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, blank=True, null=True)
    nutritional_status = models.CharField(max_length=50, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='preschoolers/', null=True, blank=True)
    
    # Existing birth fields
    birth_weight = models.FloatField(blank=True, null=True, help_text="Birth weight in kilograms")
    birth_height = models.FloatField(blank=True, null=True, help_text="Birth length/height in centimeters")
    place_of_birth = models.CharField(max_length=255, blank=True, null=True, help_text="Place where the child was born")
    time_of_birth = models.TimeField(blank=True, null=True, help_text="Time when the child was born (HH:MM)")
    
    # New birth fields
    TYPE_OF_BIRTH_CHOICES = [
        ('Normal', 'Normal'),
        ('CS', 'Cesarean Section (CS)'),
    ]
    type_of_birth = models.CharField(
        max_length=20, 
        choices=TYPE_OF_BIRTH_CHOICES, 
        blank=True, 
        null=True,
        help_text="Type of delivery"
    )
    
    PLACE_OF_DELIVERY_CHOICES = [
        ('Home', 'Home'),
        ('Lying-in', 'Lying-in'),
        ('Hospital', 'Hospital'),
        ('Others', 'Others'),
    ]
    place_of_delivery = models.CharField(
        max_length=20, 
        choices=PLACE_OF_DELIVERY_CHOICES, 
        blank=True, 
        null=True,
        help_text="Place where delivery occurred"
    )
    
    # Existing fields
    is_archived = models.BooleanField(default=False)
    date_registered = models.DateTimeField(default=timezone.now)
    is_notif_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.preschooler_id})"
    
    class Meta:
        verbose_name = "Preschooler"
        verbose_name_plural = "Preschoolers"
        ordering = ['-date_registered']

class BMI(models.Model):
    bmi_id = models.AutoField(primary_key=True)
    preschooler_id = models.ForeignKey(Preschooler, on_delete=models.CASCADE)
    weight = models.FloatField()    
    height = models.FloatField()
    bmi_value = models.FloatField()
    date_recorded = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"BMI Record for {self.preschooler_id} on {self.date_recorded}"

class Temperature(models.Model):
    temperature_id = models.AutoField(primary_key=True)
    preschooler_id = models.ForeignKey(Preschooler, on_delete=models.CASCADE)
    temperature_value = models.FloatField()
    date_recorded = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey(BHW, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"Temperature Record for {self.preschooler_id} on {self.date_recorded}"
    
class Immunization(models.Model):
    immunization_id = models.AutoField(primary_key=True)
    preschooler_id = models.ForeignKey(Preschooler, on_delete=models.CASCADE)
    vaccine_name = models.CharField(max_length=100)
    date_administered = models.DateField()
    administered_by = models.ForeignKey(BHW, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.vaccine_name} for {self.preschooler_id} on {self.date_administered}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    class Meta:
        ordering = ['-created_at']

class ProfilePhoto(models.Model):
    account = models.OneToOneField('Account', on_delete=models.CASCADE, related_name='profile_photo')
    image = models.ImageField(upload_to='profile_photos/', default='default-profile.png')

    def __str__(self):
        return f"{self.account.full_name}'s Photo"

class VaccinationSchedule(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('rescheduled', 'Rescheduled'),
        ('missed', 'Missed'),
    ]
    
    preschooler = models.ForeignKey(Preschooler, on_delete=models.CASCADE, related_name='vaccination_schedules')
    vaccine_name = models.CharField(max_length=100)
    doses = models.IntegerField(blank=True, null=True)
    required_doses = models.IntegerField(blank=True, null=True)
    scheduled_date = models.DateField()
    next_vaccine_schedule = models.DateField(blank=True, null=True)
    
    # New status field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    scheduled_by = models.ForeignKey(BHW, on_delete=models.SET_NULL, null=True, blank=True)
    confirmed_by_parent = models.BooleanField(default=False)
    administered_date = models.DateField(blank=True, null=True)
    administered_by = models.ForeignKey(BHW, on_delete=models.SET_NULL, blank=True, null=True, related_name='administered_schedules')
    
    # Additional fields for tracking
    completion_date = models.DateTimeField(blank=True, null=True)
    reschedule_reason = models.TextField(blank=True, null=True)
    stock_deducted = models.BooleanField(default=False)  # Track if stock was already deducted
    
    notified = models.BooleanField(default=False)
    lapsed = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Auto-set completion_date when status changes to completed
        if self.status == 'completed' and not self.completion_date:
            self.completion_date = timezone.now()
            self.administered_date = timezone.now().date()
            
        # Deduct stock when marked as completed (only once)
        if self.status == 'completed' and not self.stock_deducted:
            try:
                vaccine_stock = VaccineStock.objects.get(vaccine_name=self.vaccine_name)
                if vaccine_stock.available_stock > 0:
                    vaccine_stock.available_stock -= 1
                    vaccine_stock.save()
                    self.stock_deducted = True
            except VaccineStock.DoesNotExist:
                pass  # Handle case where vaccine stock doesn't exist
                
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.vaccine_name} for {self.preschooler.first_name} {self.preschooler.last_name} - {self.get_status_display()}"


class VaccineStock(models.Model):
    vaccine_name = models.CharField(max_length=100, unique=True)
    total_stock = models.IntegerField(default=0)
    available_stock = models.IntegerField(default=0)  # Stock available for scheduling
    last_updated = models.DateTimeField(auto_now=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, related_name='vaccine_stocks', blank=True, null=True)
                               

    class Meta:
        unique_together = ('vaccine_name', 'barangay')  # prevent duplicate vaccine names per barangay

    def __str__(self):
        return f"{self.vaccine_name} - {self.barangay.name}"
    
class ParentActivityLog(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE)
    activity = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.activity}"

class PreschoolerActivityLog(models.Model):
    preschooler_name = models.CharField(max_length=255)
    activity = models.TextField()
    performed_by = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.preschooler_name} - {self.activity}"
    



    def create_account(email, raw_password, full_name, role):
    # Create Django User (hashed password stored here)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=raw_password
        )

        # Create Account model (optional: store hashed pw too)
        account = Account.objects.create(
            full_name=full_name,
            email=email,
            password=user.password,   # hashed password
            user_role=role,
            validated_by=None
        )

        return account
    
class NutritionService(models.Model):
    preschooler = models.ForeignKey(Preschooler, on_delete=models.CASCADE, related_name='nutrition_services')
    service_type = models.CharField(max_length=100)
    completion_date = models.DateTimeField()  # No default value needed
    status = models.CharField(max_length=20, default='completed')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completion_date']