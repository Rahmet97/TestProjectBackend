from django.db.models import enums


class VpsDevicePriceEnum(enums.IntegerChoices):
    CPU = 78000   # default per a core
    RАМ = 12000  # default GB
    HHD = 850  # default GB
    SSD = 2500  # default GB
    INTERNET = 20000  # default MBit/s
    TASIX = 10000  # default MBit/s
    IMUT = 15000  # default MBit/s
    IPV4_ADDRESS = 25000
