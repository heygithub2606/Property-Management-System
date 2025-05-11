from django.shortcuts import render,redirect,get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.contrib import messages  
from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from .models import Property
from .serializers import PropertySerializer
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from rest_framework import status
from django.views.generic import ListView
from django.core.paginator import Paginator
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.db.models import Count
from django.utils import timezone
from django.db.models.functions import ExtractDay, ExtractMonth

from drf_yasg import openapi
# Create your views here.
def index(request):
    properties = Property.objects.all()  # Adjust the query as needed
    return render(request, 'index.html', {'properties': properties})


class PropertySearchView(APIView):
    """
    View to search for properties without authentication required.
    """
    permission_classes = [AllowAny]  # Allow any user to access this view

    def get(self, request):
        query = request.GET.get('query')  # Get the search query from the URL
        page_number = request.GET.get('page', 1)  # Get page number, default to 1
        properties = Property.objects.all()  # Get all properties initially

        # Apply filters based on query
        if query:
            properties = properties.filter(
                models.Q(title__icontains=query) |  # Filter by title
                models.Q(city__icontains=query) |  # Filter by city
                models.Q(price__icontains=query)   # Filter by price
                
            )

        # Set up pagination (e.g., 6 properties per page)
        paginator = Paginator(properties, 6)
        paginated_properties = paginator.get_page(page_number)

        # Check if the request expects JSON or HTML
        if request.headers.get('Accept') == 'application/json':
            # Prepare JSON response for API/Swagger
            properties_data = [
                {
                    'id': property.id,
                    'title': property.title,
                    'city': property.city,
                    'price': property.price,
                    'location_latitude': property.location_latitude,
                    'location_longitude': property.location_longitude
                }
                for property in paginated_properties
            ]
            return Response({
                'properties': properties_data,
                'query': query,
                'page': paginated_properties.number,
                'total_pages': paginated_properties.paginator.num_pages,
                'has_previous': paginated_properties.has_previous(),
                'has_next': paginated_properties.has_next()
            }, status=status.HTTP_200_OK)
        else:
            # Render HTML template for web requests with paginated properties
            return render(request, 'property_search_results.html', {
                'properties': paginated_properties,
                'query': query
            })  
        

def services(request):
    return render(request, 'services.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def all_properties(request):
    properties_list = Property.objects.all()

    # Get filter values from the request
    title = request.GET.get('title')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    status = request.GET.get('status')

    # Apply filters if they exist
    if title:
        properties_list = properties_list.filter(title__icontains=title)
    if min_price:
        properties_list = properties_list.filter(price__gte=min_price)
    if max_price:
        properties_list = properties_list.filter(price__lte=max_price)
    if status:
        properties_list = properties_list.filter(status=status)

    # Pagination with 6 properties per page
    paginator = Paginator(properties_list, 6)
    page_number = request.GET.get('page')
    properties = paginator.get_page(page_number)

    return render(request, 'all_properties.html', {
        'properties': properties,
        'title': title,
        'min_price': min_price,
        'max_price': max_price,
        'status': status
    })


def view_detail(request, pk):
    # Fetch the property object using the primary key (pk)
    property_instance = get_object_or_404(Property, pk=pk)

    # Check if the user is authenticated
    if request.user.is_authenticated:
        back_url = 'tenant_dashboard'  # Back to tenant dashboard if logged in
    else:
        back_url = 'index'  # Back to index if not logged in

    # Pass the property and back_url to the template
    return render(request, 'view_detail.html', {
        'property': property_instance,
        'back_url': back_url,
        'images': property_instance.images.all()  # Get all images for the property
    })



# Registration View
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('user_login')
        else:
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, error)  # Add each error message
    else:
        form = RegistrationForm()
    return render(request, 'login.html', {'form': form})

