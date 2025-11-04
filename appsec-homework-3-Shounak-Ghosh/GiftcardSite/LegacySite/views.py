import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound
from LegacySite.models import User, Product, Card
from . import extras
from django.views.decorators.csrf import csrf_protect as csrf_protect
from django.contrib.auth import login, authenticate, logout
from django.core.exceptions import ObjectDoesNotExist
import prometheus_client
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

SALT_LEN = 16

# Prometheus counters
graphs = {}
graphs['r_counter'] = Counter('python_request_r_posts', 'The total number of register posts.')
graphs['l_counter'] = Counter('python_request_l_posts', 'The total number of login posts.')
graphs['b_counter'] = Counter('python_request_b_posts', 'The total number of card buy posts.')
graphs['g_counter'] = Counter('python_request_g_posts', 'The total number of card gift posts.')
graphs['u_counter'] = Counter('python_request_u_posts', 'The total number of card use posts.')

# New: Counter for 404s caused by DB errors
database_error_return_404 = Counter('database_error_return_404', 'Counts database errors resulting in 404s')

# Create your views here.
def index(request): 
    context = {'user': request.user}
    return render(request, "index.html", context)

def register_view(request):
    if request.method == 'GET':
        return render(request, "register.html", {'method': 'GET'})
    else:
        graphs['r_counter'].inc()
        context = {'method': 'POST'}
        uname = request.POST.get('uname', None)
        pword = request.POST.get('pword', None)
        pword2 = request.POST.get('pword2', None)
        assert (None not in [uname, pword, pword2])
        if pword != pword2:
            context["success"] = False
            return render(request, "register.html", context)
        salt = extras.generate_salt(SALT_LEN)
        hashed_pword = extras.hash_pword(salt, pword)
        hashed_pword = salt.decode('utf-8') + '$' + hashed_pword
        u = User(username=uname, password=hashed_pword)
        u.save()
        return redirect("index.html")

def login_view(request):
    if request.method == "GET":
        return render(request, "login.html", {'method': 'GET', 'failed': False})
    else:
        graphs['l_counter'].inc()
        context = {'method': 'POST'}
        uname = request.POST.get('uname', None)
        pword = request.POST.get('pword', None)
        assert (None not in [uname, pword])
        user = authenticate(username=uname, password=pword)
        if user is not None:
            context['failed'] = False
            login(request, user)
            print("Logged in user")
        else:
            context['failed'] = True
            return render(request, "login.html", context)
        return redirect("index.html")

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect("index.html")

def buy_card_view(request, prod_num=0):
    if request.method == 'GET':
        context = {"prod_num": prod_num}
        director = request.GET.get('director', None)
        if director is not None:
            context['director'] = director
        try:
            prod = Product.objects.get(product_id=prod_num or 1) 
        except:
            database_error_return_404.inc()
            return HttpResponseNotFound("ERROR: 404 Not Found.")
        context['prod_name'] = prod.product_name
        context['prod_path'] = prod.product_image_path
        context['price'] = prod.recommended_price
        context['description'] = prod.description
        return render(request, "item-single.html", context)
    elif request.method == 'POST':
        graphs['b_counter'].inc()
        prod_num = prod_num or 1
        num_cards = len(Card.objects.filter(user=request.user))
        card_file_path = f"/tmp/addedcard_{request.user.id}_{num_cards + 1}.gftcrd'"
        card_file_name = "newcard.gftcrd"
        prod = Product.objects.get(product_id=prod_num)
        amount = request.POST.get('amount', prod.recommended_price)
        extras.write_card_data(card_file_path, prod, amount, request.user)
        with open(card_file_path, 'rb') as card_file:
            card = Card(data=card_file.read(), product=prod, amount=amount, fp=card_file_path, user=request.user)
            card.save()
            card_file.seek(0)
            response = HttpResponse(card_file, content_type="application/octet-stream")
            response['Content-Disposition'] = f"attachment; filename={card_file_name}"
            return response
    else:
        return redirect("/buy/1")

