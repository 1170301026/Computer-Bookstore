from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^register_handle/$', views.register_handle, name='register_handle'),  # 用户注册
    url(r'^login/$', views.login, name='login'),  # 显示登录界面
    url(r'^login_check/$', views.login_check, name='login_check'),  # 用户登录校验
    url(r'^logout/$', views.logout, name='logout'),  # 退出用户登录
    url(r'^address/$', views.address, name='address'),  # 用户中心-地址页
    url(r'^$', views.user, name='user'),
    url(r'^order/(?P<page>\d+)?/?$', views.order, name='order'),
    url(r'^active/(?P<token>.*)/$', views.register_active, name='active'),  # 用户激活
]