def user_login(request):
    form = AuthenticationForm(request, data=request.POST or None)
    print("user_login view called")  # Check if view is called

    if request.method == 'POST':
        print("POST request received")  # Check if POST is working
        
        if form.is_valid():
            print("Form is valid")  # Check if form is valid
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                print("User authenticated")  # Check if user is authenticated
                login(request, user)
                
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                try:
                    profile = Profile.objects.get(user=user)
                    print("User Profile:", profile)  # Check if profile is fetched
                    
                    if profile.role == 'landlord':
                        response = redirect('landlord_dashboard')
                    elif profile.role == 'tenant':
                        response = redirect('tenant_dashboard')
                    else:
                        messages.error(request, "User role not recognized.")
                        return render(request, 'login.html', {'form': form})

                    response.set_cookie(key='access_token', value=access_token, httponly=True)
                    return response

                except Profile.DoesNotExist:
                    print("Profile not found.")  # Debug for profile existence
                    messages.error(request, "Profile not found.")
                    return render(request, 'login.html', {'form': form})

            else:
                print("Authentication failed")  # Debug failed authentication
                messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html', {'form': form})



#logout
def logout_view(request):
    auth_logout(request)  # Log the user out using the correct logout function
    return redirect('index') 

# Forgot Password View
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)

            # Construct the reset password URL
            reset_url = request.build_absolute_uri('/reset-password/')  # No token required

            # Send password reset email
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_url}',
                'admin@yourdomain.com',
                [email],
            )

            messages.success(request, 'A password reset link has been sent to your email.')
            return redirect('forgot_password')
        except User.DoesNotExist:
            messages.error(request, 'No user with this email exists.')

    return render(request, 'forgot_password.html')

# Reset Password View
def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        try:
            user = User.objects.get(email=email)
            if new_password == confirm_password:
                user.password = make_password(new_password)
                user.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('password_reset_success')
            else:
                messages.error(request, 'Passwords do not match.')
        except User.DoesNotExist:
            messages.error(request, 'No user with this email exists.')

    return render(request, 'reset_password.html')

# Password Reset Success View
def password_reset_success(request):
    return render(request, 'password_reset_success.html')