def gift_card_view(request, prod_num=0):
    context = {"prod_num": prod_num}
    if request.method == "GET":
        context['user'] = None
        director = request.GET.get('director', None)
        if director:
            context['director'] = director
        try:
            prod = Product.objects.get(product_id=prod_num or 1)
        except:
            database_error_return_404.inc()
            return HttpResponseNotFound("ERROR: 404 Not Found.")
        context['prod_name'] = prod.product_name
        context['prod_path'] = prod.product_image_path
        context['price'] = prod.recommended_price
        context['description'] = prod.description
        return render(request, "gift.html", context)
    elif request.method == "POST":
        graphs['g_counter'].inc()
        prod_num = prod_num or 1
        user = request.POST.get('username', None)
        if not user:
            return HttpResponseNotFound("ERROR 404")
        try:
            user_account = User.objects.get(username=user)
        except:
            database_error_return_404.inc()
            user_account = None
        if user_account is None:
            context['user'] = None
            return render(request, "gift.html", context)
        context['user'] = user_account
        num_cards = len(Card.objects.filter(user=user_account))
        card_file_path = f"/tmp/addedcard_{user_account.id}_{num_cards + 1}.gftcrd'"
        prod = Product.objects.get(product_id=prod_num)
        amount = request.POST.get('amount', prod.recommended_price)
        extras.write_card_data(card_file_path, prod, amount, user)
        with open(card_file_path, 'rb') as card_file:
            card = Card(data=card_file.read(), product=prod, amount=amount, fp=card_file_path, user=user_account)
            card.save()
        return render(request, "gift.html", context)

def use_card_view(request):
    context = {'card_found': None}
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return redirect("login.html")
        try:
            user_cards = Card.objects.filter(user=request.user).filter(used=False)
        except ObjectDoesNotExist:
            user_cards = None
        context['card_list'] = user_cards
        context['card'] = None
        return render(request, 'use-card.html', context)
    elif request.method == "POST" and request.POST.get('card_supplied', False):
        graphs['u_counter'].inc()
        context['card_list'] = None
        card_file_data = request.FILES['card_data']
        card_fname = request.POST.get('card_fname', '')
        card_file_path = f'/tmp/{card_fname or "newcard"}_{request.user.id}_parser.gftcrd'
        card_data = extras.parse_card_data(card_file_data.read(), card_file_path)
        signature = json.loads(card_data)['records'][0]['signature']
        card_query = Card.objects.raw('select id from LegacySite_card where data = \'%s\'' % signature)
        user_cards = Card.objects.raw('select id, count(*) as count from LegacySite_card where LegacySite_card.user_id = %s' % str(request.user.id))
        card_query_string = "".join(str(c) + '\n' for c in card_query)
        if len(card_query) == 0:
            card_file_path = f'/tmp/{card_fname or "newcard"}_{request.user.id}_{user_cards[0].count + 1}.gftcrd'
            with open(card_file_path, 'w') as fp:
                fp.write(card_data)
            card = Card(data=card_data, fp=card_file_path, user=request.user, used=True)
        else:
            context['card_found'] = card_query_string
            try:
                card = Card.objects.get(data=card_data)
                card.used = True
            except ObjectDoesNotExist:
                card = None
        context['card'] = card
        return render(request, "use-card.html", context)
    elif request.method == "POST":
        graphs['u_counter'].inc()
        card = Card.objects.get(id=request.POST.get('card_id', None))
        card.used = True
        card.save()
        context['card'] = card
        try:
            user_cards = Card.objects.filter(user=request.user).filter(used=False)
        except ObjectDoesNotExist:
            user_cards = None
        context['card_list'] = user_cards
        return render(request, "use-card.html", context)
    return HttpResponse("Error 404: Internal Server Error")

def metrics_view(request):
    res = []
    for key, value in graphs.items():
        res.append(prometheus_client.generate_latest(value))
    res.append(prometheus_client.generate_latest(database_error_return_404))
    return HttpResponse(b''.join(res), content_type="text/plain")
    # return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
