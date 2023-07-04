from os.path import splitext
from django.utils.translation import gettext_lazy as _

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser
from django.template.defaultfilters import slugify
from simple_history.models import HistoricalRecords

from .managers import CustomUserManager


# def slugify_upload(instance, filename):
#     folder = instance._meta.model.__name__
#     name, ext = splitext(filename)
#     try:
#
#         name_t = slugify(name)
#         if name_t is None:
#             name_t = name
#         path = folder + "/" + name_t + ext
#     except:
#         path = folder + "/default" + ext
#
#     return path

def slugify_upload(instance, filename):
    folder = instance._meta.model_name
    name, ext = splitext(filename)
    name_t = slugify(name) or name
    return f"{folder}/{name_t}{ext}"


class Departament(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Group(models.Model):
    full_name = models.CharField(max_length=255, unique=True, blank=True, null=True)
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, blank=True)
    comment = models.TextField()
    # prefix = models.CharField(max_length=5)

    active_icon = models.ImageField(upload_to=slugify_upload, blank=True, null=True)
    inactive_icon = models.ImageField(upload_to=slugify_upload, blank=True, null=True)

    is_one_time_payment = models.BooleanField(default=False, verbose_name="bir martalik to'lovmi?")
    is_visible_in_front = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DepartamentGroup(models.Model):
    departament = models.ForeignKey(to=Departament, related_name="departament_croup", on_delete=models.CASCADE)
    group = models.ForeignKey(to="Group", related_name="croup_departament", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.departament.name} -> {self.group.full_name}|{self.group.name}"


class Permission(models.Model):
    class FilterTagChoices(models.IntegerChoices):
        MANAGEMENT = 1, "Boshqaruv"

    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=100, blank=True)
    icon = models.FileField(upload_to=slugify_upload, blank=True, null=True)

    filter_tag = models.IntegerField(choices=FilterTagChoices.choices, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Role(models.Model):
    class RoleNames(models.TextChoices):
        ADMIN = "admin", "admin"
        DEPARTMENT_BOSS = "departament boshlig'i", "departament boshlig'i"
        SECTION_HEAD = "bo'lim boshlig'i", "bo'lim boshlig'i"
        SECTION_SPECIALIST = "bo'lim mutaxasisi", "bo'lim mutaxasisi"
        DEPUTY_DIRECTOR = "direktor o'rinbosari", "direktor o'rinbosari"
        DIRECTOR = "direktor", "direktor"
        # ECONOMIST = "iqtisodchi", "iqtisodchi"
        ACCOUNTANT = "buxgalteriya", "buxgalteriya"
        DISPATCHER = "dispetcher", "dispetcher"
        CLIENT = "mijoz", "mijoz"

    name = models.CharField(max_length=50, choices=RoleNames.choices)
    # name = models.CharField(max_length=50)
    partition = models.ManyToManyField(Permission, through='RolePermission')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permissions = models.ForeignKey(Permission, on_delete=models.CASCADE)
    create = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)

    # def __str__(self):
    #     return str(self.group.name) + "|" + str(self.role.name) + "|" + str(self.filter_tag)


class UserData(AbstractUser):
    class StatusChoices(models.IntegerChoices):
        CLIENT = 1, "Mijoz"
        WAITING_LIST = 2, "Kutish zali"
        EMPLOYEE = 3, "Xodim"

    FIZ = 1
    YUR = 2
    user_type = (
        (FIZ, 'Fizik'),
        (YUR, 'Yuridik')
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, blank=True, null=True)
    # group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    group = models.ManyToManyField(Group, blank=True, null=True)
    type = models.IntegerField(choices=user_type, blank=True, null=True)
    status_action = models.IntegerField(choices=StatusChoices.choices, default=1)

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
    birth_date = models.DateField(blank=True, null=True)
    ctzn = models.CharField(max_length=50, blank=True, null=True)
    per_adr = models.CharField(max_length=255)
    tin = models.CharField(max_length=9, blank=True, null=True)
    pport_issue_place = models.CharField(max_length=255, blank=True, null=True)
    sur_name = models.CharField(max_length=50)
    gd = models.IntegerField(blank=True, null=True)
    natn = models.CharField(max_length=50, blank=True, null=True)
    pport_issue_date = models.DateField(blank=True, null=True)
    pport_expr_date = models.DateField(blank=True, null=True)
    pport_no = models.CharField(max_length=20)
    pin = models.CharField(max_length=14)
    mob_phone_no = models.CharField(max_length=20, blank=True, null=True)
    user_id = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    birth_place = models.CharField(max_length=50, blank=True, null=True)
    mid_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=1)
    sess_id = models.CharField(max_length=255, blank=True, null=True)
    ret_cd = models.IntegerField(blank=True, null=True)
    first_name = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.sur_name}"

    @property
    def get_short_full_name(self):
        return f"{str(self.first_name)[0]}.{str(self.mid_name)[0]} {self.sur_name}"

    @property
    def get_user_role(self):
        return f"{self.userdata.role}"


