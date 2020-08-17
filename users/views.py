from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse

import settings
from order.models import OrderInfo, OrderBooks
from users.models import Passport, Address
import re
from django.shortcuts import render, redirect, reverse
from utils.decorators import login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired
from users.tasks import send_active_email


# Create your views here.

def register(request):
    """显示用户注册页面"""
    return render(request, 'users/register.html')


def register_handle(request):
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')

    # 进行数据校验
    if not all([username, password, email]):
        # 有数据为空
        return render(request, 'users/register.html', {'errmsg': '参数不能为空！'})

    # 判断邮箱是否合法
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        # 邮箱格式不合法
        return render(request, 'users/register.html', {'errmsg': '邮箱不合法！'})
    p = Passport.objects.check_passport(username=username)
    if p:
        return render(request, 'users/register.html', {'errmsg': '用户名已存在！'})

    # 进行业务处理：注册，向账户系统中添加账户
    # Passport.objects.create(username=username,password=password,email=email)
    passport = Passport.objects.add_one_passport(username=username, password=password, email=email)
    # 生成激活的token itsdangerous
    serializer = Serializer(settings.SECRET_KEY, 3600)
    token = serializer.dumps({'confirm': passport.id})  # 返回bytes
    token = token.decode()

    # 给用户的邮箱发激活邮件
    send_active_email.delay(token, username, email)

    # 注册完，返回主页
    return redirect(reverse('books:index'))


def register_active(request, token):
    """用户账户激活"""
    serializer = Serializer(settings.SECRET_KEY, 3600)
    try:
        info = serializer.loads(token)
        passport_id = info['confirm']
        # 进行用户激活
        passport = Passport.objects.get(id=passport_id)
        passport.is_active = True
        passport.save()
        # 跳转的登录页
        return redirect(reverse('user:login'))
    except SignatureExpired:
        # 链接过期
        return HttpResponse('激活链接已过期')


def login(request):
    """显示登录页面"""
    if request.COOKIES.get("username"):
        username = request.COOKIES.get("username")
        checked = 'checked'
    else:
        username = ''
        checked = ''
    context = {
        'username': username,
        'checked': checked,
    }
    return render(request, 'users/login.html', context)


def login_check(request):
    """进行用户登录校验"""
    # 1.获取数据
    username = request.POST.get('username')
    password = request.POST.get('password')
    remember = request.POST.get('remember')

    # 2.数据校验
    if not all([username, password, remember]):
        # 有数据为空
        return JsonResponse({'res', 2})

    # 3.进行处理：根据用户名和密码查找账户信息
    passport = Passport.objects.get_one_passport(username=username, password=password)

    if passport:
        next_url = reverse('books:index')
        jres = JsonResponse({'res': 1, 'next_url': next_url})

        # 判断是否需要记住用户名
        if remember == 'true':
            # 记住用户名
            jres.set_cookie('username', username, max_age=7 * 24 * 3600)
        else:
            # 不记住用户名
            jres.delete_cookie('username')

        # 记住用户登录状态
        request.session['islogin'] = True
        request.session['username'] = username
        request.session['passport_id'] = passport.id
        return jres
    else:
        # 用户名或密码错误：
        return JsonResponse({'res': 0})


def logout(request):
    """用户退出登录"""
    # 清空用户会话信息
    request.session.flush()
    # 返回首页
    return redirect(reverse('books:index'))


@login_required
def user(request):
    """用户中心-信息页"""
    passport_id = request.session.get('passport_id')
    # 获取用户基本信息
    addr = Address.objects.get_default_address(passport_id=passport_id)

    books_li = []

    context = {
        'addr': addr,
        'page': 'user',
        'books_li': books_li
    }

    return render(request, 'users/user_center_info.html', context)


@login_required
def address(request):
    """用户中心-地址页"""
    # 获取登录用户的id
    passport_id = request.session.get('passport_id')

    if request.method == 'GET':
        # 显示地址页面
        # 查询用户的默认地址
        addr = Address.objects.get_default_address(passport_id=passport_id)
        return render(request, 'users/user_center_site.html', {'addr': addr, 'page': 'address'})
    else:
        # 添加收货地址
        # 1.接收数据
        recipient_name = request.POST.get('username')
        recipient_addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recipient_phone = request.POST.get('phone')

    # 2.进行校验
    if not all([recipient_name, recipient_addr, zip_code, recipient_phone]):
        return render(request, 'users/user_center_site.html', {'errmsg': '参数不能为空！'})

    # 3.添加收货地址
    Address.objects.add_one_address(passport_id=passport_id,
                                    recipient_name=recipient_name,
                                    recipient_addr=recipient_addr,
                                    zip_code=zip_code,
                                    recipient_phone=recipient_phone)
    # 4.返回应答
    return redirect(reverse('user:address'))


@login_required
def order(request, page):
    """用户中心-订单页"""
    # 查询用户的订单信息
    passport_id = request.session.get('passport_id')

    # 获取订单信息
    order_li = OrderInfo.objects.filter(passport_id=passport_id)

    # 遍历获取订单的商品信息
    # orders->OrderInfo实例对象
    for orders in order_li:
        # 根据订单id查询订单商品信息
        order_id = orders.order_id
        order_books_li = OrderBooks.objects.filter(order_id=order_id)

        # 计算商品的小计
        # order_books ->OrderBooks实例对象
        for order_books in order_books_li:
            count = order_books.count
            price = order_books.price
            amount = count * price
            # 保存订单中每一个商品的小计
            order_books.amount = amount

        # 给orders对象动态增加一个属性order_books_li,保存订单中商品的信息
        orders.order_books_li = order_books_li

    paginator = Paginator(order_li, 3)  # 每页显示3个订单

    num_pages = paginator.num_pages

    if not page:  # 首次进入时默认进入第一页
        page = 1
    if page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)

    order_li = paginator.page(page)

    if num_pages < 5:
        pages = range(1, num_pages + 1)
    elif page <= 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages - 4, num_pages + 1)
    else:
        pages = range(page - 2, page + 3)

    context = {
        'order_li': order_li,
        'pages': pages,
    }

    return render(request, 'users/user_center_order.html', context)
