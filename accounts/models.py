from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Partition(models.Model):
    name = models.CharField(max_length=50)
    create = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=50)
    comment = models.CharField(max_length=30)
    created_date = models.DateTimeField(auto_now_add=True)
    prefix = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class UserData(models.Model):
    user = models.CharField(max_length=20)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.role.name


class LogGroup(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    comment = models.CharField(max_length=30)
    created_date = models.DateTimeField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.comment


class FizUser(models.Model):
    user_id = models.ForeignKey(UserData, on_delete=models.CASCADE)
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
    user_id = models.ForeignKey(UserData, on_delete=models.CASCADE)
    tin = models.CharField(max_length=9)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)
    opf = models.CharField(max_length=3)
    soogu = models.CharField(max_length=5)
    oked = models.CharField(max_length=5)
    status = models.CharField(max_length=5)
    vatNumber = models.CharField(max_length=12)
    taxpayerType = models.CharField(max_length=255)
    businessType = models.CharField(max_length=255)
    activityCode = models.CharField(max_length=4)
    individualEntrepreneurType = models.CharField(max_length=2)
    countryCode = models.CharField(max_length=3)
    soato = models.CharField(max_length=10)
    villageCode = models.CharField(max_length=5)
    sectorCode = models.CharField(max_length=1)
    streetName = models.CharField(max_length=100)
    house = models.IntegerField()
    flat = models.IntegerField()
    postCode = models.CharField(max_length=20)
    cadastreNumber = models.CharField(max_length=36)
    shippingCountryCode = models.CharField(max_length=3)
    shippingSoato = models.CharField(max_length=10)
    shippingVillageCode = models.CharField(max_length=5)
    shippingSectorCode = models.CharField(max_length=1)
    shippingStreetName = models.CharField(max_length=100)
    shippingHouse = models.IntegerField()
    shippingFlat = models.IntegerField()
    shippingPostCode = models.CharField(max_length=20)
    shippingCadastreNumber = models.CharField(max_length=36)
    director_lastname = models.CharField(max_length=50)
    director_firstname = models.CharField(max_length=50)
    director_middlename = models.CharField(max_length=50)
    director_gender = models.CharField(max_length=1)
    director_nationality = models.CharField(max_length=4)
    director_ctzn = models.CharField(max_length=3)
    director_passportSeries = models.CharField(max_length=2)
    director_passportNumber = models.IntegerField()
    director_pinfl = models.CharField(max_length=14)
    director_tin = models.CharField(max_length=9)
    director_phone = models.CharField(max_length=12)
    director_email = models.CharField(max_length=40)
    mfo = models.CharField(max_length=5)
    paymentAccount = models.CharField(max_length=20)
    extraActivityType = models.CharField(max_length=4)

    def __str__(self):
        return self.name
