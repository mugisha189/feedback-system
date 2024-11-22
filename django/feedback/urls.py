from django.urls import path
from .views import product_create, product_list, feedback_list, feedback_create
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/products/', permanent=True)),
    path('products/', product_list, name='product_list'),
    path('products/new/', product_create, name='product_create'),
    path('products/<int:product_id>/feedbacks/', feedback_list, name='feedback_list'),
    path('products/<int:product_id>/feedbacks/new/', feedback_create, name='feedback_create'),
]