@login_required
def landlord_dashboard(request):
    # Get the logged-in user
    user = request.user

    # Get total properties created by the user
    total_properties = Property.objects.filter(created_by=user).count()
    
    # Count properties by status for the logged-in user
    properties_for_rent = Property.objects.filter(created_by=user, status='Rent').count()
    properties_sold = Property.objects.filter(created_by=user, status='Sell').count()
    
    # Get daily data for properties sold by the user
    current_year = timezone.now().year
    current_month = timezone.now().month
    daily_sold_data = (
        Property.objects.filter(status='Sell', created_by=user, created_at__year=current_year, created_at__month=current_month)
        .annotate(day=ExtractDay('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    # Prepare data for charts
    days = [i['day'] for i in daily_sold_data]
    sold_counts = [i['count'] for i in daily_sold_data]

    context = {
        'total_properties': total_properties,
        'properties_for_rent': properties_for_rent,
        'properties_sold': properties_sold,
        'days': days,
        'sold_counts': sold_counts,
    }
    return render(request, 'Landlord/landlord.html', context)



# @method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')  # Exempt CSRF for API requests
class PropertyCreateView(APIView):
    """
    View to create a new property.
    Supports both session-based and token-based authentication.
    """
    authentication_classes = [SessionAuthentication, JWTAuthentication]  # Added JWTAuthentication
    permission_classes = [IsAuthenticated]  # Ensures the user is authenticated

    template_name = 'Landlord/property_create.html'
    success_template = 'Landlord/property_list.html'

    cities  = [
        'Select City',  'Agra', 'Aligarh', 'Allahabad', 'Ambedkar Nagar', 'Amethi', 'Amroha', 
    'Auraiya', 'Azamgarh', 'Baghpat', 'Bahraich', 'Ballia', 'Balrampur',
    'Banda', 'Barabanki', 'Bareilly', 'Basti', 'Bijnor', 'Bulandshahr', 
    'Chandauli','Delhi', 'Etah', 'Etawah', 'Farrukhabad', 'Fatehpur', 'Firozabad', 
    'Ghaziabad', 'Gautam Buddha Nagar', 'Gonda', 'Gorakhpur', 'Greater Noida', 
    'Hamirpur', 'Hapur', 'Hardoi', 'Hathras', 'Jaunpur', 'Jhansi', 'Kannauj', 
    'Kanpur', 'Kasganj', 'Kaushambi', 'Kushinagar', 'Lalitpur', 'Lucknow', 
    'Maharajganj', 'Mainpuri', 'Mathura', 'Meerut', 'Mirzapur', 'Moradabad', 
    'Muzaffarnagar', 'Noida', 'Pilibhit', 'Prayagraj', 'Rae Bareli', 
    'Rampur', 'Saharanpur', 'Sambhal', 'Shahjahanpur', 'Shamli', 
    'Shravasti', 'Siddharthnagar', 'Sitapur', 'Sonbhadra', 'Sultanpur', 
    'Unnao', 'Varanasi'
    ]   

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Success', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                    'description': openapi.Schema(type=openapi.TYPE_STRING),
                    'price': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'city': openapi.Schema(type=openapi.TYPE_STRING),
                    'property_type': openapi.Schema(type=openapi.TYPE_STRING),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'landlord_email': openapi.Schema(type=openapi.TYPE_STRING),
                    'phone_no': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ))
        }
    )
    def get(self, request):
        """
        Handle GET request to render the property creation form for web requests or return default data for APIs.
        """
        if request.headers.get('Accept') == 'application/json':
            # If the request is from Swagger/API, return default JSON data
            response_data = {
                'title': '',
                'description': '',
                'price': 0,
                'city': '',
                'property_type': '',
                'status': '',
                'landlord_email': '',
                'phone_no': ''
            }
            return Response(response_data, status=status.HTTP_200_OK)

        # Render HTML form for web users with city choices
        return render(request, self.template_name, {'cities': self. cities })

    @swagger_auto_schema(request_body=PropertySerializer)
    def post(self, request):
        """
        Handle POST request for property creation via web or API requests.
        """
        # Ensure user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to create a property.")
            return render(request, self.template_name, {'cities': self. cities })

        # Prepare data from request
        data = {
            'title': request.data.get('title'),
            'description': request.data.get('description'),
            'price': float(request.data.get('price', 0)),
            'city': request.data.get('city'),
            'property_type': request.data.get('property_type'),
            'status': request.data.get('status'),
            'landlord_email': request.data.get('landlord_email'),
            'phone_no': request.data.get('phone_no'),
        }

        # Handle image files
        images = request.FILES.getlist('images')
        data['images'] = [{'image': img} for img in images]

        serializer = PropertySerializer(data=data, context={'request': request})

        if serializer.is_valid():
            property_instance = serializer.save(created_by=request.user)
            messages.success(request, "Property created successfully!")

            # Respond based on the request type (API or web)
            if request.headers.get('Accept') == 'application/json':
                return Response({'message': 'Property created successfully!', 'property_id': property_instance.id}, status=status.HTTP_201_CREATED)
            else:
                return redirect('property-list')

        else:
            messages.error(request, "Failed to create property. Please correct the errors.")
            
            # Return errors for API or render form again for web users
            if request.headers.get('Accept') == 'application/json':
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return render(request, self.template_name, {'form': serializer.errors, 'data': data, 'cities': self. cities })

        
@login_required 
def property_success(request):
    """
    View to display success page after property creation.
    """
    return render(request, 'Landlord/property_success.html')

class PropertyListView(ListView):
    model = Property
    template_name = 'Landlord/property_list.html'  # Specify your template path
    context_object_name = 'properties'
    paginate_by = 4  # Optional: Add pagination if needed

    def get_queryset(self):
        # Start with properties created by the user
        queryset = Property.objects.filter(created_by=self.request.user)

        # Get filter parameters from the request
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        status = self.request.GET.get('status')
        title = self.request.GET.get('title')


        # Apply filters if they exist
        if title:
            queryset = queryset.filter(title__icontains=title)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

