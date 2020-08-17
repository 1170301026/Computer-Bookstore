import xadmin

# Register your models here.
from django.contrib import admin

from order.models import OrderInfo

xadmin.site.register(OrderInfo)
