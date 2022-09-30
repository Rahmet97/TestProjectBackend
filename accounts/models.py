from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser
from django.template.defaultfilters import slugify

from .managers import CustomUserManager


class Group(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, blank=True)
    comment = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    prefix = models.CharField(max_length=5)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Permission(models.Model):
    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=50)
    partition = models.ManyToManyField(Permission, through='RolePermission')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permissions = models.ForeignKey(Permission, on_delete=models.CASCADE)
    create = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)


class UserData(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)

    objects = CustomUserManager()

    # USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


class LogPermission(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    comment = models.CharField(max_length=50)
    created_date = models.DateTimeField(auto_now_add=True)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.created_date)


class LogGroup(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    comment = models.CharField(max_length=30)
    created_date = models.DateTimeField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.comment


class FizUser(models.Model):
    userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
    birth_date = models.DateField()
    ctzn = models.CharField(max_length=50)
    per_adr = models.CharField(max_length=255)
    tin = models.CharField(max_length=9)
    pport_issue_place = models.CharField(max_length=255)
    sur_name = models.CharField(max_length=50)
    gd = models.IntegerField()
    natn = models.CharField(max_length=50)
    pport_issue_date = models.DateField()
    pport_expr_date = models.DateField()
    pport_no = models.CharField(max_length=20)
    pin = models.CharField(max_length=14)
    mob_phone_no = models.CharField(max_length=20)
    user_id = models.CharField(max_length=30)
    email = models.EmailField()
    birth_place = models.CharField(max_length=50)
    mid_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=1)
    sess_id = models.CharField(max_length=255)
    ret_cd = models.IntegerField()
    first_name = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class YurUser(models.Model):
    userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=100, blank=True)
    opf = models.CharField(max_length=3, blank=True)
    soogu = models.CharField(max_length=5, blank=True)
    oked = models.CharField(max_length=5, blank=True)
    status = models.CharField(max_length=5, blank=True)
    vatNumber = models.CharField(max_length=12, blank=True)
    taxpayerType = models.CharField(max_length=255, blank=True)
    businessType = models.CharField(max_length=255, blank=True)
    activityCode = models.CharField(max_length=4, blank=True)
    individualEntrepreneurType = models.CharField(max_length=2, blank=True)
    countryCode = models.CharField(max_length=3, blank=True)
    soato = models.CharField(max_length=10, blank=True)
    villageCode = models.CharField(max_length=5, blank=True)
    sectorCode = models.CharField(max_length=1, blank=True)
    streetName = models.CharField(max_length=100, blank=True)
    house = models.IntegerField(blank=True)
    flat = models.IntegerField(blank=True)
    postCode = models.CharField(max_length=20, blank=True)
    cadastreNumber = models.CharField(max_length=36, blank=True)
    billingCountryCode = models.CharField(max_length=3, blank=True)
    billingSoato = models.CharField(max_length=10, blank=True)
    billingVillageCode = models.CharField(max_length=5, blank=True)
    billingSectorCode = models.CharField(max_length=1, blank=True)
    billingStreetName = models.CharField(max_length=100, blank=True)
    billingHouse = models.IntegerField(blank=True)
    billingFlat = models.IntegerField(blank=True)
    billingPostCode = models.CharField(max_length=20, blank=True)
    billingCadastreNumber = models.CharField(max_length=36, blank=True)
    director_lastname = models.CharField(max_length=50, blank=True)
    director_firstname = models.CharField(max_length=50, blank=True)
    director_middlename = models.CharField(max_length=50, blank=True)
    director_gender = models.CharField(max_length=1, blank=True)
    director_nationality = models.CharField(max_length=4, blank=True)
    director_ctzn = models.CharField(max_length=3, blank=True)
    director_passportSeries = models.CharField(max_length=2, blank=True)
    director_passportNumber = models.IntegerField(blank=True)
    director_pinfl = models.CharField(max_length=14, blank=True)
    director_tin = models.CharField(max_length=9, blank=True)
    director_phone = models.CharField(max_length=12, blank=True)
    director_email = models.CharField(max_length=40, blank=True)
    mfo = models.CharField(max_length=5, blank=True)
    paymentAccount = models.CharField(max_length=20, blank=True)
    extraActivityType = models.CharField(max_length=4, blank=True)
    birth_date = models.DateField()
    ctzn = models.CharField(max_length=50)
    per_adr = models.CharField(max_length=255)
    tin = models.CharField(max_length=9)
    pport_issue_place = models.CharField(max_length=255)
    sur_name = models.CharField(max_length=50)
    gd = models.IntegerField()
    natn = models.CharField(max_length=50)
    pport_issue_date = models.DateField()
    pport_expr_date = models.DateField()
    pport_no = models.CharField(max_length=20)
    pin = models.CharField(max_length=14)
    mob_phone_no = models.CharField(max_length=20)
    user_id = models.CharField(max_length=30)
    email = models.EmailField()
    birth_place = models.CharField(max_length=50)
    mid_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=1)
    sess_id = models.CharField(max_length=255)
    ret_cd = models.IntegerField()
    first_name = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
