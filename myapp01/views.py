from django.shortcuts import render,redirect,HttpResponse
import re
from .models import RegisterUser

# 注册页面
def register(request):
    if request.method=='GET':
        return render(request,'register.html')
    else:
    # 接受数据
        email=request.POST.get("email")
        password=request.POST.get("pwd")

        if not all([email, password]):
        # 数据不完整
            return render(request, 'register.html', {"errmsg": "数据不完整"})
    # 检验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return render(request,'register.html',{"msg":'邮箱格式不正确'})

    # 检验密码长度
        if len(password) < 9:
            return render(request, 'register.html', {"emsg": "密码长度必须为 9 位以上"})

    # 进行业务处理,进行用户注册
        user=RegisterUser()
        user.reg_mai=email
        user.reg_pwd=password
        user.save()

    # 返回应答
        return render(request,'login.html')


def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        # 接受数据
        email = request.POST.get("email")
        password = request.POST.get("pwd")
        # 打印调试信息
        # print(f"Email: {email}")
        # print(f"Password: {password}")

        # 校验数据
        if not all([email, password]):
            # 数据不完整
            return render(request, 'login.html', {"msg1": "数据不完整"})

        # 检查用户是否存在
        user = RegisterUser.objects.filter(reg_mai=email).first()  # 获取第一个匹配的用户
        if not user:
            # 用户不存在
            return render(request, 'login.html', {'msg2': "用户不存在",})

        # 校验密码（明文比较）
        if password != user.reg_pwd:  # 直接比较明文密码
            return render(request, 'login.html', {"msg3": "密码错误", "email": email})

        # 登录成功，重定向到主页或其他页面
        return render(request,'layout.html')
def index(request):
    return render(request, "index.html")


def layout(request):
    return render(request, "layout.html")


def information(request):
    return render(request, "information.html")


def hotdir(request):
    return render(request, "hotdir.html")


def view(request):
    return render(request, "view.html")


def saying(request):
    return render(request, "saying.html")


def ip(request):
    return render(request, "ip.html")


def soso(request):
    return render(request, "soso.html")


def hotlist(request):
    return render(request,'hot.html')