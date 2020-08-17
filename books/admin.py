import xadmin
from books.models import Books


class BooksAdmin(object):
    search_fields = ['name', 'status']
    list_filter = ['name', 'status']


# Register your models here.
xadmin.site.register(Books, BooksAdmin)  # 在admin中添加有关商品的编辑功能
