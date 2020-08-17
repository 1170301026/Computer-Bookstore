"""Bookstore URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import xadmin
from django.conf.urls import url
from django.contrib import admin
from django.urls import include
from xadmin.plugins import xversion
xversion.register_models()
urlpatterns = [
    url(r'^', include(('books.urls', 'books'), namespace='books')),
    url(r'^admin/', xadmin.site.urls),
    url(r'^user/', include(('users.urls', 'users'), namespace='user')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^cart/', include(('cart.urls', 'cart'), namespace='cart')),
    url(r'^order/', include(('order.urls', 'order'), namespace='order')),
    url(r'^search/', include('haystack.urls')),
]
