from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.conf import settings

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class LoginManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        if not username:
            raise ValueError("The Username field is required")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self.create_user(email, username, password, **extra_fields)
# Create your models here.
class login_tbl(AbstractBaseUser, PermissionsMixin):
    username=models.CharField(max_length=12)
    password=models.CharField(max_length=10)
    email=models.EmailField(unique=True)
    is_blocked = models.BooleanField(default=False)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    is_superuser = models.BooleanField(default=False) 
    is_staff = models.BooleanField(default=False)  # to distinguish admin
    # add other fields as needed like full_name, created_at, etc.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = LoginManager()

    def __str__(self):
        return self.email
    def __str__(self):
        return self.username  # ✅ so this shows correctly in forms and admin

    
   
class add_subuser(models.Model):
    username = models.ForeignKey(login_tbl, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    new_password=models.CharField(max_length=12)
    email=models.EmailField(unique=True)
    login_id=models.CharField(max_length=15,unique=True)
    foldername=models.CharField(max_length=12)
    licence_domain=models.CharField(max_length=15)
    embed_domain=models.CharField(max_length=15)
    licence_logo=models.ImageField(upload_to='images/')
    tools_logo=models.ImageField(upload_to='images/')
    login_screenlogo=models.ImageField(upload_to='images/')
    firstname=models.CharField(max_length=20)
    lastname=models.CharField(max_length=20)
    access_code=models.BigIntegerField()
    address=models.TextField()
    zipcode=models.IntegerField()
    mobile=models.BigIntegerField()
    fax=models.CharField(max_length=15)
    database_host=models.CharField(max_length=20,default='localhost:127.0.0.1')
    db_username=models.CharField(max_length=20,default='root')
    db_name=models.CharField(max_length=20,default='mysql')
    db_password=models.CharField(max_length=20,default="")
    is_blocked = models.BooleanField(default=False)
    allowed_number = models.IntegerField(default=0)
    unlimited = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)
class SubUserPermission(models.Model):
    user = models.ForeignKey(login_tbl, on_delete=models.CASCADE)
    section_name = models.CharField(max_length=100)
    allowed = models.IntegerField(default=0, blank=True, null=True)
    unlimited = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.section_name}"
    

class SubMaster(models.Model):
    login_id = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100, blank=True, default="")
    email = models.EmailField(unique=True)
    is_blocked = models.BooleanField(default=False)

    foldername = models.CharField(max_length=100, blank=True, default="")
    licence_domain = models.CharField(max_length=255, blank=True, default="")
    embed_domain = models.CharField(max_length=255, blank=True, default="")

    access_code = models.CharField(max_length=100, blank=True, default="")
    address = models.TextField(blank=True, default="")
    zipcode = models.CharField(max_length=20, blank=True, default="")
    mobile = models.CharField(max_length=20, blank=True, default="")
    fax = models.CharField(max_length=50, blank=True, default="")

    database_host = models.CharField(max_length=255, blank=True, default="")
    db_username = models.CharField(max_length=100, blank=True, default="")
    db_name = models.CharField(max_length=100, blank=True, default="")
    db_password = models.CharField(max_length=100, blank=True, default="")

    licence_logo = models.ImageField(upload_to="images/", blank=True, null=True)
    tools_logo = models.ImageField(upload_to="images/", blank=True, null=True)
    login_screenlogo = models.ImageField(upload_to="images/", blank=True, null=True)
    user = models.ForeignKey(login_tbl, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.login_id
class SubmasterPermission(models.Model):
    user = models.ForeignKey(login_tbl, on_delete=models.CASCADE)
    section_name = models.CharField(max_length=100)
    allowed = models.IntegerField(default=0, blank=True, null=True)
    unlimited = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.section_name}"
class LoginLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_type = models.CharField(max_length=50)  # e.g., "Master Admin", "Sub User"
    browser = models.CharField(max_length=100)
    operating_system = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.login_time}"
class SystemSetting(models.Model):
    no_star_message = models.CharField(max_length=255, default='No Star')
    head_unit = models.CharField(max_length=50, default='Meters')
    discharge_unit = models.CharField(max_length=50, default='LPH - Liter Per Hour')
    rating_unit = models.CharField(max_length=50, default='HP')
    per_page = models.IntegerField(default=10)
    help_head = models.TextField(blank=True, null=True)

    def __str__(self):
        return "System Settings"
