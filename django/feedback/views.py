from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.mail import send_mail
from .models import Product, Feedback
from .forms import ProductForm, FeedbackForm
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignupForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()
            login(request, user)
            return redirect("product_list")
    else:
        form = SignupForm()
    print(form.errors)
    return render(request, "feedback/signup.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("product_list")
            else:
                form.add_error(None, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "feedback/login.html", {"form": form})


@login_required
def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "feedback/product_form.html", {"form": form})


def product_list(request):
    search_query = request.GET.get("search", "")
    items_per_page = request.GET.get("items_per_page", 10)

    if request.user.is_authenticated:
        products = Product.objects.filter(owner=request.user)
    else:
        products = Product.objects.all()

    if search_query:
        products = products.filter(name__icontains=search_query)

    if not request.user.is_authenticated:
        owners = Product.objects.values_list("owner__username", flat=True).distinct()
    else:
        owners = None

    paginator = Paginator(products, items_per_page)
    page_number = request.GET.get("page")
    products_page = paginator.get_page(page_number)

    return render(
        request,
        "feedback/product_list.html",
        {
            "products": products_page,
            "owners": owners,
            "search_query": search_query,
            "items_per_page": items_per_page,
        },
    )


def feedback_list(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user != product.owner:
        return redirect("/")

    feedbacks = Feedback.objects.filter(product=product)

    search_query = request.GET.get("search", "")
    if search_query:
        feedbacks = feedbacks.filter(customer_name__icontains=search_query)

    rating_filter = request.GET.get("rating")
    if rating_filter:
        feedbacks = feedbacks.filter(rating=rating_filter)

    paginator = Paginator(feedbacks, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "feedback/feedback_list.html",
        {"product": product, "page_obj": page_obj},
    )


def feedback_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = FeedbackForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            if Feedback.objects.filter(product=product, email=email).exists():
                messages.error(
                    request, "You have already submitted feedback for this product."
                )
                return redirect("feedback_create", product_id=product.id)

            feedback = form.save(commit=False)
            feedback.product = product
            feedback.save()

            send_mail(
                "New Feedback Received",
                f"You have received new feedback for {product.name}.",
                "your_email@gmail.com",
                [product.owner.email],
                fail_silently=False,
            )
            return redirect("/products")
    else:
        form = FeedbackForm()

    return render(
        request, "feedback/feedback_form.html", {"form": form, "product": product}
    )