#read detailed 
# @method_decorator(login_required, name='dispatch')
class PropertyView(APIView):
    """
    View to retrieve and display property details.
    """
    template_name = 'Landlord/property_detail.html'  # Template for property detail
    authentication_classes = [SessionAuthentication, JWTAuthentication]  # Allow both session and JWT authentication
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Fetch the property by ID
        property_instance = get_object_or_404(Property, pk=pk)
        # Serialize the property data
        serializer = PropertySerializer(property_instance)

        # Fetch property images
        property_images = property_instance.images.all()  # Assuming images is the related name for images

        # Check if request is expecting JSON or HTML
        if request.headers.get('Accept') == 'application/json':
            # Return JSON response for API/Swagger requests
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Render the property detail template for HTML response
            return render(request, self.template_name, {
                'property': serializer.data,
                'property_images': property_images  # Pass images to the template
            })



#update property
# @method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class EditPropertyView(APIView):
    """
    View to edit an existing property.
    """
    template_name = 'Landlord/property_edit.html'  # Template for edit form
    authentication_classes = [SessionAuthentication, JWTAuthentication]  # Support both session and JWT authentication
    permission_classes = [IsAuthenticated]

    # List of cities
    cities = [
        'Select City', 'Agra', 'Aligarh', 'Allahabad', 'Ambedkar Nagar', 'Amethi', 'Amroha', 
        'Auraiya', 'Azamgarh', 'Baghpat', 'Bahraich', 'Ballia', 'Balrampur',
        'Banda', 'Barabanki', 'Bareilly', 'Basti', 'Bijnor', 'Bulandshahr', 
        'Chandauli', 'Etah', 'Etawah', 'Farrukhabad', 'Fatehpur', 'Firozabad', 
        'Ghaziabad', 'Gautam Buddha Nagar', 'Gonda', 'Gorakhpur', 'Greater Noida', 
        'Hamirpur', 'Hapur', 'Hardoi', 'Hathras', 'Jaunpur', 'Jhansi', 'Kannauj', 
        'Kanpur', 'Kasganj', 'Kaushambi', 'Kushinagar', 'Lalitpur', 'Lucknow', 
        'Maharajganj', 'Mainpuri', 'Mathura', 'Meerut', 'Mirzapur', 'Moradabad', 
        'Muzaffarnagar', 'Noida', 'Pilibhit', 'Prayagraj', 'Rae Bareli', 
        'Rampur', 'Saharanpur', 'Sambhal', 'Shahjahanpur', 'Shamli', 
        'Shravasti', 'Siddharthnagar', 'Sitapur', 'Sonbhadra', 'Sultanpur', 
        'Unnao', 'Varanasi'
    ]

    def get(self, request, pk):
        property_instance = get_object_or_404(Property, pk=pk)
        serializer = PropertySerializer(property_instance)

        if request.headers.get('Accept') == 'application/json':
            return Response({
                'form': serializer.data,
                'property_images': [image.image.url for image in property_instance.images.all()]  
            }, status=status.HTTP_200_OK)
        else:
            return render(request, self.template_name, {
                'form': serializer.data,
                'property_images': property_instance.images.all(),
                'cities': self.cities  # Add cities to the context for rendering the form
            })

    @swagger_auto_schema(request_body=PropertySerializer)
    def post(self, request, pk):
        property_instance = get_object_or_404(Property, pk=pk)
        serializer = PropertySerializer(property_instance, data=request.data)
        print(serializer)
        if serializer.is_valid():
            serializer.save()  # Save the updated property
            messages.success(request, "Property updated successfully!")

            if request.headers.get('Accept') == 'application/json':
                return Response({'message': 'Property updated successfully!'}, status=status.HTTP_200_OK)
            else:
                return redirect('property-detail', pk=pk)  # Redirect to property detail after update
        else:
            messages.error(request, "Failed to update property. Please correct the errors.")

            if request.headers.get('Accept') == 'application/json':
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return render(request, self.template_name, {
                    'form': serializer.errors,
                    'property_images': property_instance.images.all(),
                    'cities': self.cities  # Include cities in case of errors
                })