class BankMFOName(models.Model):
    mfo = models.CharField(max_length=5)
    bank_name = models.CharField(max_length=30)
    branch_name = models.CharField(max_length=150)
    branch_address = models.CharField(max_length=255)
    region = models.CharField(max_length=30)
    district = models.CharField(max_length=30)
    city = models.CharField(max_length=30)
    tin = models.CharField(max_length=9)
    website = models.CharField(max_length=50)
    geolocation = models.CharField(max_length=50)

    def __str__(self):
        return self.branch_name


class YurUser(models.Model):
    userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    opf = models.CharField(max_length=3, blank=True, null=True)
    soogu = models.CharField(max_length=5, blank=True, null=True)
    oked = models.CharField(max_length=5, blank=True, null=True)
    status = models.CharField(max_length=5, blank=True, null=True)
    vatNumber = models.CharField(max_length=12, blank=True, null=True)
    taxpayerType = models.CharField(max_length=255, blank=True, null=True)
    businessType = models.CharField(max_length=255, blank=True, null=True)
    activityCode = models.CharField(max_length=4, blank=True, null=True)
    individualEntrepreneurType = models.CharField(max_length=2, blank=True, null=True)
    countryCode = models.CharField(max_length=3, blank=True, null=True)
    soato = models.CharField(max_length=10, blank=True, null=True)
    villageCode = models.CharField(max_length=5, blank=True, null=True)
    sectorCode = models.CharField(max_length=1, blank=True, null=True)
    streetName = models.CharField(max_length=100, blank=True, null=True)
    house = models.IntegerField(blank=True, null=True)
    flat = models.IntegerField(blank=True, null=True)
    postCode = models.CharField(max_length=20, blank=True, null=True)
    cadastreNumber = models.CharField(max_length=36, blank=True, null=True)
    billingCountryCode = models.CharField(max_length=3, blank=True, null=True)
    billingSoato = models.CharField(max_length=10, blank=True, null=True)
    billingVillageCode = models.CharField(max_length=5, blank=True, null=True)
    billingSectorCode = models.CharField(max_length=1, blank=True, null=True)
    billingStreetName = models.CharField(max_length=100, blank=True, null=True)
    billingHouse = models.IntegerField(blank=True, null=True)
    billingFlat = models.IntegerField(blank=True, null=True)
    billingPostCode = models.CharField(max_length=20, blank=True, null=True)
    billingCadastreNumber = models.CharField(max_length=36, blank=True, null=True)
    position = models.CharField(max_length=255, blank=True, null=True)
    director_lastname = models.CharField(max_length=50, blank=True, null=True)
    director_firstname = models.CharField(max_length=50, blank=True, null=True)
    director_middlename = models.CharField(max_length=50, blank=True, null=True)
    director_gender = models.CharField(max_length=1, blank=True, null=True)
    director_nationality = models.CharField(max_length=4, blank=True, null=True)
    director_ctzn = models.CharField(max_length=3, blank=True, null=True)
    director_passportSeries = models.CharField(max_length=2, blank=True, null=True)
    director_passportNumber = models.IntegerField(blank=True, null=True)
    director_pinfl = models.CharField(max_length=14, blank=True, null=True)
    director_tin = models.CharField(max_length=9, blank=True, null=True)
    director_phone = models.CharField(max_length=12, blank=True, null=True)
    director_email = models.CharField(max_length=40, blank=True, null=True)
    bank_mfo = models.ForeignKey(BankMFOName, on_delete=models.CASCADE, blank=True, null=True)
    paymentAccount = models.CharField(max_length=24, blank=True, null=True)
    extraActivityType = models.CharField(max_length=4, blank=True, null=True)
    xxtut = models.CharField(max_length=20, blank=True, null=True)
    ktut = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    ctzn = models.CharField(max_length=50, blank=True, null=True)
    per_adr = models.CharField(max_length=255)
    tin = models.CharField(max_length=9, blank=True, null=True)
    pport_issue_place = models.CharField(max_length=255, blank=True, null=True)
    sur_name = models.CharField(max_length=50, blank=True, null=True)
    gd = models.IntegerField(blank=True, null=True)
    natn = models.CharField(max_length=50, blank=True, null=True)
    pport_issue_date = models.DateField(blank=True, null=True)
    pport_expr_date = models.DateField(blank=True, null=True)
    pport_no = models.CharField(max_length=20, blank=True, null=True)
    pin = models.CharField(max_length=14, blank=True, null=True)
    mob_phone_no = models.CharField(max_length=20, blank=True, null=True)
    user_id = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    birth_place = models.CharField(max_length=50, blank=True, null=True)
    mid_name = models.CharField(max_length=50, blank=True, null=True)
    user_type = models.CharField(max_length=1)
    sess_id = models.CharField(max_length=255, blank=True, null=True)
    ret_cd = models.IntegerField(blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name or "Unnamed YurUser"

    @property
    def get_director_short_full_name(self):
        return f"{str(self.director_firstname)[0]}.{str(self.director_middlename)[0]} {self.director_lastname}"

    @property
    def get_director_full_name(self):
        return f"{self.director_firstname} {self.director_middlename} {self.director_lastname}"

    @property
    def get_user_role(self):
        return f"{self.userdata.role}"


class UniconDatas(models.Model):
    name = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    name_ru = models.CharField(max_length=255, blank=True, null=True)

    short_name = models.CharField(max_length=100)
    short_name_en = models.CharField(max_length=100, blank=True, null=True)
    short_name_ru = models.CharField(max_length=100, blank=True, null=True)

    position = models.CharField(max_length=255)
    position_en = models.CharField(max_length=255, blank=True, null=True)
    position_ru = models.CharField(max_length=255, blank=True, null=True)

    first_name = models.CharField(max_length=50)
    first_name_en = models.CharField(max_length=50, blank=True, null=True)
    first_name_ru = models.CharField(max_length=50, blank=True, null=True)

    mid_name = models.CharField(max_length=50)
    mid_name_en = models.CharField(max_length=50, blank=True, null=True)
    mid_name_ru = models.CharField(max_length=50, blank=True, null=True)

    sur_name = models.CharField(max_length=50)
    sur_name_en = models.CharField(max_length=50, blank=True, null=True)
    sur_name_ru = models.CharField(max_length=50, blank=True, null=True)

    document = models.CharField(max_length=50, blank=True, null=True)
    document_en = models.CharField(max_length=50, blank=True, null=True)
    document_ru = models.CharField(max_length=50, blank=True, null=True)

    per_adr = models.CharField(max_length=255)
    per_adr_en = models.CharField(max_length=255, blank=True, null=True)
    per_adr_ru = models.CharField(max_length=255, blank=True, null=True)

    phone_number = models.CharField(max_length=50, blank=True, null=True)
    fax = models.CharField(max_length=50, blank=True, null=True)  # faks
    email = models.EmailField(blank=True, null=True)
    e_xat = models.EmailField(blank=True, null=True)
    postCode = models.CharField(max_length=20, blank=True, null=True)
    tin = models.CharField(max_length=9, blank=True, null=True)
    bank_mfo = models.ForeignKey(BankMFOName, on_delete=models.CASCADE, blank=True, null=True)
    paymentAccount = models.CharField(max_length=24, blank=True, null=True)
    xxtut = models.CharField(max_length=20, blank=True, null=True)
    ktut = models.CharField(max_length=20, blank=True, null=True)
    oked = models.CharField(max_length=5, blank=True, null=True)  # ifut
    web_site = models.URLField(blank=True, null=True)
    dm_web_site = models.URLField(blank=True, null=True)
    dm_phone_number = models.CharField(max_length=50, blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.mid_name} {self.sur_name}"

    @property
    def get_director_short_full_name(self):
        return f"{str(self.first_name)[0]}.{str(self.mid_name)[0]} {self.sur_name}"