class Category(models.Model):
    name = models.CharField(max_length=100)
    account = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    discharge_unit = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class MasterArea(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class CategoryMasterLink(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    master_area = models.CharField(max_length=100)  # Store area name directly
    is_applicable = models.BooleanField(default=False)
class MotorRating(models.Model):
    ACCOUNT_CHOICES = [
        ('Pump Demo', 'Pump Demo'),
        ('Pump A', 'Pump A'),
        ('Pump B', 'Pump B'),
    ]

    kw = models.DecimalField(max_digits=5, decimal_places=2)
    hp = models.DecimalField(max_digits=5, decimal_places=2)
    account = models.CharField(max_length=50, choices=ACCOUNT_CHOICES)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.kw} kW / {self.hp} HP - {self.account} - {'Active' if self.status else 'Inactive'}"
class Phase(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50)
    status = models.BooleanField(default=True)
    account = models.CharField(max_length=100, default='Pump Demo')  # or use a ForeignKey if needed

    def __str__(self):
        return self.name
class Hertz(models.Model):
    hz_name = models.CharField(max_length=100)
    account = models.CharField(max_length=100, default='Pump Demo')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.hz_name} - {self.account}"
class RPM(models.Model):
    rpm_name = models.CharField(max_length=50)
    account = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.rpm_name} ({self.account})"
class PipeSize(models.Model):
    pipe_size = models.CharField(max_length=100)
    account = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, related_name='pipesizes')

    def __str__(self):
        return self.pipe_size
class Size(models.Model):
    star_rating = models.CharField(max_length=100, verbose_name="Star Rating Name")
    account = models.CharField(max_length=100)
    pipe_sizes = models.ManyToManyField(PipeSize, blank=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.star_rating
    
class DischargeUnit(models.Model):
    UNIT_CHOICES = [
        ('M3/HR', 'M3/HR'),
        ('LPS', 'LPS'),
        ('LPH', 'LPH'),
        ('LPM', 'LPM'),
    ]

    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, unique=True)
    denotes = models.CharField(max_length=100)
    decimal_places = models.PositiveIntegerField(default=0)
    account = models.CharField(max_length=100, default='Pump Demo')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.unit} - {self.denotes}"
class Discharge(models.Model):
    discharge = models.IntegerField()
    account = models.CharField(max_length=100)
    unit = models.ForeignKey(DischargeUnit, on_delete=models.CASCADE, related_name="discharges")  # ✅ Add this
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.discharge} ({self.account})"
class MotorMaterial(models.Model):
    material_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=200, blank=True, null=True)
    
    account = models.CharField(max_length=100, default="Pump Demo")
    is_active = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, blank=True)

    def __str__(self):
        return self.material_name
class Certificate(models.Model):
    certificate_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=200, blank=True, null=True)
    account = models.CharField(max_length=100, default="Pump Demo")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.certificate_name
    @property
    def no_certificate_message(self):
        """Generate a dynamic message like: 'Non CE Marking'"""
        if self.certificate_name:
            return f"Non {self.certificate_name} Marking"
        return "No Certificate"
class MotorRotorMaterial(models.Model):
    motor_rotor_name = models.CharField(max_length=100)
    account = models.CharField(max_length=100, default='Pump Demo')
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.motor_rotor_name

class ImpellerMaterial(models.Model):
    impeller_name = models.CharField(max_length=100)
    account = models.CharField(max_length=100, default="Pump Demo")
    long_name = models.CharField(max_length=200, blank=True, null=True)
    categories = models.ManyToManyField(Category, blank=True)
    is_active = models.BooleanField(default=False)


    def __str__(self):
        return self.impeller_name
class MotorType(models.Model):
    motor_type_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=200, blank=True, null=True)
    account = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, blank=True)

    def __str__(self):
        return self.motor_type_name
class StarRating(models.Model):
    star_rating_name = models.CharField(max_length=100)
    account = models.CharField(max_length=100, default="Pump Demo")
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.star_rating_name

class Product(models.Model):
    model_name = models.CharField(max_length=100)

    # ForeignKey fields to master tables
    account = models.CharField(max_length=100, default="Pump Demo")
    categories = models.ManyToManyField(Category, blank=True)
    unit = models.ForeignKey(DischargeUnit, on_delete=models.CASCADE, null=True, blank=True)

    # Image uploads
    thumb_image = models.ImageField(upload_to='product/thumbs/', null=True, blank=True)
    motor_rating = models.ForeignKey(MotorRating, on_delete=models.SET_NULL, null=True, blank=True)
    phase = models.ForeignKey(Phase, on_delete=models.SET_NULL, null=True, blank=True)
    rpm = models.ForeignKey(RPM, on_delete=models.SET_NULL, null=True, blank=True)
    pipe_size = models.ForeignKey(PipeSize, on_delete=models.SET_NULL, null=True, blank=True)
    discharge = models.ManyToManyField(Discharge)  # assuming multiple discharges
    preview_image = models.ImageField(upload_to='product/previews/', null=True, blank=True)
    hertz = models.ForeignKey(Hertz, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.model_name
class MotorPumpData(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    motor_rating = models.ForeignKey(MotorRating, on_delete=models.SET_NULL, null=True)
    phase = models.ForeignKey(Phase, on_delete=models.SET_NULL, null=True)
    pipe_size = models.ForeignKey(PipeSize, on_delete=models.SET_NULL, null=True)
    discharge = models.IntegerField()  # LPM
    head = models.FloatField()         # In meters
    recommend = models.BooleanField(default=False)