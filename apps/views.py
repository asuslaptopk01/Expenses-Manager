import json
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from redis import Redis

from apps.functions import otp_generator, users_balance, send_email
from apps.models import User, Operation, Category

rd = Redis(host='redis', port=6380)


def register_view(request):
    if request.POST:
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        errors = {}
        if not name:
            errors['name'] = "Введите свое имя!"

        if not str(email).endswith('@gmail.com'):
            errors['email'] = "Адрес электронной почты недействителен! Проверьте свою почту!"

        user = User.objects.filter(email=email).first()
        if user:
            errors[
                'email'] = 'Этот адрес электронной почты уже зарегистрирован. Пожалуйста, попробуйте другой или войдите в систему!'

        if len(password) < 4:
            errors['password'] = "Пароль слишком короткий. Пожалуйста, используйте 4 или более символов!"

        if errors:
            return JsonResponse({'success': False, 'errors': errors, 'status': 400})
        otp_code = otp_generator()
        send_email(email, otp_code)
        data = json.dumps({"name": name, "email": email, "password": password, "otp": otp_code})
        rd.setex(email, 90, data)
        return JsonResponse({'success': True, 'redirect': f'/auth/otp'})
    return render(request, 'auth/register.html')


def otp_view(request):
    if request.POST:
        email = request.POST.get('email', '').strip()
        raw_data = rd.get(email)
        if raw_data is None:
            return JsonResponse({'success': False, 'message': 'Срок действия истек или электронная почта не найдено!'})
        data = rd.get(email)
        data = json.loads(raw_data)
        input_otp = request.POST.get('otp')
        otp_code = data.get('otp')

        if input_otp and input_otp.isdigit() and int(input_otp) == int(otp_code):
            name = data.get("name")
            password = data.get('password')
            hash_ps = make_password(password=password)
            User(first_name=name, email=email, password=hash_ps).save()
            return JsonResponse({'success': True, 'redirect': '/auth/login'})

        return JsonResponse({'success': False, 'redirect': '/auth/register', 'message': 'OTP-код неверный!'})
    return render(request, 'auth/otp.html')


def login_view(request):
    if request.POST:
        email = request.POST.get('email')
        password = request.POST.get('password')

        errors = {}
        if not str(email).endswith('@gmail.com'):
            errors['email'] = "Адрес электронной почты недействителен! Проверьте свою почту!"

        if len(password) < 4:
            errors['password'] = "Пароль слишком короткий. Пожалуйста, используйте 4 или более символов!"

        if errors:
            return JsonResponse({'success': False, 'errors': errors, 'status': 400})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Адрес электронной почты не найден. Сначала зарегистрируйтесь!'})

        if check_password(password, user.password):
            login(request, user=user)
            return redirect('main')
        return JsonResponse({'error': 'Неверный пароль или адрес электронной почты!'})

    return render(request, 'auth/login.html')


@login_required(login_url='/auth/login')
def main_page_view(request):
    user = request.user
    balance = users_balance(user)
    date_to = timezone.now()
    date_from = date_to - timedelta(days=30)
    operations = Operation.objects.filter(user=user, date__range=(date_from, date_to)).order_by('-date')

    total_income = Operation.objects.filter(user=user, type='income').aggregate(
        total_income=Sum('amount'))['total_income'] or Decimal('0.00')
    income_count = Operation.objects.filter(user=user, type='income').count()
    total_expense = Operation.objects.filter(user=user, type='expense').aggregate(
        total_expense=Sum('amount'))['total_expense'] or Decimal('0.00')
    expense_count = Operation.objects.filter(user=user, type='expense').count()

    expense = (
        Operation.objects.filter(user=user, type='expense').values('category__name').annotate(total=Sum('amount')))
    income = Operation.objects.filter(user=user, type='income').values('category__name').annotate(total=Sum('amount'))

    monthly_data = Operation.objects.filter(
        user=request.user,
        date__year=timezone.now().year).annotate(
        month=TruncMonth('date')).values('month', 'type', 'category__name').annotate(
        total=Sum('amount'))
    monthly = {i: {'expense': {}, 'income': {}} for i in range(12)}

    for entry in monthly_data:
        month_idx = entry['month'].month - 1
        op_type = entry['type']
        cat_name = entry['category__name']
        total = float(entry['total'])

        monthly[month_idx][op_type][cat_name] = total

    chart_data = {
        'expense': {item['category__name']: float(item['total']) for item in expense},
        'income': {item['category__name']: float(item['total']) for item in income},
        'months': monthly,
    }

    context = {
        "first_name": user.first_name,
        'balance': balance,
        'operations': operations,
        'total_income': total_income,
        'income_count': income_count,
        'total_expense': total_expense,
        'expense_count': expense_count,
        'chart_data_json': json.dumps(chart_data),
        'expense': expense,
        'income': income,
    }
    return render(request, "main/main.html", context=context)



