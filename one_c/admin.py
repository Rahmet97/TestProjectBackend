from django.contrib import admin
from .models import *

admin.site.register((Status, Invoice, Nomenclature))