# @method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')  # Apply CSRF exemption for API requests
class DeletePropertyView(APIView):
    """
    View to delete an existing property.
    Supports both session-based and token-based authentication.
    """
    authentication_classes = [SessionAuthentication, JWTAuthentication]  # Session and JWT auth
    permission_classes = [IsAuthenticated]  # Authenticated users only

    def dispatch(self, request, *args, **kwargs):
        # Exempt CSRF only if the request is for the API (non-browser clients)
        if request.headers.get('Accept') == 'application/json':
            return super().dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        # Get property instance for deletion confirmation
        property_instance = get_object_or_404(Property, pk=pk)
        if request.headers.get('Accept') == 'application/json':
            # API request
            property_data = {
                'id': property_instance.id,
                'name': property_instance.title,
                'description': property_instance.description,
            }
            return Response(property_data, status=status.HTTP_200_OK)
        else:
            # Web request - render HTML template
            context = {'property': property_instance}
            return render(request, 'Landlord/property_delete.html', context)

    def delete(self, request, pk):
        property_instance = get_object_or_404(Property, pk=pk)
        property_instance.delete()
        return Response({'message': 'Property deleted successfully!'}, status=status.HTTP_200_OK)



               
@login_required
def profile_view(request):
    user = request.user  # Get the currently logged-in user

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        updated = False  # Flag to track if any field is updated

        # Check if username or email is changed
        if username and username != user.username:
            user.username = username
            updated = True  # Set updated to True

        if email and email != user.email:
            user.email = email
            updated = True  # Set updated to True

        # Check if the password is changed (if it is not empty)
        if password:
            user.set_password(password)  # Update the password
            update_session_auth_hash(request, user)  # Keep the user logged in after password change
            updated = True  # Set updated to True

        # Save the user details only if any field has changed
        if updated:
            user.save()  # Save the updated user details
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        else:
            messages.warning(request, "You have not updated anything. Please make changes to update your profile.")

    return render(request, 'Landlord/profile.html', {'user': user})



@login_required
def tenant_dashboard(request):
    properties = Property.objects.all()

    # Filter by title
    title = request.GET.get('title', '')
    if title:
        properties = properties.filter(title__icontains=title)

    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        properties = properties.filter(price__gte=min_price)
    if max_price:
        properties = properties.filter(price__lte=max_price)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        properties = properties.filter(status=status)

    # Pagination
    paginator = Paginator(properties, 6)  # Show 6 properties per page
    page_number = request.GET.get('page')
    properties_page = paginator.get_page(page_number)

    return render(request, 'tenant/tenant_dashboard.html', {'properties': properties_page})


#contact details
@login_required(login_url='user_login') 
def contact_landlord(request, pk):
    property = get_object_or_404(Property, pk=pk)
    landlord_email = property.landlord_email  # Assuming the owner field has a reference to the landlord's User model

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            tenant_email = form.cleaned_data['tenant_email']
            landlord_email = form.cleaned_data['landlord_email']
            message = form.cleaned_data['message']

            # Send email
            send_mail(
                subject=f"Message from Tenant about {property.title}",
                message=message,
                from_email=tenant_email,
                recipient_list=[landlord_email],
                fail_silently=False,
            )

            # Display success message or redirect
            messages.success(request, 'Your message has been sent to the landlord!')
            return redirect('tenant_dashboard')
    else:
        form = ContactForm(initial={'landlord_email': landlord_email, 'tenant_email': request.user.email})

    return render(request, 'tenant/contact_landlord.html', {'form': form, 'property': property})


#JWT 
class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "This is a protected view"})