def add_income_view(request):
    categories = Category.objects.filter(operation_type='income')
    if request.POST:
        user = request.user
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        date = request.POST.get('date')
        time = request.POST.get('time')
        description = request.POST.get('description', '')

        errors = {}
        if not amount:
            errors['amount'] = ['Требуется указать сумму!']
        else:
            try:
                amount = float(amount)
                if amount <= 0:
                    errors['amount'] = ['Сумма должна быть больше 0!']
            except ValueError:
                errors['amount'] = ['Введите действительный номер!']

        if not category_id:
            errors['category'] = ['Категория обязательна!']

        if not date:
            errors['date'] = ['Дата обязательна!']
        else:
            try:
                if date > datetime.now().strftime('%Y-%m-%d'):
                    errors['date'] = ['Добавить расходы на будущие даты невозможно!']
            except Exception:
                errors['date'] = ['Введите действительную дату!']
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        try:
            category = Category.objects.get(id=category_id)
            Operation.objects.create(
                type='income',
                amount=amount,
                category=category,
                date=date,
                description=description,
                user=user
            )
            return JsonResponse({'success': True})
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'errors': {'category': ['Неверная категория!']}}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': 'Error!'}, status=400)
    return render(request, 'main/income.html', {'categories': categories})



def add_expense_view(request):
    categories = Category.objects.filter(operation_type='expense')
    if request.POST:
        user = request.user
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        date = request.POST.get('date')
        description = request.POST.get('description', '')

        errors = {}
        if not amount:
            errors['amount'] = ['Требуется указать сумму!']
        else:
            balance = users_balance(user)
            if Decimal(amount) > Decimal(balance):
                errors['amount'] = ['Недостаточный баланс. Вы не можете добавить этот расход!']
            try:
                amount = float(amount)
                if amount <= 0:
                    errors['amount'] = ['Сумма должна быть больше 0!']
            except ValueError:
                errors['amount'] = ['Введите действительный номер!']

        if not category_id:
            errors['category'] = ['Категория обязательна!']

        if not date:
            errors['date'] = ['Дата обязательна!']
        else:
            try:
                if date > datetime.now().strftime('%Y-%m-%d'):
                    errors['date'] = ['Добавить расходы на будущие даты невозможно!']
            except Exception:
                errors['date'] = ['Введите действительную дату!']
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        try:
            category = Category.objects.get(id=category_id)
            Operation.objects.create(
                type='expense',
                amount=amount,
                category=category,
                date=date,
                description=description,
                user=user
            )
            return JsonResponse({'success': True})
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'errors': {'category': ['Неверная категория!']}}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': 'Error!'}, status=400)
    return render(request, 'main/expense.html', {'categories': categories})


def edit_operation_view(request, id):
    operation = get_object_or_404(Operation, user=request.user, id=id)
    if request.POST:
        type_ = request.POST.get('type') or operation.type
        amount = request.POST.get('amount') or operation.amount
        category = request.POST.get('category') or operation.category_id
        date = request.POST.get('date') or operation.date.strftime('%Y-%m-%d')
        time = request.POST.get('time') or operation.date.strftime('%H:%M')
        desc = request.POST.get('description', operation.description)

        errors = {}
        if operation.type == 'expense' and Decimal(users_balance(request.user)) < Decimal(amount):
            errors['amount'] = 'Вы не можете добавить расходов, превышающих ваш баланс!'
        if date > datetime.now().strftime('%Y-%m-%d'):
            errors['date'] = ['Добавить расходы на будущие даты невозможно!']
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        operation.type = type_
        operation.amount = amount
        operation.category_id = category
        operation.date = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        operation.description = desc
        operation.save()
        return JsonResponse({'success': True, 'redirect': '/'})

    return render(request, 'main/edit_operation.html', {
        'operation': operation,
        'categories': Category.objects.all(),
    })


def delete_operation_view(request, id):
    operation = get_object_or_404(Operation, user=request.user, id=id)
    if request.POST:
        operation.delete()
        return JsonResponse({'success': True, 'redirect': '/'})
    return JsonResponse({'success': False})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/auth/login/')
def profile_edit_view(request):
    user = request.user
    if request.POST:
        field = request.POST.get('field')
        new_info = request.POST.get('value', '').strip()
        user = request.user

        if field == 'name':
            if not new_info:
                return JsonResponse({'success': False, 'error': 'Пустое имя!'})
            user.first_name = new_info
            user.save()
            return JsonResponse({'success': True, 'data': new_info})
        elif field == 'email':
            if not new_info.endswith('@gmail.com'):
                return JsonResponse({'success': False, 'error': 'Неверный адрес электронной почты!'})
            if User.objects.filter(email=new_info).exists():
                return JsonResponse(
                    {'success': False, 'error': 'Пользователь с таким адресом электронной почты уже существует!'})
            user.email = new_info
            user.save()
            return JsonResponse({'success': True, 'data': new_info})
        elif field == 'password':
            current_pw = request.POST.get('current_password', '')
            if not check_password(current_pw, user.password):
                return JsonResponse({'success': False, 'error': 'Пароль неверный!'})
            if len(new_info) < 4:
                return JsonResponse({'success': False, 'error': 'Пароль слишком короткий!'})
            user.password = make_password(new_info)
            user.save()
            return JsonResponse(
                {'success': True, 'fullname': user.first_name, 'email': user.email, 'password': user.password})
    return render(request, 'main/profile.html',
                  {'fullname': user.first_name,
                   'email': user.email,
                   'password': user.password})


@login_required(login_url='/auth/login/')
def profile_delete_view(request):
    if request.POST:
        user = request.user
        logout(request)
        user.delete()
        return JsonResponse({'success': True, 'redirect': '/auth/register/'})
    return JsonResponse({'success': False})