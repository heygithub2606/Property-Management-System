from .views import *
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)

# Define the schema view for Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="Your API",
      default_version='v1',
      description="API description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@yourapi.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', index, name='index'),
    path('property/search/', PropertySearchView.as_view(), name='property-search'),
    path('services/', services, name='services'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('all-properties/', all_properties, name='all_properties'),
    path('property/<int:pk>/detail/', view_detail, name='view_detail'),

    path('register/', register, name='register'),
    path('login/', user_login, name='user_login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/', reset_password, name='reset_password'),
    path('password-reset-success/', password_reset_success, name='password_reset_success'),

    path('landlord-dashboard/', landlord_dashboard, name='landlord_dashboard'),
    path('properties-create/', PropertyCreateView.as_view(), name='property-create'),
    path('properties/<int:pk>/', PropertyView.as_view(), name='property-detail'),
    path('properties/edit/<int:pk>/', EditPropertyView.as_view(), name='property-edit'),
    path('properties/delete/<int:pk>/', DeletePropertyView.as_view(), name='property-delete'),
    path('properties/', PropertyListView.as_view(), name='property-list'),
    path('property-success/', property_success, name='property-success'),
    path('profile/', profile_view, name='profile'),

    path('tenant/dashboard/', tenant_dashboard, name='tenant_dashboard'),
    path('property/<int:pk>/contact/', contact_landlord, name='contact_landlord'),

    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),


    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
