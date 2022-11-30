from django.contrib import admin
from .models import *

admin.site.register((
    Service,
    SavedService,
    Element,
    UserContractTarifDevice,
    UserDeviceCount,
    Device,
    Offer,
    Document,
    Tarif,
    TarifElement,
    Contract,
    ContractStatus,
    AgreementStatus,
    Status,
    Contracts_Participants,
    ConnetMethod
))
