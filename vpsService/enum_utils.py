from django.db.models import enums


class VpsDevicePriceEnum(enums.IntegerChoices):
    CPU = 88312   # default per a core
    RАМ = 12068  # default GB
    HHD = 728  # default GB
    SSD = 2408  # default GB
    INTERNET = 55500  # default MBit/s -> free <= 10 MBit/s
    TASIX = 1400  # default MBit/s -> free <= 100 MBit/s
    IMUT = 10000  # default MBit/s -> test demo
    IPV4_ADDRESS = 24000
