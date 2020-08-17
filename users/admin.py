import xadmin

from users.models import Passport


class UserAdmin(object):
    search_fields = ['username']
    list_filter = ['username']


# Register your models here.
xadmin.site.register(Passport, UserAdmin)
