from datetime import datetime, date
from venv import logger
from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from .models import BMI, Account, Barangay, Parent, Temperature, VaccinationSchedule, BHW, BNS, Announcement, Midwife, Nurse
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required #abang lang
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import PasswordResetOTP
from django.core.serializers.json import DjangoJSONEncoder
from .models import Account, ProfilePhoto
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Preschooler, Account, Barangay, BHW, BMI, Parent, PasswordResetOTP, VaccineStock, NutritionService
from .models import ParentActivityLog, PreschoolerActivityLog
from django.db.models import Prefetch
from django.db.models import Q, F
import json
from calendar import monthrange
from django.http import HttpResponseForbidden
from django.contrib.auth.hashers import check_password
from django.views.decorators.http import require_POST
from .models import Preschooler, BMI, Temperature, Barangay, BHW, BNS
from django.utils import timezone
from django.utils.timesince import timesince
from datetime import timedelta
from django.db import IntegrityError
from django.core.paginator import Paginator
import calendar
import random
import string
from django.db.models.functions import TruncMonth
from .models import Account, Parent, Barangay, BHW, VaccineStock
from django.db.models import Count, Q
from django.views.decorators.http import require_GET
from django.utils.html import strip_tags
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from WebApp.modelserializers import AccountSerializer
from .modelserializers import *
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from django.utils.decorators import method_decorator

#added for hardware - start
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt                                   
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import ESP32DataSerializer, ESP32ResponseSerializer
import json

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow ESP32 to send data without authentication
def receive_esp32_data(request):
    """
    API endpoint to receive data from ESP32 using proper serializers
    """
    try:
        # Use serializer to validate incoming data
        serializer = ESP32DataSerializer(data=request.data)
        
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            # Store the data in session for the form to access
            request.session['esp32_data'] = {
                'weight': validated_data['weight'],
                'height': validated_data['height'],
                'temperature': validated_data['temperature'],
                'bmi': validated_data.get('bmi'),
                'bmi_category': validated_data.get('bmi_category'),
                'temperature_status': validated_data.get('temperature_status'),
                'device_id': validated_data.get('device_id', 'ESP32_BMI_Station'),
                'timestamp': str(timezone.now()),
                'esp32_timestamp': validated_data.get('timestamp')
            }
            
            # Optional: Save to database if you have a model
            # measurement = BMIMeasurement.objects.create(**validated_data)
            
            # Create response using response serializer
            response_data = {
                'status': 'success',
                'message': 'Data received and validated successfully',
                'data': validated_data,
                'server_timestamp': timezone.now()
            }
            
            response_serializer = ESP32ResponseSerializer(response_data)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        else:
            # Validation failed
            response_data = {
                'status': 'error',
                'message': 'Data validation failed',
                'errors': serializer.errors,
                'server_timestamp': timezone.now()
            }
            
            response_serializer = ESP32ResponseSerializer(response_data)
            
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        # Unexpected error
        response_data = {
            'status': 'error',
            'message': f'Server error: {str(e)}',
            'server_timestamp': timezone.now()
        }
        
        response_serializer = ESP32ResponseSerializer(response_data)
        
        return Response(response_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_esp32_data(request):
    """
    API endpoint for the webpage to get the latest ESP32 data
    """
    esp32_data = request.session.get('esp32_data', None)
    
    if esp32_data:
        response_data = {
            'status': 'success',
            'message': 'ESP32 data found',
            'data': esp32_data,
            'server_timestamp': timezone.now()
        }
        
        response_serializer = ESP32ResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    else:
        response_data = {
            'status': 'no_data',
            'message': 'No ESP32 data available in session',
            'server_timestamp': timezone.now()
        }
        
        response_serializer = ESP32ResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_404_NOT_FOUND)


# Alternative view using regular Django (without DRF)
@csrf_exempt
@require_http_methods(["POST"])
def receive_esp32_data_simple(request):
    """
    Simple version without Django REST Framework (if you prefer)
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Use serializer for validation only
        serializer = ESP32DataSerializer(data=data)
        
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            # Store in session
            request.session['esp32_data'] = {
                'weight': validated_data['weight'],
                'height': validated_data['height'],
                'temperature': validated_data['temperature'],
                'bmi': validated_data.get('bmi'),
                'bmi_category': validated_data.get('bmi_category'),
                'temperature_status': validated_data.get('temperature_status'),
                'device_id': validated_data.get('device_id', 'ESP32_BMI_Station'),
                'timestamp': str(timezone.now()),
            }
            
            return JsonResponse({
                'status': 'success',
                'message': 'Data received successfully',
                'data': validated_data
            })
            
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET"])
def get_esp32_data(request):
    """
    API endpoint for the webpage to get the latest ESP32 data
    """
    esp32_data = request.session.get('esp32_data', None)
    
    if esp32_data:
        return JsonResponse({
            'status': 'success',
            'data': esp32_data
        })
    else:
        return JsonResponse({
            'status': 'no_data',
            'message': 'No ESP32 data available'
        })
    
@csrf_exempt
@require_http_methods(["GET"])
def get_esp32_data_simple(request):
    """
    Simple version to get ESP32 data
    """
    esp32_data = request.session.get('esp32_data', None)
    
    if esp32_data:
        return JsonResponse({
            'status': 'success',
            'data': esp32_data
        })
    else:
        return JsonResponse({
            'status': 'no_data',
            'message': 'No ESP32 data available'
        })
    
# At the top of views.py, add this simple storage
ESP32_DATA_CACHE = {}

@csrf_exempt
@require_http_methods(["POST"])
def receive_esp32_data_simple(request):
    global ESP32_DATA_CACHE
    try:
        data = json.loads(request.body)
        
        # Store in global cache instead of session
        ESP32_DATA_CACHE = {
            'weight': data.get('weight'),
            'height': data.get('height'),
            'temperature': data.get('temperature'),
            'bmi': data.get('bmi'),
            'bmi_category': data.get('bmi_category'),
            'temperature_status': data.get('temperature_status'),
            'device_id': data.get('device_id', 'ESP32_BMI_Station'),
            'timestamp': str(timezone.now()),
        }
        
        print(f"DEBUG: Stored data: {ESP32_DATA_CACHE}")  # Debug output
        
        return JsonResponse({
            'status': 'success',
            'message': 'Data received successfully',
            'data': ESP32_DATA_CACHE
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_esp32_data_simple(request):
    global ESP32_DATA_CACHE
    
    print(f"DEBUG: Retrieving data: {ESP32_DATA_CACHE}")  # Debug output
    
    if ESP32_DATA_CACHE:
        return JsonResponse({
            'status': 'success',
            'data': ESP32_DATA_CACHE
        })
    else:
        return JsonResponse({
            'status': 'no_data',
            'message': 'No ESP32 data available'
        })
#added for hardware - end


def view_vaccine_stocks(request):
    """Updated medicine/vaccine stocks view with better filtering"""
    # Get user's barangay if applicable
    user_barangay = None
    if hasattr(request.user, 'account'):
        user_barangay = request.user.account.barangay
    
    # Filter stocks by barangay if user has one
    if user_barangay:
        stocks = VaccineStock.objects.filter(barangay=user_barangay)
    else:
        stocks = VaccineStock.objects.all()

    total_vaccines = stocks.count()
    total_stock = sum(stock.total_stock for stock in stocks)
    available_stock = sum(stock.available_stock for stock in stocks)
    low_stock_count = sum(1 for stock in stocks if stock.available_stock < 10)

    return render(request, 'HTML/vaccine_stocks.html', {
        'vaccine_stocks': stocks,
        'total_vaccines': total_vaccines,
        'total_stock': total_stock,
        'available_stock': available_stock,
        'low_stock_count': low_stock_count,
    })

@login_required
def add_stock(request):
    """Add medicine/vaccine stock - updated to include deworming and vitamin A"""
    if request.method == 'POST':
        name = request.POST.get('vaccine_name')
        quantity = int(request.POST.get('quantity'))

        # Define valid medicine/vaccine options
        valid_options = [
            # Vaccines
            'BCG',
            'Hepatitis B',
            'Pentavalent (DPT-Hep B HiB)',
            'Oral Polio Vaccine',
            'Inactivated Polio Vaccine',
            'Pneumococcal Conjugate Vaccine',
            'Measles Mumps and Rubella',
            # Medicines & Supplements
            'Deworming Tablets',
            'Vitamin A Capsules'
        ]

        # Validate the medicine/vaccine name
        if name not in valid_options:
            messages.error(request, f"Invalid medicine/vaccine name: {name}")
            return redirect('view_vaccine_stocks')

        try:
            # Get user's barangay if applicable
            user_barangay = None
            if hasattr(request.user, 'account'):
                user_barangay = request.user.account.barangay

            # Try to find existing stock
            if user_barangay:
                stock = VaccineStock.objects.get(vaccine_name=name, barangay=user_barangay)
            else:
                stock = VaccineStock.objects.get(vaccine_name=name)
            
            # Update existing stock
            if hasattr(stock, 'update_stock'):
                stock.update_stock(quantity)
            else:
                stock.total_stock += quantity
                stock.available_stock += quantity
                stock.save()
            
            messages.success(request, f"Stock updated for {name}. Added {quantity} units.")
            
        except VaccineStock.DoesNotExist:
            # Create new stock entry
            stock_data = {
                'vaccine_name': name,
                'total_stock': quantity,
                'available_stock': quantity
            }
            
            # Add barangay if user has one
            if user_barangay:
                stock_data['barangay'] = user_barangay
            
            VaccineStock.objects.create(**stock_data)
            messages.success(request, f"New medicine/vaccine '{name}' added with {quantity} units.")

        except ValueError:
            messages.error(request, "Invalid quantity. Please enter a valid number.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return redirect('view_vaccine_stocks')

# Helper function to get medicine categories for reporting
def get_medicine_categories():
    """Returns categorized list of medicines/vaccines"""
    return {
        'vaccines': [
            'BCG',
            'Hepatitis B', 
            'Pentavalent (DPT-Hep B HiB)',
            'Oral Polio Vaccine',
            'Inactivated Polio Vaccine',
            'Pneumococcal Conjugate Vaccine',
            'Measles Mumps and Rubella'
        ],
        'medicines_supplements': [
            'Deworming Tablets',
            'Vitamin A Capsules'
        ]
    }

@login_required
def email_endorsement(request):
    account = Account.objects.select_related('barangay').get(email=request.user.email)

    # Filter only parents from the same barangay
    parents = Parent.objects.filter(barangay=account.barangay).exclude(email__isnull=True)

    if request.method == 'POST':
        from_email = request.POST.get('from_email')
        to_email = request.POST.get('to_email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False
            )
            messages.success(request, "Endorsement email sent successfully.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Error sending email: {e}")
            return redirect('email_endorsement')

    return render(request, 'HTML/email_endorsement.html', {
        'from_email': account.email,
        'account': account,
        'parents': parents
    })

@login_required
def generate_report(request):
    user = request.user
    try:
        account = Account.objects.select_related('barangay').get(email=user.email)
    except Account.DoesNotExist:
        return HttpResponse("Account not found.", status=404)

    user_role_lower = account.user_role.lower() if account.user_role else ''
    is_authorized = (
        'bhw' in user_role_lower or 
        'health worker' in user_role_lower or
        'bns' in user_role_lower or 
        'nutritional' in user_role_lower or 
        'nutrition' in user_role_lower or
        'scholar' in user_role_lower or
        'midwife' in user_role_lower or
        'admin' in user_role_lower
    )
    if not is_authorized:
        messages.error(request, f"Your role ({account.user_role}) is not authorized to generate reports.")
        return redirect('dashboard')

    barangay = account.barangay
    preschoolers = Preschooler.objects.filter(
        barangay=barangay,
        is_archived=False
    ).select_related('parent_id').prefetch_related('bmi_set')

    # ✅ Month filter
    month_str = request.GET.get("month")  # format: YYYY-MM
    month_filter = None
    if month_str:
        try:
            month_filter = datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            month_filter = None

    status_totals = { 'Severely Underweight': 0, 'Underweight': 0, 'Normal': 0, 'Overweight': 0, 'Obese': 0 }
    preschoolers_data = []
    today = date.today()

    for p in preschoolers:
        bmi_qs = p.bmi_set.all().order_by('-date_recorded')
        if month_filter:
            bmi_qs = bmi_qs.filter(
                date_recorded__year=month_filter.year,
                date_recorded__month=month_filter.month
            )
        latest_bmi = bmi_qs.first()

        # Default values
        height, weight, bmi_value = "N/A", "N/A", "N/A"
        nutritional_status = "No BMI Record"

        if latest_bmi:
            height = f"{latest_bmi.height:.1f}" if latest_bmi.height else "N/A"
            weight = f"{latest_bmi.weight:.1f}" if latest_bmi.weight else "N/A"
            bmi_value = f"{latest_bmi.bmi_value:.1f}" if latest_bmi.bmi_value else "N/A"

            if latest_bmi.bmi_value:
                bmi = latest_bmi.bmi_value
                if bmi < 13:
                    nutritional_status = "Severely Underweight"
                elif 13 <= bmi < 14.9:
                    nutritional_status = "Underweight"
                elif 14.9 <= bmi <= 17.5:
                    nutritional_status = "Normal"
                elif 17.6 <= bmi <= 18.9:
                    nutritional_status = "Overweight"
                else:
                    nutritional_status = "Obese"

        if nutritional_status in status_totals:
            status_totals[nutritional_status] += 1

        age = today.year - p.birth_date.year - ((today.month, today.day) < (p.birth_date.month, p.birth_date.day))
        parent_name = p.parent_id.full_name if p.parent_id else "N/A"
        address = getattr(p.parent_id, 'address', 'N/A') if p.parent_id else "N/A"

        preschoolers_data.append({
            'name': f"{p.first_name} {p.last_name}",
            'age': f"{age} years",
            'height': height,
            'weight': weight,
            'bmi': bmi_value,
            'nutritional_status': nutritional_status,
            'parent_name': parent_name,
            'address': address,
            'sex': p.sex,
        })

    html_string = render_to_string('HTML/barangay_report.html', {
        'account': account,
        'barangay': barangay,
        'preschoolers': preschoolers_data,
        'summary': status_totals,
        'month_filter': month_str or "All",
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Barangay-Health-Report.pdf"'
    return response

def generate_immunization_report(request):
    """Generate PDF report for immunization schedules and vaccination records with strict month filter"""
    user = request.user
    try:
        account = Account.objects.select_related('barangay').get(email=user.email)
    except Account.DoesNotExist:
        return HttpResponse("Account not found.", status=404)

    user_role_lower = account.user_role.lower() if account.user_role else ''
    is_authorized = any(role in user_role_lower for role in [
        'bhw', 'health worker', 'bns', 'nutrition', 'nutritional', 'scholar', 'midwife', 'admin'
    ])
    if not is_authorized:
        messages.error(request, f"Your role ({account.user_role}) is not authorized to generate immunization reports.")
        return redirect('dashboard')

    barangay = account.barangay
    if not barangay:
        return HttpResponse("No barangay assigned to this account.", status=404)

    # Month filter
    month_str = request.GET.get("month")  # expected format: YYYY-MM
    month_filter = None
    month_display = "All Records"
    if month_str:
        try:
            month_filter = datetime.strptime(month_str, "%Y-%m")
            month_display = month_filter.strftime("%B %Y")
        except ValueError:
            month_filter = None
            month_display = "All Records"

    preschoolers = Preschooler.objects.filter(is_archived=False).select_related('parent_id').prefetch_related('vaccination_schedules')
    today = date.today()

    vaccination_summary = {
        'Fully Vaccinated': 0,
        'Partially Vaccinated': 0,
        'Not Vaccinated': 0,
        'Overdue': 0,
    }

    preschoolers_data = []

    # Unique vaccines
    scheduled_vaccines = VaccinationSchedule.objects.all().values_list('vaccine_name', flat=True).distinct().order_by('vaccine_name')
    required_vaccines = list(scheduled_vaccines) if scheduled_vaccines else [
        'BCG', 'Hepatitis B', 'DPT', 'OPV', 'MMR', 'Pneumococcal', 'Rotavirus'
    ]

    # Vaccine stock info
    vaccine_stocks = VaccineStock.objects.all()
    stock_info = {v.vaccine_name: {'total_stock': v.total_stock, 'available_stock': v.available_stock, 'used_stock': v.total_stock - v.available_stock} for v in vaccine_stocks}

    for p in preschoolers:
        # Filter only completed schedules in month
        schedules = [s for s in p.vaccination_schedules.all() if s.status == 'completed']
        if month_filter:
            schedules = [s for s in schedules if s.scheduled_date and s.scheduled_date.year == month_filter.year and s.scheduled_date.month == month_filter.month]

        if not schedules:
            continue  # skip preschooler if no completed schedule in the selected month

        age_years = today.year - p.birth_date.year - ((today.month, today.day) < (p.birth_date.month, p.birth_date.day))
        age_months = (today.year - p.birth_date.year) * 12 + today.month - p.birth_date.month

        total_scheduled = len(schedules)
        total_completed = total_scheduled  # because we only included completed schedules

        vaccination_status = "Fully Vaccinated" if total_completed == total_scheduled else "Partially Vaccinated"

        overdue_count = 0  # completed schedules cannot be overdue

        vaccination_summary[vaccination_status] += 1

        parent_name = p.parent_id.full_name if p.parent_id else "N/A"
        address = getattr(p.parent_id, 'address', 'N/A') if p.parent_id else getattr(p, 'address', 'N/A') or "N/A"

        last_completed = max([s.completion_date or s.administered_date for s in schedules if s.completion_date or s.administered_date], default=None)
        last_vaccination_date = last_completed.strftime('%m/%d/%Y') if last_completed else "N/A"

        completed_text = "; ".join([f"{s.vaccine_name} ({(s.completion_date or s.administered_date or s.scheduled_date).strftime('%m/%d/%Y')})" for s in schedules])

        preschoolers_data.append({
            'name': f"{p.first_name} {p.last_name}",
            'age': f"{age_years} years, {age_months % 12} months",
            'sex': p.sex,
            'vaccination_status': vaccination_status,
            'vaccines_received': f"{total_completed}/{total_scheduled}",
            'last_vaccination': last_vaccination_date,
            'vaccination_schedule': completed_text,
            'parent_name': parent_name,
            'address': address,
            'overdue_count': overdue_count,
            'all_schedules': [{
                'vaccine_name': s.vaccine_name,
                'doses': s.doses or 1,
                'required_doses': s.required_doses or 1,
                'scheduled_date': s.scheduled_date,
                'completion_date': s.completion_date,
                'administered_date': s.administered_date,
                'status': s.status,
                'reschedule_reason': s.reschedule_reason or ""
            } for s in schedules],
        })

    # Vaccine stock list
    vaccine_stock_data = []
    for v in required_vaccines:
        stock = stock_info.get(v, {'total_stock': 0, 'available_stock': 0, 'used_stock': 0})
        vaccine_stock_data.append({'vaccine_name': v, **stock})

    context = {
        'account': account,
        'barangay': barangay,
        'preschoolers': preschoolers_data,
        'summary': vaccination_summary,
        'required_vaccines': required_vaccines,
        'vaccine_stocks': vaccine_stock_data,
        'month_filter': month_str or "All",
    }

    html_string = render_to_string('HTML/immunization_report.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Immunization-Report.pdf"'
    return response


def index(request):
    
    return HttpResponse('Welcome to the PPMA Web Application!')

def addbarangay(request):
    if request.method == 'POST':
        name = request.POST.get('barangay-name', '').strip()
        location = request.POST.get('location', '').strip()
        email = request.POST.get('email', '').strip()
        health_center = request.POST.get('health-center', '').strip()
        remarks = request.POST.get('remarks', '').strip()

        print(f"[DEBUG] Received: {name=}, {location=}, {email=}, {health_center=}, {remarks=}")

        # ✅ Check for empty barangay name
        if not name:
            messages.error(request, "Barangay name is required.")
            return render(request, 'HTML/addbarangay.html')

        # ✅ Check if barangay name already exists
        if Barangay.objects.filter(name__iexact=name).exists():
            messages.error(request, f"A barangay named '{name}' already exists.")
            return render(request, 'HTML/addbarangay.html')

        # ✅ Check if location already exists (if provided)
        if location and Barangay.objects.filter(location__iexact=location).exists():
            messages.error(request, f"A barangay with location '{location}' already exists.")
            return render(request, 'HTML/addbarangay.html')

        # ✅ Check if email already exists (if provided)
        if email and Barangay.objects.filter(email__iexact=email).exists():
            messages.error(request, f"A barangay with email '{email}' already exists.")
            return render(request, 'HTML/addbarangay.html')

        # ✅ Try saving the barangay
        try:
            Barangay.objects.create(
                name=name,
                location=location or None,
                email=email or None,
                health_center=health_center or None,
                remarks=remarks or None
                # date_created will be automatically set by Django if you have auto_now_add=True in your model
            )
            messages.success(request, f"Barangay '{name}' was added successfully!")
            return redirect('addbarangay')
        except Exception as e:
            print(f"[ERROR] Failed to add barangay: {e}")
            messages.error(request, "Something went wrong while saving. Please try again.")
    
    return render(request, 'HTML/addbarangay.html')


def Admin(request):
    health_worker_count = Account.objects.filter(user_role__iexact='healthworker').count() or 0
    preschoolers = Preschooler.objects.all()
    accounts = Account.objects.filter(is_validated=False)

    # Notification system
    notifications = []

    for acc in accounts:
        notifications.append({
            'type': 'account',
            'full_name': acc.full_name,
            'created_at': acc.created_at,
            'user_role': acc.user_role,
        })

    for child in preschoolers:
        notifications.append({
            'type': 'preschooler',
            'full_name': f"{child.first_name} {child.last_name}",
            'date_registered': child.date_registered,
            'bhw_image': getattr(child.bhw_id.account.profile_photo.image, 'url', None)
                          if child.bhw_id and child.bhw_id.account and hasattr(child.bhw_id.account, 'profile_photo') else None,
        })

    # Process timestamps for all notifications
    for notif in notifications:
        # Get the timestamp (either created_at or date_registered)
        timestamp = notif.get('created_at') or notif.get('date_registered')
        
        if timestamp:
            # Handle date vs datetime conversion
            if isinstance(timestamp, date) and not isinstance(timestamp, datetime):
                # Convert date to datetime at current time instead of midnight
                # This fixes the timezone offset issue for newly registered preschoolers
                current_time = timezone.now().time()
                timestamp = timezone.make_aware(datetime.combine(timestamp, current_time))
            elif isinstance(timestamp, datetime) and timezone.is_naive(timestamp):
                # Make datetime timezone-aware if it's naive
                timestamp = timezone.make_aware(timestamp)
        else:
            # Fallback if no timestamp found
            timestamp = timezone.now()  # Use current time instead of datetime.min
        
        notif['timestamp'] = timestamp

    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    latest_notifications = notifications[:15]

    latest_timestamp = latest_notifications[0]['timestamp'] if latest_notifications else None

    total_preschoolers = Parent.objects.values_list('registered_preschoolers', flat=True)\
        .distinct().exclude(registered_preschoolers=None).count() or 0

    # Calculate total vaccinated preschoolers
    # Option 1: If you have a vaccination model/field
    # total_vaccinated = Preschooler.objects.filter(is_vaccinated=True, is_archived=False).count()
    
    # Option 2: If you have a separate Vaccination model
    # total_vaccinated = Vaccination.objects.values('preschooler').distinct().count()
    
    # Option 3: If vaccination data is in a related model (like ImmunizationRecord)
    # Assuming you have an ImmunizationRecord or similar model
    try:
        # Replace 'ImmunizationRecord' with your actual vaccination/immunization model name
        # and adjust the field names according to your model structure
        total_vaccinated = Preschooler.objects.filter(
            immunizationrecord__isnull=False,  # Has at least one immunization record
            is_archived=False
        ).distinct().count() or 0
    except:
        # Default to 0 if vaccination tracking isn't implemented yet
        total_vaccinated = 0

    barangays = Barangay.objects.all()

    # Pie chart data: summarize nutritional status
    status_totals = {
        'Severely Underweight': 0,
        'Underweight': 0,
        'Normal': 0,
        'Overweight': 0,
        'Obese': 0,
    }

    # Table summary
    summary = []
    for brgy in barangays:
        preschoolers_in_barangay = Preschooler.objects.filter(
            barangay=brgy,
            is_archived=False
        ).prefetch_related(
            Prefetch('bmi_set', queryset=BMI.objects.order_by('-date_recorded'), to_attr='bmi_records')
        )

        nutritional_counts = {
            'severely_underweight': 0,
            'underweight': 0,
            'normal': 0,
            'overweight': 0,
            'obese': 0,
        }

        for p in preschoolers_in_barangay:
            latest_bmi = p.bmi_records[0] if hasattr(p, 'bmi_records') and p.bmi_records else None
            if latest_bmi:
                bmi_value = latest_bmi.bmi_value
                if bmi_value < 13:
                    nutritional_counts['severely_underweight'] += 1
                    status_totals['Severely Underweight'] += 1
                elif 13 <= bmi_value < 14.9:
                    nutritional_counts['underweight'] += 1
                    status_totals['Underweight'] += 1
                elif 14.9 <= bmi_value <= 17.5:
                    nutritional_counts['normal'] += 1
                    status_totals['Normal'] += 1
                elif 17.6 <= bmi_value <= 18.9:
                    nutritional_counts['overweight'] += 1
                    status_totals['Overweight'] += 1
                elif bmi_value >= 19:
                    nutritional_counts['obese'] += 1
                    status_totals['Obese'] += 1

        summary.append({
            'barangay': brgy.name,
            'preschooler_count': preschoolers_in_barangay.count(),
            **nutritional_counts
        })

    # Line Chart Data (Registrations per month)
    monthly_data = (
        Preschooler.objects
        .filter(is_archived=False)
        .annotate(month=TruncMonth('date_registered'))
        .values('month')
        .annotate(count=Count('preschooler_id'))
        .order_by('month')
    )
    line_chart_labels = [calendar.month_name[data['month'].month] for data in monthly_data]
    line_chart_values = [data['count'] for data in monthly_data]

    return render(request, 'HTML/Admindashboard.html', {
        'health_worker_count': health_worker_count,
        'notifications': latest_notifications,
        'latest_notif_timestamp': latest_timestamp.isoformat() if latest_timestamp else '',
        'total_preschoolers': total_preschoolers,
        'total_vaccinated': total_vaccinated,  # Add this new dynamic value
        'barangay_summary': summary,
        'nutritional_data': {
            'labels': list(status_totals.keys()),
            'values': list(status_totals.values())
        },
        'line_chart_data': {
            'labels': line_chart_labels,
            'values': line_chart_values
        }
    })

def archived(request):
    archived_preschoolers_qs = Preschooler.objects.filter(is_archived=True).select_related('barangay')

    # Paginate archived preschoolers
    paginator = Paginator(archived_preschoolers_qs, 10)  # 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Convert to JSON
    archived_json = json.dumps([
        {
            "id": p.preschooler_id,
            "name": f"{p.first_name} {p.last_name}",
            "age": p.age,
            "barangay": p.barangay.name if p.barangay else "N/A",
            "gender": p.sex,
            "birthdate": str(p.birth_date),
            "weight": "",
            "height": "",
            "bmi": "",
            "immunization_status": "",
            "nutrition_history": [],
            "notes": ""
        } for p in page_obj
    ])

    return render(request, 'HTML/archived.html', {
        'archived_preschoolers_json': archived_json,
        'archived_page': page_obj,  # paginated
    })

def archived_details(request):
    return render(request, 'HTML/archived_details.html')

def dashboard(request):
    # ✅ Redirect to login if not authenticated
    if not request.user.is_authenticated:
        return redirect('login')

    # ✅ Get the current user's account (remove barangay relation)
    account = get_object_or_404(
        Account.objects.select_related('profile_photo'),
        email=request.user.email
    )

    # ✅ Active preschoolers (show all, remove barangay filter)
    preschoolers = Preschooler.objects.filter(
        is_archived=False
    ).prefetch_related('bmi_set')

    preschooler_count = preschoolers.count()

    # ✅ Archived preschoolers (show all)
    archived_preschooler_count = Preschooler.objects.filter(
        is_archived=True
    ).count()

    # ✅ Parents (show all, remove barangay filter)
    parent_accounts = Parent.objects.all().distinct().order_by('-created_at')

    parent_count = parent_accounts.count()

    print(f"DEBUG Dashboard: Total Parent count: {parent_count}")

    # ✅ Nutritional Summary via latest BMI
    nutritional_summary = {
        'normal': 0,
        'underweight': 0,
        'overweight': 0,
        'severely_underweight': 0,
        'obese': 0,
    }

    for p in preschoolers:
        latest_bmi = p.bmi_set.order_by('-date_recorded').first()
        if latest_bmi:
            bmi_value = latest_bmi.bmi_value
            if bmi_value < 13:
                nutritional_summary['severely_underweight'] += 1
            elif 13 <= bmi_value < 14.9:
                nutritional_summary['underweight'] += 1
            elif 14.9 <= bmi_value <= 17.5:
                nutritional_summary['normal'] += 1
            elif 17.6 <= bmi_value <= 18.9:
                nutritional_summary['overweight'] += 1
            elif bmi_value >= 19:
                nutritional_summary['obese'] += 1

    # ✅ Prepare pie chart data for nutritional status
    pie_chart_data = {
        'labels': ['Severely Underweight', 'Underweight', 'Normal', 'Overweight', 'Obese'],
        'values': [
            nutritional_summary['severely_underweight'],
            nutritional_summary['underweight'],
            nutritional_summary['normal'],
            nutritional_summary['overweight'],
            nutritional_summary['obese']
        ],
        'colors': ['#e74c3c', '#f39c12', '#27ae60', '#e67e22', '#c0392b']
    }

    # ✅ Recent parent account notifications
    notifications = []
    seen_ids = set()

    for parent in parent_accounts:
        if parent.parent_id not in seen_ids:
            notifications.append({
                'type': 'account',
                'id': parent.parent_id,
                'full_name': parent.full_name,
                'user_role': 'Parent',
                'timestamp': parent.created_at,
            })
            seen_ids.add(parent.parent_id)

    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    latest_notif_timestamp = notifications[0]['timestamp'] if notifications else None

    # ✅ NEW: Fetch active announcements for the dashboard
    try:
        announcements = Announcement.objects.filter(
            is_active=True
        ).order_by('-created_at')[:10]
    except Exception as e:
        announcements = []

    return render(request, 'HTML/dashboard.html', {
        'account': account,
        'full_name': account.full_name,
        'preschooler_count': preschooler_count,
        'archived_preschooler_count': archived_preschooler_count,
        'parent_count': parent_count,
        'nutritional_summary': nutritional_summary,
        'pie_chart_data': pie_chart_data,
        'notifications': notifications[:15],
        'latest_notif_timestamp': latest_notif_timestamp.isoformat() if latest_notif_timestamp else '',
        'announcements': announcements,
    })

@csrf_exempt
def upload_cropped_photo(request):
    if request.method == 'POST' and request.user.is_authenticated:
        image = request.FILES.get('cropped_image')
        account = Account.objects.get(email=request.user.email)

        if hasattr(account, 'profile_photo'):
            account.profile_photo.image = image
            account.profile_photo.save()
        else:
            ProfilePhoto.objects.create(account=account, image=image)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'unauthorized'}, status=403)

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # 🔐 Admin hardcoded login
        if email.lower() == 'admin@gmail.com' and password == 'admin123':
            request.session['user_role'] = 'admin'
            request.session['full_name'] = 'Admin'
            return redirect('Admindashboard')

        # ✅ Authenticate using email as username
        user = authenticate(request, username=email, password=password)

        if user is not None:
            try:
                account = Account.objects.get(email=email)

                if account.is_rejected:
                    messages.error(request, "Your account has been rejected by the admin.")
                    return render(request, 'HTML/login.html')

                # ✅ BHW, BNS, MIDWIFE, and NURSE login (requires validation)
                if (account.user_role.lower() == 'healthworker' or 
                    account.user_role.lower() == 'bhw' or
                    account.user_role.lower() in ['bns', 'barangay nutritional scholar'] or
                    account.user_role.lower() == 'midwife' or
                    account.user_role.lower() == 'nurse'):  # Added nurse here
                    
                    if not account.is_validated:
                        messages.error(request, "Your account is still pending admin validation.")
                        return render(request, 'HTML/login.html')

                    auth_login(request, user)
                    account.last_activity = timezone.now()
                    account.save(update_fields=['last_activity'])

                    request.session['email'] = account.email
                    request.session['user_role'] = account.user_role.lower()
                    request.session['full_name'] = account.full_name
                    request.session['contact_number'] = account.contact_number

                    # Redirect based on role
                    if account.user_role.lower() == 'midwife':
                        return redirect('dashboard')  # Adjust as needed
                    elif account.user_role.lower() == 'nurse':
                        return redirect('dashboard')  # Adjust as needed, e.g., nurse dashboard
                    else:
                        return redirect('dashboard')

                # ✅ Parent login (NO validation required)
                elif account.user_role.lower() == 'parent':
                    try:
                        parent = Parent.objects.get(email=email)
                    except Parent.DoesNotExist:
                        messages.error(request, "Parent account not found.")
                        return render(request, 'HTML/login.html')

                    if parent.must_change_password:
                        request.session['email'] = email
                        return redirect('change_password_first')

                    auth_login(request, user)
                    account.last_activity = timezone.now()
                    account.save(update_fields=['last_activity'])

                    request.session['email'] = account.email
                    request.session['user_role'] = 'parent'
                    request.session['full_name'] = account.full_name
                    request.session['contact_number'] = account.contact_number

                    return redirect('parent_dashboard')

                # ❌ Unknown role
                else:
                    messages.warning(request, f"Unknown user role: {account.user_role}. Please contact support.")
                    return redirect('login')

            except Account.DoesNotExist:
                messages.error(request, "Account record not found. Please contact support.")
                return render(request, 'HTML/login.html')

        else:
            messages.error(request, "Invalid email or password.")

    # ✅ Fetch active announcements for the login page
    try:
        announcements = Announcement.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]  # Show latest 5 announcements
    except Exception as e:
        announcements = []

    return render(request, 'HTML/login.html', {
        'announcements': announcements,
    })

def logout_view(request):
    if request.user.is_authenticated:
        try:
            account = Account.objects.get(email=request.user.email)
            account.last_activity = timezone.now()
            account.save(update_fields=['last_activity'])
        except Account.DoesNotExist:
            pass

    logout(request)
    return redirect('login')


def parent_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    account = get_object_or_404(Account.objects.select_related('profile_photo'), email=request.user.email)
    preschoolers_raw = Preschooler.objects.filter(parent_id__email=account.email)

    # Compute age per preschooler
    preschoolers = []
    today = date.today()

    for p in preschoolers_raw:
        birth_date = p.birth_date
        
        # Calculate years
        age_years = today.year - birth_date.year
        
        # Calculate months
        age_months = today.month - birth_date.month
        
        # Calculate days
        age_days = today.day - birth_date.day
        
        # Adjust if days are negative
        if age_days < 0:
            age_months -= 1
            # Get the last day of the previous month
            if today.month == 1:
                last_month = 12
                last_year = today.year - 1
            else:
                last_month = today.month - 1
                last_year = today.year
            
            from calendar import monthrange
            days_in_last_month = monthrange(last_year, last_month)[1]
            age_days += days_in_last_month
        
        # Adjust if months are negative
        if age_months < 0:
            age_years -= 1
            age_months += 12

        preschoolers.append({
            'data': p,
            'age_years': age_years,
            'age_months': age_months,
            'age_days': age_days
        })

    # Show welcome message only once per session
    if not request.session.get('first_login_shown', False):
        messages.success(request, f"👋 Welcome, {account.full_name}!")
        request.session['first_login_shown'] = True

    # Filter upcoming schedules
    upcoming_schedules = VaccinationSchedule.objects.filter(
        preschooler__in=preschoolers_raw
    ).order_by('scheduled_date')

    # ✅ NEW: Fetch active announcements for parents
    try:
        announcements = Announcement.objects.filter(
            is_active=True
        ).order_by('-created_at')[:10]  # Show latest 10 active announcements
    except Exception as e:
        announcements = []

    return render(request, 'HTML/parent_dashboard.html', {
        'account': account,
        'full_name': account.full_name,
        'preschoolers': preschoolers,
        'upcoming_schedules': upcoming_schedules,
        'announcements': announcements,  # ✅ NEW: Pass announcements to template
        'today': today,
    })

@login_required
def add_schedule(request, preschooler_id):
    print("[DEBUG] 🔁 Entered add_schedule view")

    preschooler = get_object_or_404(Preschooler, pk=preschooler_id)
    parent = preschooler.parent_id

    if request.method != "POST":
        print("[DEBUG] ❌ Request method is not POST")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Extract POST values
    vaccine_name = request.POST.get("vaccine_name")
    doses = request.POST.get("vaccine_doses")
    required_doses = request.POST.get("required_doses")
    immunization_date = request.POST.get("immunization_date")
    next_schedule = request.POST.get("next_vaccine_schedule")

    print(f"[DEBUG] vaccine_name: {vaccine_name}")
    print(f"[DEBUG] doses: {doses}")
    print(f"[DEBUG] required_doses: {required_doses}")
    print(f"[DEBUG] immunization_date: {immunization_date}")
    print(f"[DEBUG] next_vaccine_schedule: {next_schedule}")

    try:
        schedule = VaccinationSchedule.objects.create(
            preschooler=preschooler,
            vaccine_name=vaccine_name,
            doses=int(doses),
            required_doses=int(required_doses),
            scheduled_date=immunization_date,
            next_vaccine_schedule=next_schedule or None,
            confirmed_by_parent=False
        )
        print("[DEBUG] ✅ VaccinationSchedule saved:", schedule)
        messages.success(request, "✅ Vaccination schedule saved successfully.")

        # Send email
        if parent and parent.email:
            subject = f"[PPMS] Vaccination Schedule for {preschooler.first_name}"
            message = (
                f"Dear {parent.full_name},\n\n"
                f"A new vaccination schedule has been created for your child, {preschooler.first_name} {preschooler.last_name}.\n\n"
                f"📌 Vaccine: {vaccine_name}\n"
                f"💉 Doses: {doses} of {required_doses}\n"
                f"📅 Schedule: {immunization_date}\n"
                f"{f'📆 Next Dose: {next_schedule}\n' if next_schedule else ''}"
                "\nPlease confirm the vaccination on your dashboard once completed.\n\n"
                "Thank you,\nPPMS System"
            )
            send_mail(subject, message, "your_gmail_account@gmail.com", [parent.email], fail_silently=True)
            print("[DEBUG] 📧 Email sent to parent")

    except Exception as e:
        print(f"[ERROR] ❌ Failed to save schedule: {e}")
        messages.error(request, "An error occurred while saving the vaccination schedule.")

    return redirect(request.META.get("HTTP_REFERER", "/"))

@require_POST #may binago ako dito
def confirm_schedule(request, schedule_id):
    if not request.user.is_authenticated:
        return redirect('login')

    schedule = get_object_or_404(VaccinationSchedule, id=schedule_id)

    if schedule.preschooler.parent_id.email != request.user.email:
        messages.error(request, "Unauthorized confirmation attempt.")
        return redirect('parent_dashboard')

    # ✅ Mark current schedule as confirmed
    schedule.confirmed_by_parent = True
    schedule.save()

    # 🚫 Prevent over-scheduling
    if (
        schedule.next_vaccine_schedule and 
        schedule.doses < schedule.required_doses
    ):
        # Double check that no future duplicate already exists
        existing = VaccinationSchedule.objects.filter(
            preschooler=schedule.preschooler,
            vaccine_name=schedule.vaccine_name,
            doses=schedule.doses + 1
        ).exists()

        if not existing:
            next_schedule = VaccinationSchedule.objects.create(
                preschooler=schedule.preschooler,
                vaccine_name=schedule.vaccine_name,
                doses=schedule.doses + 1,
                required_doses=schedule.required_doses,
                scheduled_date=schedule.next_vaccine_schedule,
                scheduled_by=schedule.scheduled_by,
                confirmed_by_parent=False
            )
            print("[DEBUG] ➕ Created next dose schedule:", next_schedule)
            messages.success(request, f"Dose {schedule.doses} confirmed. ✅ Next dose scheduled.")
        else:
            print("[DEBUG] ⛔ Skipped creating duplicate schedule")
    else:
        print("[DEBUG] ✅ Final dose confirmed. No more schedules.")
        messages.success(request, "Vaccination confirmed. ✅")

    return redirect('parent_dashboard')

def confirm_vaccine_schedule(request, schedule_id):
    if request.method == 'POST':
        schedule = get_object_or_404(VaccinationSchedule, id=schedule_id)
        schedule.confirmed_by_parent = True
        schedule.save()
        return JsonResponse({'status': 'success', 'message': 'Schedule confirmed!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def parents_mypreschooler(request, preschooler_id):
    preschooler = get_object_or_404(
        Preschooler.objects.prefetch_related(
            Prefetch('bmi_set', queryset=BMI.objects.order_by('-date_recorded'), to_attr='bmi_records')
        ),
        pk=preschooler_id
    )

    # Calculate age with years, months, and days
    today = date.today()
    birth_date = preschooler.birth_date
    
    # Calculate years
    age_years = today.year - birth_date.year
    
    # Calculate months
    age_months = today.month - birth_date.month
    
    # Calculate days
    age_days = today.day - birth_date.day
    
    # Adjust if days are negative
    if age_days < 0:
        age_months -= 1
        # Get the last day of the previous month
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year
        
        from calendar import monthrange
        days_in_last_month = monthrange(last_year, last_month)[1]
        age_days += days_in_last_month
    
    # Adjust if months are negative
    if age_months < 0:
        age_years -= 1
        age_months += 12

    # Calculate total age in months for WHO standards
    total_age_months = age_years * 12 + age_months

    # Get WHO standards for weight and height
    standard_weight = get_weight_for_age_standard(total_age_months, preschooler.sex)
    standard_height = get_height_for_age_standard(total_age_months, preschooler.sex)

    # Extract the latest BMI from bmi_records
    latest_bmi = preschooler.bmi_records[0] if preschooler.bmi_records else None

    # Calculate growth status
    weight_for_age_status = "N/A"
    height_for_age_status = "N/A"
    weight_height_for_age_status = "N/A"
    
    if latest_bmi and standard_weight:
        # Weight-for-age comparison
        weight_ratio = latest_bmi.weight / standard_weight
        if weight_ratio < 0.8:
            weight_for_age_status = "Underweight"
        elif 0.8 <= weight_ratio <= 1.2:
            weight_for_age_status = "Normal"
        else:
            weight_for_age_status = "Overweight"
    
    if latest_bmi and standard_height:
        # Height-for-age comparison
        height_ratio = latest_bmi.height / standard_height
        if height_ratio < 0.95:
            height_for_age_status = "Stunted"
        elif height_ratio >= 0.95:
            height_for_age_status = "Normal"

    # Weight-Height-for-Age (simplified BMI interpretation)
    if latest_bmi:
        bmi_value = latest_bmi.bmi_value
        if bmi_value < 13:
            weight_height_for_age_status = "Severely Underweight"
        elif 13 <= bmi_value < 14.9:
            weight_height_for_age_status = "Underweight"
        elif 14.9 <= bmi_value <= 17.5:
            weight_height_for_age_status = "Normal"
        elif 17.6 <= bmi_value <= 18.9:
            weight_height_for_age_status = "Overweight"
        elif bmi_value >= 19:
            weight_height_for_age_status = "Obese"

    # Get immunization history
    immunization_history = preschooler.vaccination_schedules.filter(confirmed_by_parent=True)

    return render(request, 'HTML/parents_mypreschooler.html', {
        'preschooler': preschooler,
        'age_years': age_years,
        'age_months': age_months,
        'age_days': age_days,  # Now includes days
        'latest_bmi': latest_bmi,
        'standard_weight': standard_weight,
        'standard_height': standard_height,
        'weight_for_age_status': weight_for_age_status,
        'height_for_age_status': height_for_age_status,
        'weight_height_for_age_status': weight_height_for_age_status,
        'immunization_history': immunization_history,
    })

def add_vaccine(request, preschooler_id):
    """
    View to add a completed vaccine directly to immunization history
    """
    if request.method == 'POST':
        preschooler = get_object_or_404(Preschooler, preschooler_id=preschooler_id)
        
        # Get form data
        vaccine_name = request.POST.get('vaccine_name')
        required_doses = request.POST.get('required_doses')
        immunization_date = request.POST.get('immunization_date')
        completion_date_str = request.POST.get('completion_date')
        
        try:
            # Parse the completion datetime
            completion_date = datetime.strptime(completion_date_str, '%Y-%m-%dT%H:%M')
            completion_date = timezone.make_aware(completion_date, timezone.get_current_timezone())
            
            # Parse the immunization date (use this as the scheduled date)
            immunization_date = datetime.strptime(immunization_date, '%Y-%m-%d').date()
            
            # Convert required_doses to integer for calculations
            required_doses_int = int(required_doses)
            
            # Check if vaccine is available in stock
            vaccine_stock = VaccineStock.objects.filter(vaccine_name=vaccine_name).first()
            if not vaccine_stock or vaccine_stock.available_stock < required_doses_int:
                messages.error(request, f'Insufficient {vaccine_name} stock. Available: {vaccine_stock.available_stock if vaccine_stock else 0}, Required: {required_doses_int}')
                return redirect('preschooler_detail', preschooler_id=preschooler_id)
            
            # Create the vaccination schedule record with completed status
            vaccination_schedule = VaccinationSchedule.objects.create(
                preschooler=preschooler,
                vaccine_name=vaccine_name,
                required_doses=required_doses_int,
                scheduled_date=immunization_date,  # Use immunization date as scheduled date
                status='completed',
                completion_date=completion_date,
                reschedule_reason=None
            )
            
            # Deduct from vaccine stock based on required doses
            vaccine_stock.available_stock -= required_doses_int
            vaccine_stock.save()
            
            messages.success(request, f'Vaccine {vaccine_name} added to immunization history successfully!')
            
        except ValueError as e:
            messages.error(request, 'Invalid date format provided.')
        except Exception as e:
            messages.error(request, f'Error adding vaccine: {str(e)}')
    
    return redirect('preschooler_detail', preschooler_id=preschooler_id)

def preschooler_detail(request, preschooler_id):
    preschooler = get_object_or_404(Preschooler, preschooler_id=preschooler_id)
    bmi = preschooler.bmi_set.order_by('-date_recorded').first()

    # Calculate age with years, months, and days
    today = date.today()
    birth_date = preschooler.birth_date
    
    # Calculate years
    age_years = today.year - birth_date.year
    
    # Calculate months
    age_months = today.month - birth_date.month
    
    # Calculate days
    age_days = today.day - birth_date.day
    
    # Adjust if days are negative
    if age_days < 0:
        age_months -= 1
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year
        
        from calendar import monthrange
        days_in_last_month = monthrange(last_year, last_month)[1]
        age_days += days_in_last_month
    
    # Adjust if months are negative
    if age_months < 0:
        age_years -= 1
        age_months += 12

    # Calculate total age in months
    total_age_months = age_years * 12 + age_months

    # Get WHO standards for weight and height
    standard_weight = get_weight_for_age_standard(total_age_months, preschooler.sex)
    standard_height = get_height_for_age_standard(total_age_months, preschooler.sex)

    # Calculate weight-for-age and height-for-age status
    weight_for_age_status = "N/A"
    height_for_age_status = "N/A"
    
    if bmi and standard_weight:
        weight_ratio = bmi.weight / standard_weight
        if weight_ratio < 0.8:
            weight_for_age_status = "Underweight"
        elif 0.8 <= weight_ratio <= 1.2:
            weight_for_age_status = "Normal"
        else:
            weight_for_age_status = "Overweight"
    
    if bmi and standard_height:
        height_ratio = bmi.height / standard_height
        if height_ratio < 0.95:
            height_for_age_status = "Stunted"
        elif height_ratio >= 0.95:
            height_for_age_status = "Normal"

    # Determine nutritional status based on latest BMI
    if bmi:
        bmi_value = bmi.bmi_value
        if bmi_value < 13:
            nutritional_status = "Severely Underweight"
        elif 13 <= bmi_value < 14.9:
            nutritional_status = "Underweight"
        elif 14.9 <= bmi_value <= 17.5:
            nutritional_status = "Normal"
        elif 17.6 <= bmi_value <= 18.9:
            nutritional_status = "Overweight"
        elif bmi_value >= 19:
            nutritional_status = "Obese"
        else:
            nutritional_status = "N/A"
    else:
        nutritional_status = "N/A"

    # Updated immunization data queries with status filtering
    pending_schedules = preschooler.vaccination_schedules.exclude(status='completed').order_by('scheduled_date')
    immunization_history = preschooler.vaccination_schedules.filter(status='completed').order_by('-completion_date')
    
    # Get nutrition services for this preschooler - FIXED ORDER BY
    nutrition_services = preschooler.nutrition_services.all().order_by('-completion_date')
    
    # Get available vaccine stocks (for vaccines)
    available_vaccines = VaccineStock.objects.filter(
        available_stock__gt=0,
        vaccine_name__in=[
            'BCG', 'Hepatitis B', 'Pentavalent (DPT-Hep B HiB)',
            'Oral Polio Vaccine', 'Inactivated Polio Vaccine',
            'Pneumococcal Conjugate Vaccine', 'Measles Mumps and Rubella'
        ]
    ).order_by('vaccine_name')
    
    # Get available medicine stocks (for nutrition services)
    available_medicines = VaccineStock.objects.filter(
        available_stock__gt=0,
        vaccine_name__in=['Deworming Tablets', 'Vitamin A Capsules']
    ).order_by('vaccine_name')

    return render(request, 'HTML/preschooler_data.html', {
        'preschooler': preschooler,
        'bmi': bmi,
        'pending_schedules': pending_schedules,
        'immunization_history': immunization_history,
        'nutrition_services': nutrition_services,
        'age_years': age_years,
        'age_months': age_months,
        'age_days': age_days,
        'total_age_months': total_age_months,
        'nutritional_status': nutritional_status,
        'available_vaccines': available_vaccines,
        'available_medicines': available_medicines,
        'standard_weight': standard_weight,
        'standard_height': standard_height,
        'weight_for_age_status': weight_for_age_status,
        'height_for_age_status': height_for_age_status,
    })

def add_nutrition_service(request, preschooler_id):
    """Add completed nutrition service (Vitamin A or Deworming) for a preschooler"""
    if request.method == 'POST':
        try:
            preschooler = get_object_or_404(Preschooler, preschooler_id=preschooler_id)
            
            service_type = request.POST.get('service_type')
            completion_date = request.POST.get('completion_date')
            notes = request.POST.get('notes', '')
            
            # Validate that the service type is available in stock
            try:
                medicine_stock = VaccineStock.objects.get(vaccine_name=service_type)
                if medicine_stock.available_stock <= 0:
                    messages.error(request, f"{service_type} is out of stock.")
                    return redirect('preschooler_detail', preschooler_id=preschooler_id)
                
                # Deduct from stock immediately since it's already completed
                medicine_stock.available_stock -= 1
                medicine_stock.save()
                
            except VaccineStock.DoesNotExist:
                messages.error(request, f"{service_type} is not available in inventory.")
                return redirect('preschooler_detail', preschooler_id=preschooler_id)
            
            # Create nutrition service record as completed
            nutrition_service = NutritionService.objects.create(
                preschooler=preschooler,
                service_type=service_type,
                completion_date=completion_date,
                status='completed',
                notes=notes
            )
            
            messages.success(request, f"{service_type} recorded successfully. Stock updated.")
            return redirect('preschooler_detail', preschooler_id=preschooler_id)
            
        except Exception as e:
            messages.error(request, f"Error recording nutrition service: {str(e)}")
            return redirect('preschooler_detail', preschooler_id=preschooler_id)
    
    return redirect('preschooler_detail', preschooler_id=preschooler_id)

@csrf_exempt
def update_nutrition_status(request, nutrition_id):
    """Update nutrition service status (mark as completed)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            
            nutrition_service = get_object_or_404(NutritionService, id=nutrition_id)
            
            if status == 'completed':
                # Check if medicine is still available in stock
                try:
                    medicine_stock = VaccineStock.objects.get(vaccine_name=nutrition_service.service_type)
                    if medicine_stock.available_stock <= 0:
                        return JsonResponse({
                            'success': False,
                            'message': f"{nutrition_service.service_type} is out of stock."
                        })
                    
                    # Deduct from stock
                    medicine_stock.available_stock -= 1
                    medicine_stock.save()
                    
                    # Update nutrition service status
                    nutrition_service.status = 'completed'
                    nutrition_service.completion_date = timezone.now()
                    nutrition_service.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f"{nutrition_service.service_type} marked as completed. Stock updated."
                    })
                    
                except VaccineStock.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': f"{nutrition_service.service_type} not found in inventory."
                    })
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid status update.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating nutrition service: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@require_POST
@csrf_exempt
def update_schedule_status(request, schedule_id):
    """Update vaccination schedule status and handle stock deduction"""
    try:
        schedule = get_object_or_404(VaccinationSchedule, id=schedule_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in ['scheduled', 'completed', 'rescheduled', 'missed']:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid status'
            })
        
        old_status = schedule.status
        
        # Prevent duplicate completion
        if old_status == 'completed' and new_status == 'completed':
            return JsonResponse({
                'success': False,
                'message': 'This vaccination has already been completed'
            })
        
        schedule.status = new_status
        
        # Handle completion
        if new_status == 'completed':
            schedule.completion_date = timezone.now()
            schedule.administered_date = timezone.now().date()
            schedule.confirmed_by_parent = True
            
            # Only deduct stock if not already deducted
            if not schedule.stock_deducted:
                # Get preschooler's barangay for stock lookup
                preschooler_barangay = schedule.preschooler.barangay
                
                # Try to find vaccine stock with multiple lookup methods
                vaccine_stock = None
                
                # Method 1: Try with barangay first (if your VaccineStock has barangay field)
                try:
                    vaccine_stock = VaccineStock.objects.get(
                        vaccine_name=schedule.vaccine_name,
                        barangay=preschooler_barangay
                    )
                except VaccineStock.DoesNotExist:
                    pass
                
                # Method 2: Try exact match without barangay
                if not vaccine_stock:
                    try:
                        vaccine_stock = VaccineStock.objects.get(vaccine_name=schedule.vaccine_name)
                    except VaccineStock.DoesNotExist:
                        pass
                
                # Method 3: Try case-insensitive match
                if not vaccine_stock:
                    try:
                        vaccine_stock = VaccineStock.objects.get(vaccine_name__iexact=schedule.vaccine_name)
                    except VaccineStock.DoesNotExist:
                        pass
                
                # Method 4: Try partial match (contains)
                if not vaccine_stock:
                    vaccine_stock = VaccineStock.objects.filter(
                        vaccine_name__icontains=schedule.vaccine_name
                    ).first()
                
                if vaccine_stock:
                    if vaccine_stock.available_stock <= 0:
                        return JsonResponse({
                            'success': False,
                            'message': f'No stock available for {schedule.vaccine_name}. Current stock: {vaccine_stock.available_stock}'
                        })
                    
                    # Deduct stock based on required doses
                    doses_needed = schedule.required_doses or 1  # Default to 1 if None
                    
                    if vaccine_stock.available_stock < doses_needed:
                        return JsonResponse({
                            'success': False,
                            'message': f'Insufficient stock for {schedule.vaccine_name}. Required: {doses_needed}, Available: {vaccine_stock.available_stock}'
                        })
                    
                    # Deduct the required doses from stock
                    vaccine_stock.available_stock -= doses_needed
                    vaccine_stock.save()
                    
                    # Mark stock as deducted
                    schedule.stock_deducted = True
                    
                    print(f"Stock deducted for {schedule.vaccine_name}: {doses_needed} doses. Remaining stock: {vaccine_stock.available_stock}")
                    
                else:
                    # Log warning but continue - maybe you want to allow completion even without stock record
                    print(f"Warning: No stock record found for {schedule.vaccine_name}")
            
            schedule.save()
            
            # Log the activity (if you have this model)
            try:
                PreschoolerActivityLog.objects.create(
                    preschooler_name=f"{schedule.preschooler.first_name} {schedule.preschooler.last_name}",
                    activity=f"Vaccination completed: {schedule.vaccine_name}",
                    performed_by=request.user.username if request.user.is_authenticated else 'System',
                    barangay=schedule.preschooler.barangay
                )
            except Exception as log_error:
                # Don't fail the main operation if logging fails
                print(f"Warning: Could not create activity log: {log_error}")
            
            return JsonResponse({
                'success': True,
                'message': f'Vaccination completed successfully. Stock updated for {schedule.vaccine_name}.'
            })
        
        # Handle other status changes
        else:
            schedule.save()
            
            status_messages = {
                'scheduled': 'Vaccination rescheduled successfully',
                'rescheduled': 'Vaccination marked as rescheduled',
                'missed': 'Vaccination marked as missed'
            }
            
            return JsonResponse({
                'success': True,
                'message': status_messages.get(new_status, 'Status updated successfully')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data received'
        })
    except Exception as e:
        print(f"Error in update_schedule_status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating status: {str(e)}'
        })
    
@require_POST
def reschedule_vaccination(request):
    """Handle vaccination rescheduling"""
    schedule_id = request.POST.get('schedule_id')
    new_date = request.POST.get('new_date')
    reschedule_reason = request.POST.get('reschedule_reason', '')
    
    try:
        schedule = get_object_or_404(VaccinationSchedule, id=schedule_id)
        
        # Parse the new date
        from datetime import datetime
        new_schedule_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        
        # Update the schedule
        old_date = schedule.scheduled_date
        schedule.scheduled_date = new_schedule_date
        schedule.status = 'rescheduled'
        schedule.reschedule_reason = reschedule_reason
        schedule.save()
        
        # Log the activity
        PreschoolerActivityLog.objects.create(
            preschooler_name=f"{schedule.preschooler.first_name} {schedule.preschooler.last_name}",
            activity=f"Vaccination rescheduled: {schedule.vaccine_name} from {old_date} to {new_schedule_date}",
            performed_by=request.user.email if hasattr(request.user, 'email') else 'System',
            barangay=schedule.preschooler.barangay
        )
        
        messages.success(request, f'Vaccination successfully rescheduled to {new_schedule_date}')
        
    except Exception as e:
        messages.error(request, f'Error rescheduling vaccination: {str(e)}')
    
    return redirect('preschooler_detail', preschooler_id=schedule.preschooler.preschooler_id)
    
def update_preschooler_photo(request, preschooler_id):
    preschooler = get_object_or_404(Preschooler, preschooler_id=preschooler_id)

    if request.method == 'POST' and 'profile_photo' in request.FILES:
        preschooler.profile_photo = request.FILES['profile_photo']
        preschooler.save()
        return JsonResponse({
            'success': True,
            'new_photo_url': preschooler.profile_photo.url
        })

    return JsonResponse({'success': False}, status=400)

from django.db.models import Prefetch
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from .models import Preschooler, BMI, Temperature
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from .models import Preschooler, BMI, Temperature

def preschoolers(request):
    user_email = request.session.get('email')
    raw_role = (request.session.get('user_role') or '').strip().lower()
    
    print(f"=== PRESCHOOLERS VIEW DEBUG ===")
    print(f"Email: '{user_email}'")
    print(f"Raw Role: '{raw_role}'")
    print(f"Session data: {dict(request.session)}")
    
    # Get all active preschoolers
    if raw_role == 'admin':
        preschoolers_qs = Preschooler.objects.filter(is_archived=False)
    else:
        # For testing: show all preschoolers regardless of barangay
        preschoolers_qs = Preschooler.objects.filter(is_archived=False)
        print(f"Showing all active preschoolers for testing...")
    
    preschoolers_qs = preschoolers_qs.select_related('parent_id', 'barangay') \
        .prefetch_related(
            Prefetch('bmi_set', queryset=BMI.objects.order_by('-date_recorded'), to_attr='bmi_records'),
            Prefetch('temperature_set', queryset=Temperature.objects.order_by('-date_recorded'), to_attr='temp_records')
        )
    
    print(f"Found {preschoolers_qs.count()} preschoolers")
    
    # Pagination
    paginator = Paginator(preschoolers_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Process nutritional status and delivery place color coding
    for p in page_obj.object_list:
        # Handle BMI and nutritional status
        latest_bmi = None
        if hasattr(p, 'bmi_records') and p.bmi_records:
            latest_bmi = p.bmi_records[0]
        else:
            latest_bmi = p.bmi_set.order_by('-date_recorded').first()
        
        if latest_bmi and latest_bmi.bmi_value:
            bmi = latest_bmi.bmi_value
            if bmi < 13:
                p.nutritional_status = "Severely Underweight"
            elif 13 <= bmi < 14.9:
                p.nutritional_status = "Underweight"
            elif 14.9 <= bmi <= 17.5:
                p.nutritional_status = "Normal"
            elif 17.6 <= bmi <= 18.9:
                p.nutritional_status = "Overweight"
            elif bmi >= 19:
                p.nutritional_status = "Obese"
        else:
            p.nutritional_status = "N/A"
        
        # Add color coding for place of delivery
        delivery_place = getattr(p, 'place_of_delivery', None)
        print(f"Debug: {p.first_name} {p.last_name} - Place of delivery: '{delivery_place}'")  # Debug line
        
        if delivery_place:
            # Match exactly with your model choices
            if delivery_place == 'Home':
                p.delivery_class = 'delivery-home'
            elif delivery_place == 'Lying-in':
                p.delivery_class = 'delivery-lying-in'
            elif delivery_place == 'Hospital':
                p.delivery_class = 'delivery-hospital'
            elif delivery_place == 'Others':
                p.delivery_class = 'delivery-others'
            else:
                p.delivery_class = 'delivery-na'
        else:
            p.delivery_class = 'delivery-na'
        
        print(f"Debug: Assigned class: '{p.delivery_class}'")  # Debug line
    
    # Determine user role for template
    if raw_role in ['bhw', 'bns', 'midwife']:
        template_user_role = 'health_worker'
    else:
        template_user_role = raw_role
    
    context = {
        'preschoolers': page_obj,
        'user_email': user_email,
        'user_role': template_user_role,
        'original_role': raw_role,
        'barangay_name': 'Test Mode - All Barangays',
    }
    
    print(f"Template context:")
    print(f"  - user_role: '{template_user_role}'")
    print(f"  - original_role: '{raw_role}'")
    print(f"  - preschoolers count: {len(page_obj.object_list)}")
    print(f"=== END PRESCHOOLERS DEBUG ===")
    
    return render(request, 'HTML/preschoolers.html', context)

@login_required
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Allow account.barangay to be None safely
    account = get_object_or_404(Account.objects.select_related('profile_photo', 'barangay'), email=request.user.email)

    if request.method == 'POST':
        if 'photo' in request.FILES:
            photo_file = request.FILES['photo']
            if hasattr(account, 'profile_photo'):
                account.profile_photo.image = photo_file
                account.profile_photo.save()
            else:
                ProfilePhoto.objects.create(account=account, image=photo_file)
            return redirect('profile')

        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        contact = request.POST.get('contact_number')
        birthdate = request.POST.get('birthdate')
        barangay_id = request.POST.get('barangay')

        # ✅ Validate contact number
        if not contact or not contact.isdigit() or len(contact) != 11:
            messages.error(request, "Contact number must be exactly 11 digits.")
            return redirect('profile')

        account.full_name = full_name
        if address is not None:
            account.address = address
        account.contact_number = contact
        account.birthdate = birthdate or None

        # ✅ Handle first-time barangay selection
        if barangay_id:
            try:
                barangay = Barangay.objects.get(id=barangay_id)

                if account.barangay != barangay:
                    old_barangay = account.barangay
                    account.barangay = barangay
                    account.save()

                    if account.user_role.lower() == 'parent':
                        try:
                            parent = Parent.objects.get(email=account.email)
                            parent.barangay = barangay
                            parent.save()

                            # Update preschoolers
                            Preschooler.objects.filter(parent_id=parent).update(barangay=barangay)

                            # Log transfer
                            if old_barangay:  
                                ParentActivityLog.objects.create(
                                    parent=parent,
                                    activity=f"Transferred to {barangay.name}",
                                    barangay=old_barangay,
                                    timestamp=now()
                                )
                                ParentActivityLog.objects.create(
                                    parent=parent,
                                    activity=f"Recently transferred from {old_barangay.name}",
                                    barangay=barangay,
                                    timestamp=now()
                                )

                                for p in Preschooler.objects.filter(parent_id=parent):
                                    PreschoolerActivityLog.objects.create(
                                        preschooler_name=f"{p.first_name} {p.last_name}",
                                        performed_by=parent.full_name,
                                        activity=f"Transferred to {barangay.name}",
                                        barangay=old_barangay,
                                        timestamp=now()
                                    )
                                    PreschoolerActivityLog.objects.create(
                                        preschooler_name=f"{p.first_name} {p.last_name}",
                                        performed_by=parent.full_name,
                                        activity=f"Recently transferred from {old_barangay.name}",
                                        barangay=barangay,
                                        timestamp=now()
                                    )
                        except Parent.DoesNotExist:
                            pass
                else:
                    account.save()

            except Barangay.DoesNotExist:
                messages.error(request, "Selected barangay does not exist.")
                return redirect('profile')

        else:
            
            account.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    # On GET
    dashboard_url = reverse('parent_dashboard') if account.user_role.lower() == 'parent' else reverse('dashboard')
    barangays = Barangay.objects.all()

    return render(request, 'HTML/profile.html', {
        'account': account,
        'dashboard_url': dashboard_url,
        'barangays': barangays,
    })

def registered_parents(request):
    # Get the current user's account
    try:
        account = Account.objects.get(email=request.user.email)
    except Account.DoesNotExist:
        messages.error(request, "User account not found.")
        return redirect('dashboard')

    # More flexible role checking for BNS and other authorized roles
    user_role_lower = account.user_role.lower()
    
    # Check if user has permission - allow BHW, BNS, Midwife, Admin roles
    is_authorized = (
        'bhw' in user_role_lower or 
        'health worker' in user_role_lower or
        'bns' in user_role_lower or 
        'nutritional' in user_role_lower or 
        'nutrition' in user_role_lower or
        'scholar' in user_role_lower or
        'midwife' in user_role_lower or
        'nurse' in user_role_lower or
        'admin' in user_role_lower
    )
    
    if not is_authorized:
        print(f"DEBUG: User role '{account.user_role}' not authorized")
        messages.error(request, f"Your role ({account.user_role}) is not authorized to view registered parents.")
        return redirect('dashboard')

    print(f"DEBUG: User '{account.full_name}' with role '{account.user_role}' is authorized")

    # Determine user's barangay based on their role
    user_barangay = None
    
    # Method 1: Try to get barangay from BHW table (if user is BHW)
    try:
        bhw = BHW.objects.get(email__iexact=request.user.email)
        user_barangay = bhw.barangay
        print(f"DEBUG: Found BHW barangay: {user_barangay}")
    except BHW.DoesNotExist:
        print(f"DEBUG: No BHW found, checking other methods...")
        
        # Method 2: Try to find barangay through name matching
        bhw_by_name = BHW.objects.filter(full_name__iexact=account.full_name).first()
        if bhw_by_name:
            user_barangay = bhw_by_name.barangay
            print(f"DEBUG: Found barangay via name match: {user_barangay}")
        else:
            # Method 3: Try to find barangay through contact number
            bhw_by_contact = BHW.objects.filter(contact_number=account.contact_number).first()
            if bhw_by_contact:
                user_barangay = bhw_by_contact.barangay
                print(f"DEBUG: Found barangay via contact: {user_barangay}")
            else:
                # Method 4: Get default barangay from Barangay model
                print(f"DEBUG: No matching BHW profile found, getting default barangay")
                
                # Try to get 'Anabu' barangay from Barangay model
                try:
                    user_barangay = Barangay.objects.get(name__iexact='Anabu')
                    print(f"DEBUG: Found Anabu barangay: {user_barangay}")
                except Barangay.DoesNotExist:
                    # If Anabu doesn't exist, get the first available barangay
                    user_barangay = Barangay.objects.first()
                    if user_barangay:
                        print(f"DEBUG: Using first available barangay: {user_barangay}")
                    else:
                        # If no barangays exist, create one or show error
                        print(f"DEBUG: No barangays found in database")
                        messages.error(request, "No barangay found in system. Please contact admin to set up barangays.")
                        return redirect('dashboard')

    # Ensure we have a barangay before proceeding
    if not user_barangay:
        print(f"DEBUG: No barangay assigned, trying to get default barangay")
        try:
            # Try to get any barangay from the database
            user_barangay = Barangay.objects.first()
            if user_barangay:
                print(f"DEBUG: Using fallback barangay: {user_barangay}")
            else:
                messages.error(request, "No barangay available in system. Please contact admin.")
                return redirect('dashboard')
        except Exception as e:
            print(f"DEBUG: Error getting fallback barangay: {e}")
            messages.error(request, "Unable to determine barangay assignment. Please contact admin.")
            return redirect('dashboard')

    print(f"DEBUG: Final barangay assignment: {user_barangay}")

    # Get parents from the same barangay
    all_parents = Parent.objects.filter(barangay=user_barangay).order_by('-created_at')
    print(f"DEBUG: Found {all_parents.count()} parents in {user_barangay}")

    # Pagination
    paginator = Paginator(all_parents, 10)  # 10 parents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate children and age for each parent
    for parent in page_obj:
        preschoolers = Preschooler.objects.filter(parent_id=parent)
        for child in preschoolers:
            today = date.today()
            years = today.year - child.birth_date.year
            months = today.month - child.birth_date.month
            if today.day < child.birth_date.day:
                months -= 1
            if months < 0:
                years -= 1
                months += 12
            child.age_display = f"{years} year{'s' if years != 1 else ''} and {months} month{'s' if months != 1 else ''}"
        parent.children = preschoolers

    return render(request, 'HTML/registered_parent.html', {
        'account': account,
        'parents': page_obj,
        'user_barangay': user_barangay,  # Pass barangay info to template
    })

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName', '').strip()
        last_name = request.POST.get('lastName', '').strip()
        full_name = f"{first_name} {last_name}"
        email = request.POST.get('email', '').strip()
        contact = request.POST.get('contact', '').strip()
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')
        role = request.POST.get('role')  # ✅ "BHW", "BNS", or "Midwife"
        birthdate = request.POST.get('birthdate', '').strip()
        address = request.POST.get('address', '').strip()
        barangay_id = request.POST.get('barangay_id')

        print(f"[DEBUG] Registration attempt for: {full_name} ({role})")

        # --- VALIDATIONS ---
        if not all([first_name, last_name, email, contact, password, confirm, birthdate, address, barangay_id, role]):
            messages.error(request, "Please fill out all required fields.")
            return render(request, 'HTML/register.html', {'barangays': Barangay.objects.all()})

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'HTML/register.html', {'barangays': Barangay.objects.all()})

        if User.objects.filter(username=email).exists() or Account.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'HTML/register.html', {'barangays': Barangay.objects.all()})

        # ✅ Convert birthdate string to date object
        try:
            from datetime import datetime
            birthdate_obj = datetime.strptime(birthdate, '%Y-%m-%d').date()
            print(f"[DEBUG] Birthdate converted: {birthdate} -> {birthdate_obj}")
        except ValueError as e:
            print(f"[DEBUG] ❌ Birthdate conversion error: {e}")
            messages.error(request, "Invalid birthdate format. Please try again.")
            return render(request, 'HTML/register.html', {'barangays': Barangay.objects.all()})

        try:
            # ✅ Step 1: Create Django User (for authentication)
            print("[DEBUG] Creating Django User...")
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            print(f"[DEBUG] ✅ Django User created: {user.id}")

            # ✅ Step 2: Get Barangay
            barangay = Barangay.objects.get(id=int(barangay_id))
            print(f"[DEBUG] ✅ Barangay found: {barangay.name}")

            # ✅ Step 3: Create Account (this is all you need!)
            print("[DEBUG] Creating Account with all info...")
            account = Account.objects.create(
                full_name=full_name,
                email=email,
                contact_number=contact,
                address=address,
                birthdate=birthdate_obj,
                password=make_password(password),
                user_role=role,  # ✅ This stores BHW/BNS/Midwife role
                is_validated=False,
                is_rejected=False,
                barangay=barangay
            )
            print(f"[DEBUG] ✅ Account created successfully: {account.account_id}")
            print(f"[DEBUG] 🎉 REGISTRATION COMPLETED! Role: {role}")

        except Barangay.DoesNotExist:
            print(f"[DEBUG] ❌ Barangay not found: {barangay_id}")
            messages.error(request, "Invalid barangay selected.")
            return render(request, 'HTML/register.html', {'barangays': Barangay.objects.all()})
            
        except Exception as e:
            print(f"[DEBUG] ❌ Registration error: {e}")
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'HTML/register.html', {'barangays': Barangay.objects.all()})

        # ✅ Send confirmation email
        try:
            subject = f'✅ {role} Registration Received - PPMS Cluster 4'
            html_message = f"""
            <html>
              <body style="font-family:Arial,sans-serif; background:#f9f9f9; padding:20px;">
                <div style="background:#fff; padding:20px; border-radius:10px; max-width:600px; margin:auto;">
                  <h2 style="color:#007bff;">PPMS Cluster 4 – {role} Registration Received</h2>
                  <p>Hello <strong>{full_name}</strong>,</p>
                  <p>Thank you for registering as a <strong>{role}</strong> in PPMS Cluster 4.</p>
                  <p>Your account is <strong>pending admin approval</strong>. You'll be notified via email once approved.</p>
                  <p style="font-size:12px; color:#777;">&copy; 2025 PPMS Cluster 4 Imus City</p>
                </div>
              </body>
            </html>
            """
            plain_message = f"""
Hello {full_name},

Thank you for registering as a {role} with PPMS Cluster 4 Imus City.

Your account is currently pending validation by the admin.
You will receive another email once your account has been approved.
            """

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=True,
            )
            print(f"[DEBUG] ✅ Email sent to {email}")

        except Exception as email_error:
            print(f"[DEBUG] ⚠️ Email error (non-critical): {email_error}")

        # ✅ Success!
        messages.success(request, f"{role} registration successful. Pending admin approval.")
        return redirect('login')

    return render(request, 'HTML/register.html', {'barangays': Barangay.objects.all()})

def register_preschooler(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get account without barangay relation (it's broken)
    account = get_object_or_404(Account, email=request.user.email)

    # Check authorization first
    user_role_lower = account.user_role.lower()
    
    # Check if user has permission - allow BHW, BNS, Midwife, Admin roles
    is_authorized = (
        'bhw' in user_role_lower or 
        'health worker' in user_role_lower or
        'bns' in user_role_lower or 
        'nutritional' in user_role_lower or 
        'nutrition' in user_role_lower or
        'scholar' in user_role_lower or
        'midwife' in user_role_lower or
        'admin' in user_role_lower
    )
    
    if not is_authorized:
        print(f"DEBUG: User role '{account.user_role}' not authorized to register preschoolers")
        messages.error(request, f"Your role ({account.user_role}) is not authorized to register preschoolers.")
        return redirect('dashboard')

    print(f"DEBUG: User '{account.full_name}' with role '{account.user_role}' is authorized")

    # Determine user's barangay using the same logic as other views
    user_barangay = None
    
    # Method 1: Try to get barangay from BHW table
    try:
        bhw = BHW.objects.get(email__iexact=request.user.email)
        user_barangay = bhw.barangay
        print(f"DEBUG: Found BHW barangay: {user_barangay}")
    except BHW.DoesNotExist:
        print(f"DEBUG: No BHW found, checking other methods...")
        
        # Method 2: Try to find barangay through name matching
        bhw_by_name = BHW.objects.filter(full_name__iexact=account.full_name).first()
        if bhw_by_name:
            user_barangay = bhw_by_name.barangay
            print(f"DEBUG: Found barangay via name match: {user_barangay}")
        else:
            # Method 3: Try to find barangay through contact number
            bhw_by_contact = BHW.objects.filter(contact_number=account.contact_number).first()
            if bhw_by_contact:
                user_barangay = bhw_by_contact.barangay
                print(f"DEBUG: Found barangay via contact: {user_barangay}")
            else:
                # Method 4: Get default barangay from Barangay model
                print(f"DEBUG: No matching BHW profile found, getting default barangay")
                
                # Try to get 'Anabu' barangay from Barangay model
                try:
                    user_barangay = Barangay.objects.get(name__iexact='Anabu')
                    print(f"DEBUG: Found Anabu barangay: {user_barangay}")
                except Barangay.DoesNotExist:
                    # If Anabu doesn't exist, get the first available barangay
                    user_barangay = Barangay.objects.first()
                    if user_barangay:
                        print(f"DEBUG: Using first available barangay: {user_barangay}")
                    else:
                        print(f"DEBUG: No barangays found in database")
                        messages.error(request, "No barangay found in system. Please contact admin.")
                        return redirect('dashboard')

    # Ensure we have a barangay before proceeding
    if not user_barangay:
        print(f"DEBUG: No barangay assigned, trying to get default barangay")
        try:
            user_barangay = Barangay.objects.first()
            if user_barangay:
                print(f"DEBUG: Using fallback barangay: {user_barangay}")
            else:
                messages.error(request, "No barangay available in system. Please contact admin.")
                return redirect('dashboard')
        except Exception as e:
            print(f"DEBUG: Error getting fallback barangay: {e}")
            messages.error(request, "Unable to determine barangay assignment. Please contact admin.")
            return redirect('dashboard')

    print(f"DEBUG: Final barangay assignment: {user_barangay}")

    # Get parents from the same barangay
    parents_qs = Parent.objects.filter(barangay=user_barangay).order_by('-created_at')
    print(f"DEBUG: Found {parents_qs.count()} parents in {user_barangay}")

    # Pagination
    paginator = Paginator(parents_qs, 10)  # Show 10 parents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'HTML/register_preschooler.html', {
        'account': account,
        'parents': page_obj,
        'user_barangay': user_barangay,
    })

def registered_bhw(request):
    # Use same filter pattern as validate function
    bhw_list = Account.objects.filter(
        Q(user_role__iexact='healthworker') | Q(user_role__iexact='BHW'),
        is_validated=True
    )

    # Debug: Print what we found
    print(f"Found {bhw_list.count()} validated BHW accounts:")
    for bhw in bhw_list:
        print(f"- {bhw.full_name} (role: '{bhw.user_role}', validated: {bhw.is_validated})")

    for bhw in bhw_list:
        bhw.bhw_data = BHW.objects.filter(email=bhw.email).first()

        if bhw.last_activity:
            if timezone.now() - bhw.last_activity <= timedelta(minutes=1):
                bhw.last_activity_display = "🟢 Online"
            else:
                time_diff = timesince(bhw.last_activity, timezone.now())
                bhw.last_activity_display = f"{time_diff} ago"
        else:
            bhw.last_activity_display = "No activity"

    paginator = Paginator(bhw_list, 10)  # 10 BHWs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'HTML/registered_bhw.html', {
        'bhws': page_obj,
        'total_bhw_count': bhw_list.count()  # Para makita ninyo ang total
    })


def registered_bns(request):
    # Use the same filter pattern as validate function
    bns_list = Account.objects.filter(
        Q(user_role__iexact='bns') | 
        Q(user_role__iexact='BNS') |
        Q(user_role__iexact='Barangay Nutritional Scholar'),
        is_validated=True
    )

    # Debug: Print what we found
    print(f"Found {bns_list.count()} validated BNS accounts:")
    for bns in bns_list:
        print(f"- {bns.full_name} (role: '{bns.user_role}', validated: {bns.is_validated})")

    for bns in bns_list:
        if bns.last_activity:
            if timezone.now() - bns.last_activity <= timedelta(minutes=1):
                bns.last_activity_display = "🟢 Online"
            else:
                time_diff = timesince(bns.last_activity, timezone.now())
                bns.last_activity_display = f"{time_diff} ago"
        else:
            bns.last_activity_display = "No activity"

    paginator = Paginator(bns_list, 10)  # 10 BNS per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'HTML/registered_bns.html', {
        'bnss': page_obj,
        'total_bns_count': bns_list.count()  # Para makita ninyo ang total
    })

def registered_preschoolers(request):
    preschoolers_qs = Preschooler.objects.filter(is_archived=False) \
        .select_related('parent_id', 'barangay') \
        .prefetch_related(
            Prefetch('bmi_set', queryset=BMI.objects.order_by('-date_recorded'), to_attr='bmi_records'),
            Prefetch('temperature_set', queryset=Temperature.objects.order_by('-date_recorded'), to_attr='temp_records')
        )

    # Process nutritional status and delivery place color coding
    for p in preschoolers_qs:
        # Handle BMI and nutritional status
        latest_bmi = p.bmi_records[0] if hasattr(p, 'bmi_records') and p.bmi_records else None
        if latest_bmi:
            bmi = latest_bmi.bmi_value
            if bmi < 13:
                p.nutritional_status = "Severely Underweight"
            elif 13 <= bmi < 14.9:
                p.nutritional_status = "Underweight"
            elif 14.9 <= bmi <= 17.5:
                p.nutritional_status = "Normal"
            elif 17.6 <= bmi <= 18.9:
                p.nutritional_status = "Overweight"
            elif bmi >= 19:
                p.nutritional_status = "Obese"
        else:
            p.nutritional_status = "N/A"

        # Add color coding for place of delivery
        delivery_place = getattr(p, 'place_of_delivery', None)
        
        if delivery_place:
            # Match exactly with your model choices
            if delivery_place == 'Home':
                p.delivery_class = 'delivery-home'
            elif delivery_place == 'Lying-in':
                p.delivery_class = 'delivery-lying-in'
            elif delivery_place == 'Hospital':
                p.delivery_class = 'delivery-hospital'
            elif delivery_place == 'Others':
                p.delivery_class = 'delivery-others'
            else:
                p.delivery_class = 'delivery-na'
        else:
            p.delivery_class = 'delivery-na'

    paginator = Paginator(preschoolers_qs, 10)  # 10 preschoolers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    barangays = Barangay.objects.all()

    return render(request, 'HTML/registered_preschoolers.html', {
        'preschoolers': page_obj,
        'barangays': barangays,
    })

def reportTemplate(request):
    # Check if this is a PDF generation request (from admin dashboard)
    if request.GET.get('generate_pdf') == 'true':
        # Get all barangays and their data for admin report
        barangays = Barangay.objects.all()
        
        # Overall summary across all barangays
        overall_summary = {
            'Severely Underweight': 0,
            'Underweight': 0,
            'Normal': 0,
            'Overweight': 0,
            'Obese': 0,
        }
        
        barangay_details = []
        total_preschoolers = 0
        
        for barangay in barangays:
            preschoolers = Preschooler.objects.filter(
                barangay=barangay,
                is_archived=False
            ).prefetch_related(
                Prefetch('bmi_set', queryset=BMI.objects.order_by('-date_recorded'), to_attr='bmi_records')
            )
            
            # Barangay-specific summary
            barangay_summary = {
                'severely_underweight': 0,
                'underweight': 0,
                'normal': 0,
                'overweight': 0,
                'obese': 0,
            }
            
            barangay_count = preschoolers.count()
            total_preschoolers += barangay_count
            
            for p in preschoolers:
                latest_bmi = p.bmi_records[0] if hasattr(p, 'bmi_records') and p.bmi_records else None
                
                if latest_bmi and latest_bmi.bmi_value:
                    bmi = latest_bmi.bmi_value
                    if bmi < 13:
                        barangay_summary['severely_underweight'] += 1
                        overall_summary['Severely Underweight'] += 1
                    elif 13 <= bmi < 14.9:
                        barangay_summary['underweight'] += 1
                        overall_summary['Underweight'] += 1
                    elif 14.9 <= bmi <= 17.5:
                        barangay_summary['normal'] += 1
                        overall_summary['Normal'] += 1
                    elif 17.6 <= bmi <= 18.9:
                        barangay_summary['overweight'] += 1
                        overall_summary['Overweight'] += 1
                    else:
                        barangay_summary['obese'] += 1
                        overall_summary['Obese'] += 1
            
            # Calculate at-risk percentage (severely underweight + underweight + obese)
            at_risk_count = barangay_summary['severely_underweight'] + barangay_summary['underweight'] + barangay_summary['obese']
            at_risk_percentage = (at_risk_count / barangay_count * 100) if barangay_count > 0 else 0
            
            barangay_details.append({
                'name': barangay.name,
                'total_preschoolers': barangay_count,
                'severely_underweight': barangay_summary['severely_underweight'],
                'underweight': barangay_summary['underweight'],
                'normal': barangay_summary['normal'],
                'overweight': barangay_summary['overweight'],
                'obese': barangay_summary['obese'],
                'at_risk_percentage': round(at_risk_percentage, 1)
            })
        
        # Find highest count barangay
        highest_barangay = max(barangay_details, key=lambda x: x['total_preschoolers']) if barangay_details else None
        
        # Calculate total at-risk children
        total_at_risk = overall_summary['Severely Underweight'] + overall_summary['Underweight'] + overall_summary['Obese']
        
        # Get current account - handle both authenticated and anonymous users
        account = None
        if request.user.is_authenticated:
            try:
                account = Account.objects.get(email=request.user.email)
            except Account.DoesNotExist:
                # Create a default account info for display
                account = type('obj', (object,), {
                    'full_name': 'System Administrator',
                    'email': 'admin@system.local'
                })()
        else:
            # Create a default account info for anonymous users
            account = type('obj', (object,), {
                'full_name': 'System Administrator',
                'email': 'admin@system.local'
            })()
        
        # Render HTML for PDF
        html_string = render_to_string('HTML/reportTemplate.html', {
            'account': account,
            'barangay_details': barangay_details,
            'overall_summary': overall_summary,
            'total_barangays': barangays.count(),
            'total_preschoolers': total_preschoolers,
            'highest_barangay': highest_barangay,
            'total_at_risk': total_at_risk,
            'is_admin_report': True,
        })
        
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Overall-Barangay-Summary-Report.pdf"'
        return response
    
    # Default behavior - just render the template for preview
    return render(request, 'HTML/reportTemplate.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Validate email
        if not email:
            messages.error(request, 'Email address is required.')
            return render(request, 'HTML/forgot_password.html')
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'HTML/forgot_password.html')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'HTML/forgot_password.html')
        
        # Delete existing OTPs
        PasswordResetOTP.objects.filter(user=user, is_used=False).delete()
        
        # Create new OTP
        otp_instance = PasswordResetOTP.objects.create(user=user)
        
        # Compose email
        subject = '🔐 Password Reset OTP - PPMS Cluster 4'

        text_message = f"""
        Hello {user.first_name or user.username},

        You requested a password reset. Your OTP code is: {otp_instance.otp_code}

        This code will expire in 10 minutes.

        If you didn't request this, please ignore this email.
        """

        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <style>
            body {{
              font-family: Arial, sans-serif;
              background-color: #f9f9f9;
              padding: 20px;
              color: #333;
            }}
            .container {{
              background-color: #fff;
              padding: 20px;
              border-radius: 10px;
              max-width: 600px;
              margin: auto;
              box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
            .header {{
              background-color: #007bff;
              padding: 10px 20px;
              border-radius: 10px 10px 0 0;
              color: white;
              text-align: center;
            }}
            .otp {{
              font-size: 28px;
              font-weight: bold;
              color: #007bff;
              text-align: center;
              margin: 30px 0;
            }}
            .footer {{
              font-size: 12px;
              text-align: center;
              color: #777;
              margin-top: 30px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h2>PPMS Cluster 4 – Password Reset</h2>
            </div>

            <p>Hello <strong>{user.first_name or user.username}</strong>,</p>

            <p>You requested to reset your password. Please use the following OTP:</p>

            <div class="otp">{otp_instance.otp_code}</div>

            <p>This OTP is valid for <strong>10 minutes</strong>.</p>

            <p>If you did not make this request, you can safely ignore this email.</p>

            <div class="footer">
              &copy; 2025 PPMS Cluster 4 Imus City
            </div>
          </div>
        </body>
        </html>
        """

        try:
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send()

            messages.success(request, 'OTP sent to your email address.')
            return redirect('verify_otp', user_id=user.id)
        except Exception as e:
            print(f"[ERROR] Email send failed: {e}")
            messages.error(request, 'Failed to send email. Please try again.')

    return render(request, 'HTML/forgot_password.html')

def admin_registered_parents(request):
    # Ensure user is authenticated and is admin
    user_email = request.session.get('email')
    user_role = request.session.get('user_role', '').lower()

    if user_role != 'admin':
        return render(request, 'unauthorized.html')

    # Fetch all parents
    parents_qs = Parent.objects.select_related('barangay').order_by('-created_at')

    paginator = Paginator(parents_qs, 10)  # Show 10 parents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'HTML/admin_registeredparents.html', {
        'parents': page_obj,
        'user_email': user_email,
        'user_role': user_role
    })

def verify_otp(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # ✅ If resend is requested, generate a new OTP
    if request.method == 'GET' and request.GET.get('resend') == '1':
        # Mark any previous OTPs as used
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)

        # Generate and save new OTP
        new_otp = get_random_string(length=6, allowed_chars='0123456789')
        PasswordResetOTP.objects.create(user=user, otp_code=new_otp)

        # (Optional) Send the OTP to user's email here
        # send_mail(...)

        messages.success(request, 'A new OTP has been sent to your email.')

    # Existing POST logic
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()

        if not otp_code:
            messages.error(request, 'OTP code is required.')
            return render(request, 'HTML/verify_otp.html', {'user': user})

        if len(otp_code) != 6 or not otp_code.isdigit():
            messages.error(request, 'OTP must be exactly 6 digits.')
            return render(request, 'HTML/verify_otp.html', {'user': user})

        try:
            otp_instance = PasswordResetOTP.objects.get(
                user=user,
                otp_code=otp_code,
                is_used=False
            )

            if otp_instance.is_expired():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('verify_otp', user_id=user.id)

            otp_instance.is_used = True
            otp_instance.save()

            messages.success(request, 'OTP verified successfully.')
            return redirect('reset_password', user_id=user.id)

        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'HTML/verify_otp.html', {'user': user})

def reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Check if there's a recent used OTP for this user
    recent_otp = PasswordResetOTP.objects.filter(
        user=user,
        is_used=True,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
    ).first()
    
    if not recent_otp:
        messages.error(request, 'Session expired. Please start the process again.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Validate passwords
        if not password1 or not password2:
            messages.error(request, 'Both password fields are required.')
            return render(request, 'HTML/reset_password.html', {'user': user})
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'HTML/reset_password.html', {'user': user})
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'HTML/reset_password.html', {'user': user})
        
        # Additional password validation (optional)
        try:
            validate_password(password1, user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'HTML/reset_password.html', {'user': user})
        
        # Set new password
        user.set_password(password1)
        user.save()
        
        messages.success(request, 'Password reset successfully. You can now login with your new password.')
        return redirect('login')  # Replace with your login URL name
    
    return render(request, 'HTML/reset_password.html', {'user': user})
def remove_bns(request, account_id):
    if request.method == 'POST':
        bns = get_object_or_404(Account, pk=account_id, user_role="BNS")
        name = bns.full_name
        email = bns.email

        try:
            # Prepare email
            subject = 'PPMS Cluster 4 – Account Removal Notification'
            context = {
                'name': name,
            }

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8">
              <style>
                body {{
                  font-family: Arial, sans-serif;
                  background-color: #f9f9f9;
                  padding: 20px;
                  color: #333;
                }}
                .container {{
                  background-color: #fff;
                  padding: 20px;
                  border-radius: 10px;
                  max-width: 600px;
                  margin: auto;
                  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                  background-color: #dc3545;
                  padding: 10px 20px;
                  border-radius: 10px 10px 0 0;
                  color: white;
                  text-align: center;
                }}
                .footer {{
                  font-size: 12px;
                  text-align: center;
                  color: #777;
                  margin-top: 30px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <div class="header">
                  <h2>PPMS Cluster 4 – Account Removed</h2>
                </div>

                <p>Hello <strong>{name}</strong>,</p>

                <p>We would like to inform you that your account has been removed from the PPMS Cluster 4 system.</p>

                <p>If you believe this was a mistake or have any questions, please contact the system administrator.</p>

                <div class="footer">
                  &copy; 2025 PPMS Cluster 4 Imus City
                </div>
              </div>
            </body>
            </html>
            """

            text_message = f"""
            Hello {name},

            Your account has been removed from the PPMS Cluster 4 system.

            If you believe this was a mistake or have any questions, please contact the administrator.

            - PPMS Cluster 4 Imus City
            """

            email_message = EmailMultiAlternatives(
                subject,
                strip_tags(html_message),  # Fallback to plain text
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()

            # Delete account
            bns.delete()

            messages.success(request, f"{name} has been successfully removed and notified via email.")
        except Exception as e:
            print(f"[ERROR] Failed to remove BNS or send email: {e}")
            messages.error(request, "An error occurred while removing the BNS.")

    return redirect('registered_bns')

def remove_bhw(request, account_id):
    if request.method == 'POST':
        bhw = get_object_or_404(Account, pk=account_id)
        name = bhw.full_name
        email = bhw.email

        try:
            # Prepare email
            subject = 'PPMS Cluster 4 – Account Removal Notification'
            context = {
                'name': name,
            }

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8">
              <style>
                body {{
                  font-family: Arial, sans-serif;
                  background-color: #f9f9f9;
                  padding: 20px;
                  color: #333;
                }}
                .container {{
                  background-color: #fff;
                  padding: 20px;
                  border-radius: 10px;
                  max-width: 600px;
                  margin: auto;
                  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                  background-color: #dc3545;
                  padding: 10px 20px;
                  border-radius: 10px 10px 0 0;
                  color: white;
                  text-align: center;
                }}
                .footer {{
                  font-size: 12px;
                  text-align: center;
                  color: #777;
                  margin-top: 30px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <div class="header">
                  <h2>PPMS Cluster 4 – Account Removed</h2>
                </div>

                <p>Hello <strong>{name}</strong>,</p>

                <p>We would like to inform you that your account has been removed from the PPMS Cluster 4 system.</p>

                <p>If you believe this was a mistake or have any questions, please contact the system administrator.</p>

                <div class="footer">
                  &copy; 2025 PPMS Cluster 4 Imus City
                </div>
              </div>
            </body>
            </html>
            """

            text_message = f"""
            Hello {name},

            Your account has been removed from the PPMS Cluster 4 system.

            If you believe this was a mistake or have any questions, please contact the administrator.

            - PPMS Cluster 4 Imus City
            """

            email_message = EmailMultiAlternatives(
                subject,
                strip_tags(html_message),  # Fallback to plain text
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()

            # Delete account
            bhw.delete()

            messages.success(request, f"{name} has been successfully removed and notified via email.")
        except Exception as e:
            print(f"[ERROR] Failed to remove BHW or send email: {e}")
            messages.error(request, "An error occurred while removing the BHW.")

    return redirect('registered_bhw')

def registered_midwife(request):
    midwife_list = Account.objects.filter(user_role='midwife', is_validated=True)

    for midwife in midwife_list:
        # Assuming you have a Midwife model similar to BHW
        midwife.midwife_data = Midwife.objects.filter(email=midwife.email).first()

        if midwife.last_activity:
            if timezone.now() - midwife.last_activity <= timedelta(minutes=1):
                midwife.last_activity_display = "🟢 Online"
            else:
                time_diff = timesince(midwife.last_activity, timezone.now())
                midwife.last_activity_display = f"{time_diff} ago"
        else:
            midwife.last_activity_display = "No activity"

    paginator = Paginator(midwife_list, 10)  # 10 midwives per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'HTML/registered_midwife.html', {'midwives': page_obj})


def remove_midwife(request, account_id):
    if request.method == 'POST':
        midwife = get_object_or_404(Account, pk=account_id)
        name = midwife.full_name
        email = midwife.email

        try:
            # Prepare email
            subject = 'PPMS Cluster 4 – Account Removal Notification'
            context = {
                'name': name,
            }

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8">
              <style>
                body {{
                  font-family: Arial, sans-serif;
                  background-color: #f9f9f9;
                  padding: 20px;
                  color: #333;
                }}
                .container {{
                  background-color: #fff;
                  padding: 20px;
                  border-radius: 10px;
                  max-width: 600px;
                  margin: auto;
                  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                  background-color: #dc3545;
                  padding: 10px 20px;
                  border-radius: 10px 10px 0 0;
                  color: white;
                  text-align: center;
                }}
                .footer {{
                  font-size: 12px;
                  text-align: center;
                  color: #777;
                  margin-top: 30px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <div class="header">
                  <h2>PPMS Cluster 4 – Account Removed</h2>
                </div>

                <p>Hello <strong>{name}</strong>,</p>

                <p>We would like to inform you that your midwife account has been removed from the PPMS Cluster 4 system.</p>

                <p>If you believe this was a mistake or have any questions, please contact the system administrator.</p>

                <div class="footer">
                  &copy; 2025 PPMS Cluster 4 Imus City
                </div>
              </div>
            </body>
            </html>
            """

            text_message = f"""
            Hello {name},

            Your midwife account has been removed from the PPMS Cluster 4 system.

            If you believe this was a mistake or have any questions, please contact the administrator.

            - PPMS Cluster 4 Imus City
            """

            email_message = EmailMultiAlternatives(
                subject,
                strip_tags(html_message),  # Fallback to plain text
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()

            # Delete account
            midwife.delete()

            messages.success(request, f"{name} has been successfully removed and notified via email.")
        except Exception as e:
            print(f"[ERROR] Failed to remove midwife or send email: {e}")
            messages.error(request, "An error occurred while removing the midwife.")

    return redirect('registered_midwife')

def validate(request):
    """Display BHW, BNS, Midwife, and Nurse accounts - focusing on pending validation by default"""
    # Get filter parameters
    role_filter = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'pending')  # Default to pending only
    
    # Base queryset - BHW, BNS, Midwife, and Nurse accounts
    accounts = Account.objects.filter(
        Q(user_role__iexact='BHW') | 
        Q(user_role__iexact='healthworker') |
        Q(user_role__iexact='BNS') | 
        Q(user_role__iexact='bns') | 
        Q(user_role__iexact='Barangay Nutritional Scholar') |
        Q(user_role__iexact='Midwife') |
        Q(user_role__iexact='Nurse')  # Added Nurse here
    )
    
    # Apply status filter
    if status_filter == 'pending':
        accounts = accounts.filter(is_validated=False, is_rejected=False)
    elif status_filter == 'validated':
        accounts = accounts.filter(is_validated=True)
    elif status_filter == 'rejected':
        accounts = accounts.filter(is_rejected=True)
    # If status_filter == 'all', show all accounts
    
    # Apply role filter if specified
    if role_filter and role_filter != 'all':
        if role_filter.lower() == 'bns':
            accounts = accounts.filter(
                Q(user_role__iexact='bns') | 
                Q(user_role__iexact='BNS') |
                Q(user_role__iexact='Barangay Nutritional Scholar')
            )
        elif role_filter.lower() == 'healthworker':
            accounts = accounts.filter(
                Q(user_role__iexact='healthworker') |
                Q(user_role__iexact='BHW')
            )
        elif role_filter.lower() == 'midwife':
            accounts = accounts.filter(user_role__iexact='Midwife')
        elif role_filter.lower() == 'nurse':  # Added nurse filter
            accounts = accounts.filter(user_role__iexact='Nurse')
        else:
            accounts = accounts.filter(user_role=role_filter)
    
    accounts = accounts.order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(accounts, 10)  # Show 10 accounts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count statistics for display
    base_filter = (
        Q(user_role__iexact='BHW') | Q(user_role__iexact='healthworker') | 
        Q(user_role__iexact='BNS') | Q(user_role__iexact='bns') | 
        Q(user_role__iexact='Barangay Nutritional Scholar') | 
        Q(user_role__iexact='Midwife') |
        Q(user_role__iexact='Nurse')  # Added Nurse here
    )
    
    total_pending = Account.objects.filter(
        base_filter,
        is_validated=False,
        is_rejected=False
    ).count()
    
    bhw_pending = Account.objects.filter(
        Q(user_role__iexact='healthworker') | Q(user_role__iexact='BHW'),
        is_validated=False,
        is_rejected=False
    ).count()
    
    bns_pending = Account.objects.filter(
        Q(user_role__iexact='bns') | Q(user_role__iexact='BNS') | Q(user_role__iexact='Barangay Nutritional Scholar'),
        is_validated=False,
        is_rejected=False
    ).count()
    
    midwife_pending = Account.objects.filter(
        user_role__iexact='Midwife',
        is_validated=False,
        is_rejected=False
    ).count()
    
    nurse_pending = Account.objects.filter(  # Added nurse pending count
        user_role__iexact='Nurse',
        is_validated=False,
        is_rejected=False
    ).count()
    
    total_validated = Account.objects.filter(
        base_filter,
        is_validated=True
    ).count()
    
    total_rejected = Account.objects.filter(
        base_filter,
        is_rejected=True
    ).count()
    
    context = {
        'accounts': page_obj,
        'page_obj': page_obj,
        'current_filter': role_filter,
        'current_status': status_filter,
        'total_pending': total_pending,
        'bhw_pending': bhw_pending,
        'bns_pending': bns_pending,
        'midwife_pending': midwife_pending,
        'nurse_pending': nurse_pending,  # Pass nurse count to template
        'total_validated': total_validated,
        'total_rejected': total_rejected,
    }
    
    return render(request, 'HTML/validate.html', context)

@csrf_exempt
def validate_account(request, account_id):
    if request.method == 'POST':
        account = get_object_or_404(Account, pk=account_id)
        account.is_validated = True
        account.is_rejected = False
        account.save()

        # Send notification email
        if account.email:
            send_mail(
                'Account Validated',
                f"Hello {account.full_name}, your PPMS account ({account.user_role}) "
                f"has been validated. You can now log in.",
                settings.DEFAULT_FROM_EMAIL,
                [account.email],
                fail_silently=True,
            )

        # Show success message with role
        messages.success(
            request,
            f"{account.full_name} ({account.user_role}) has been validated and notified."
        )
        return redirect('validate')

@csrf_exempt
def reject_account(request, account_id):
    account = get_object_or_404(Account, account_id=account_id)

    account.is_validated = False
    account.is_rejected = True
    account.save()

    # ❗ Send rejection email with styled HTML
    if account.email:
        subject = '❌ Registration Rejected - PPMS Cluster 4'

        plain_message = f"""
Hello {account.full_name},

We regret to inform you that your registration to the PPMS Cluster 4 Imus City platform has been rejected.

If you believe this was a mistake, please contact the system administrator.

Thank you,
PPMS Admin
        """

        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <style>
            body {{
              font-family: Arial, sans-serif;
              background-color: #f9f9f9;
              padding: 20px;
              color: #333;
            }}
            .container {{
              background-color: #fff;
              padding: 20px;
              border-radius: 10px;
              max-width: 600px;
              margin: auto;
              box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
            .header {{
              background-color: #dc3545;
              padding: 10px 20px;
              border-radius: 10px 10px 0 0;
              color: white;
              text-align: center;
            }}
            .footer {{
              font-size: 12px;
              text-align: center;
              color: #777;
              margin-top: 30px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h2>PPMS Cluster 4 – Registration Rejected</h2>
            </div>

            <p>Hello <strong>{account.full_name}</strong>,</p>

            <p>We regret to inform you that your registration to the <strong>PPMS Cluster 4 Imus City</strong> platform has been <strong>rejected</strong>.</p>

            <p>If you believe this was a mistake, please contact the system administrator.</p>

            <div class="footer">
              &copy; 2025 PPMS Cluster 4 Imus City
            </div>
          </div>
        </body>
        </html>
        """

        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [account.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print("[EMAIL ERROR]", e)

    messages.success(request, f"{account.full_name} has been rejected and notified.")
    return redirect('validate')

def registered_nurse(request):
    nurse_list = Account.objects.filter(user_role='nurse', is_validated=True)
    for nurse in nurse_list:
        # Assuming you have a Nurse model similar to Midwife
        nurse.nurse_data = Nurse.objects.filter(email=nurse.email).first()
        if nurse.last_activity:
            if timezone.now() - nurse.last_activity <= timedelta(minutes=1):
                nurse.last_activity_display = "🟢 Online"
            else:
                time_diff = timesince(nurse.last_activity, timezone.now())
                nurse.last_activity_display = f"{time_diff} ago"
        else:
            nurse.last_activity_display = "No activity"
    paginator = Paginator(nurse_list, 10)  # 10 nurses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'HTML/registered_nurse.html', {'nurses': page_obj})


def remove_nurse(request, account_id):
    if request.method == 'POST':
        nurse = get_object_or_404(Account, pk=account_id, user_role="nurse")
        name = nurse.full_name
        email = nurse.email

        try:
            # Prepare email
            subject = 'PPMS Cluster 4 – Account Removal Notification'

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8">
              <style>
                body {{
                  font-family: Arial, sans-serif;
                  background-color: #f9f9f9;
                  padding: 20px;
                  color: #333;
                }}
                .container {{
                  background-color: #fff;
                  padding: 20px;
                  border-radius: 10px;
                  max-width: 600px;
                  margin: auto;
                  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                  background-color: #dc3545;
                  padding: 10px 20px;
                  border-radius: 10px 10px 0 0;
                  color: white;
                  text-align: center;
                }}
                .footer {{
                  font-size: 12px;
                  text-align: center;
                  color: #777;
                  margin-top: 30px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <div class="header">
                  <h2>PPMS Cluster 4 – Account Removed</h2>
                </div>

                <p>Hello <strong>{name}</strong>,</p>

                <p>We would like to inform you that your nurse account has been removed from the PPMS Cluster 4 system.</p>

                <p>If you believe this was a mistake or have any questions, please contact the system administrator.</p>

                <div class="footer">
                  &copy; 2025 PPMS Cluster 4 Imus City
                </div>
              </div>
            </body>
            </html>
            """

            text_message = f"""
            Hello {name},

            Your nurse account has been removed from the PPMS Cluster 4 system.

            If you believe this was a mistake or have any questions, please contact the administrator.

            - PPMS Cluster 4 Imus City
            """

            email_message = EmailMultiAlternatives(
                subject,
                strip_tags(html_message),  # Fallback to plain text
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()

            # Delete account
            nurse.delete()

            messages.success(request, f"{name} has been successfully removed and notified via email.")
        except Exception as e:
            print(f"[ERROR] Failed to remove nurse or send email: {e}")
            messages.error(request, "An error occurred while removing the nurse.")

    return redirect('registered_nurse')

def fix_existing_bns_records():
    """
    Run this once to fix any existing BNS records that might have wrong role names
    You can call this from Django shell or create a management command
    """
    try:
        # Find accounts that might be BNS but have wrong role
        bns_accounts = Account.objects.filter(
            Q(user_role__icontains='BNS') | 
            Q(user_role__icontains='bns') |
            Q(user_role='BNS')
        )
        
        count = 0
        for account in bns_accounts:
            if account.user_role != 'Barangay Nutritional Scholar':
                account.user_role = 'Barangay Nutritional Scholar'
                account.save()
                count += 1
                print(f"Fixed account: {account.full_name} - {account.email}")
        
        print(f"Fixed {count} BNS accounts")
        return count
        
    except Exception as e:
        print(f"Error fixing BNS records: {e}")
        return 0
    
@csrf_exempt
def register_preschooler_entry(request):
    if request.method == 'POST':
        try:
            # Required fields
            parent_id = request.POST.get('parent_id')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            birthdate = request.POST.get('birthdate')
            gender = request.POST.get('gender')

            # Optional fields
            place_of_birth = request.POST.get('place_of_birth', '').strip()
            birth_weight = request.POST.get('birth_weight', '').strip()
            birth_length = request.POST.get('birth_length', '').strip()
            time_of_birth = request.POST.get('time_of_birth', '').strip()   # ✅ fixed
            type_of_birth = request.POST.get('type_of_birth', '').strip()
            place_of_delivery = request.POST.get('place_of_delivery', '').strip()

            # Validate required fields
            if not all([parent_id, first_name, last_name, birthdate, gender]):
                return JsonResponse({'status': 'error', 'message': 'All required fields must be filled.'})

            # Parse and validate birthdate
            birth_date = datetime.strptime(birthdate, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

            # Validate numeric optional fields
            birth_weight_value = None
            birth_length_value = None

            if birth_weight:
                try:
                    birth_weight_value = float(birth_weight)
                    if birth_weight_value < 0:
                        return JsonResponse({'status': 'error', 'message': 'Birth weight cannot be negative.'})
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid birth weight format.'})

            if birth_length:
                try:
                    birth_length_value = float(birth_length)
                    if birth_length_value < 0:
                        return JsonResponse({'status': 'error', 'message': 'Birth length cannot be negative.'})
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid birth length format.'})

            # Validate time format if provided
            time_of_birth_value = None
            if time_of_birth:
                try:
                    datetime.strptime(time_of_birth, '%H:%M')  # must be HH:MM
                    time_of_birth_value = time_of_birth
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid time format. Please use HH:MM format.'})

            # Get parent object
            parent = Parent.objects.get(pk=parent_id)

            # Create preschooler
            preschooler = Preschooler.objects.create(
                first_name=first_name,
                last_name=last_name,
                sex=gender,
                birth_date=birth_date,
                age=age,
                address=parent.address,
                parent_id=parent,
                barangay=parent.barangay,
                place_of_birth=place_of_birth if place_of_birth else None,
                birth_weight=birth_weight_value,
                birth_height=birth_length_value,
                time_of_birth=time_of_birth_value,
                type_of_birth=type_of_birth if type_of_birth else None,
                place_of_delivery=place_of_delivery if place_of_delivery else None,
            )

            # Link to parent
            parent.registered_preschoolers.add(preschooler)

            return JsonResponse({'status': 'success', 'message': 'Preschooler registered successfully!'})

        except Parent.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Parent not found.'})
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid date format: {str(e)}'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Registration failed: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required #dinagadag
def add_vaccination_schedule(request, preschooler_id):
    preschooler = get_object_or_404(Preschooler, pk=preschooler_id)

    if request.method == "POST":
        vaccine_name = request.POST.get("vaccine_name")
        doses = request.POST.get("vaccine_doses")
        required_doses = request.POST.get("required_doses")
        scheduled_date = request.POST.get("immunization_date")
        next_schedule = request.POST.get("next_vaccine_schedule")

        # Assuming BHW is logged in via request.user.account
        bhw = get_object_or_404(BHW, email=request.user.email)

        VaccinationSchedule.objects.create(
            preschooler=preschooler,
            vaccine_name=vaccine_name,
            doses=doses,
            required_doses=required_doses,
            scheduled_date=scheduled_date,
            next_vaccine_schedule=next_schedule,
            administered_by=bhw  # Optional, can leave null initially
        )

        messages.success(request, "Vaccination schedule has been saved successfully.")
        return redirect("preschooler_details", preschooler_id=preschooler_id)

    return redirect("preschooler_details", preschooler_id=preschooler_id)

@csrf_exempt
def submit_bmi(request):
    """Handle BMI form submission"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        preschooler_id = request.POST.get('preschooler_id')
        if not preschooler_id or preschooler_id.strip() == '':
            return JsonResponse({'status': 'error', 'message': 'Preschooler ID is required'})
        
        preschooler_id = int(preschooler_id)
        weight = float(request.POST.get('weight'))
        height_cm = float(request.POST.get('height'))
        temperature = float(request.POST.get('temperature'))

        preschooler = get_object_or_404(Preschooler, pk=preschooler_id)

        # Calculate BMI
        height_m = height_cm / 100
        bmi_value = weight / (height_m ** 2)

        # --- UPDATE IF EXISTS ---
        from datetime import date
        today = date.today()

        # Try to get today's BMI record
        bmi_record, created = BMI.objects.update_or_create(
            preschooler_id=preschooler,
            date_recorded=today,
            defaults={
                'weight': weight,
                'height': height_cm,
                'bmi_value': bmi_value,
            }
        )

        # Same for temperature
        Temperature.objects.update_or_create(
            preschooler_id=preschooler,
            date_recorded=today,
            defaults={
                'temperature_value': temperature
            }
        )

        return JsonResponse({
            'status': 'success',
            'message': 'BMI and temperature recorded successfully',
            'data': {
                'bmi': round(bmi_value, 2),
                'weight': weight,
                'height': height_cm,
                'temperature': temperature,
                'updated': not created
            }
        })

    except Preschooler.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Preschooler not found'})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid number format: {str(e)}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'})


def bmi_form(request, preschooler_id):
    preschooler = get_object_or_404(Preschooler, pk=preschooler_id)
    return render(request, 'HTML/bmi_form.html', {'preschooler': preschooler})

@csrf_exempt
def remove_preschooler(request):
    if request.method == 'POST':
        preschooler_id = request.POST.get('preschooler_id')
        try:
            preschooler = Preschooler.objects.get(pk=preschooler_id)
            preschooler.is_archived = True
            preschooler.save()
            return JsonResponse({'status': 'success'})
        except Preschooler.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Preschooler not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


def archived_preschoolers(request):
    archived = Preschooler.objects.filter(is_archived=True)
    return render(request, 'HTML/archived.html', {
        'archived_preschoolers': archived
    })

@require_POST
def update_child_info(request, preschooler_id):
    preschooler = get_object_or_404(Preschooler, pk=preschooler_id)

    preschooler.place_of_birth = request.POST.get('place_of_birth') or ''
    preschooler.birth_weight = request.POST.get('birth_weight') or None
    preschooler.birth_height = request.POST.get('birth_height') or None
    preschooler.address = request.POST.get('address') or ''
    preschooler.save()

    if preschooler.parent_id:
        parent = preschooler.parent_id
        parent.mother_name = request.POST.get('mother_name') or ''
        parent.father_name = request.POST.get('father_name') or ''
        parent.save()

    messages.success(request, "Child information successfully updated.")
    return redirect('preschooler_detail', preschooler_id=preschooler.preschooler_id)

@login_required
def register_parent(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName', '').strip()
        last_name = request.POST.get('lastName', '').strip()
        email = request.POST.get('email', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        birthdate = request.POST.get('birthdate', '').strip()
        address = request.POST.get('address', '').strip()

        full_name = f"{first_name} {last_name}".strip()

        # 🔍 Find the BHW registering the parent (with flexible lookup and debugging)
        bhw = None
        barangay = None
        
        # Add debugging information
        print(f"DEBUG: Current user email: {request.user.email}")
        print(f"DEBUG: User authenticated: {request.user.is_authenticated}")
        
        try:
            # First try to find BHW by email
            bhw = BHW.objects.get(email__iexact=request.user.email)
            barangay = bhw.barangay  # This should already be a Barangay instance
            print(f"DEBUG: Found BHW directly: {bhw.full_name}, Barangay: {barangay}")
        except BHW.DoesNotExist:
            print(f"DEBUG: No BHW found with email {request.user.email}, checking Account table...")
            
            # If not BHW, try to find from Account model
            try:
                account = Account.objects.get(email__iexact=request.user.email)
                print(f"DEBUG: Found Account - Role: {account.user_role}, Name: {account.full_name}")
                
                # Check all possible roles that can register parents (case-insensitive)
                allowed_roles = ['bhw', 'BHW', 'barangay health worker', 'health worker', 'bns', 'BNS', 'barangay nutritional scholar', 'barangay nutrition scholar', 'nutritional scholar', 'nutrition scholar', 'midwife', 'MIDWIFE', 'admin', 'administrator']
                if account.user_role.lower() in [role.lower() for role in allowed_roles]:
                    print(f"DEBUG: User has authorized role: {account.user_role}")
                    
                    # Try multiple methods to find BHW/get barangay
                    # Method 1: Try to find BHW with this account info
                    bhw = BHW.objects.filter(full_name__iexact=account.full_name).first()
                    if bhw:
                        barangay = bhw.barangay  # This is a Barangay instance
                        print(f"DEBUG: Found matching BHW: {bhw.full_name}, Barangay: {barangay}")
                    else:
                        # Method 2: Try alternative lookups
                        bhw = BHW.objects.filter(contact_number=account.contact_number).first()
                        if bhw:
                            barangay = bhw.barangay  # This is a Barangay instance
                            print(f"DEBUG: Found BHW by contact: {bhw.full_name}, Barangay: {barangay}")
                        else:
                            # Method 3: Try to find by email (case-insensitive)
                            bhw = BHW.objects.filter(email__iexact=account.email).first()
                            if bhw:
                                barangay = bhw.barangay  # This is a Barangay instance
                                print(f"DEBUG: Found BHW by email: {bhw.full_name}, Barangay: {barangay}")
                            else:
                                # Method 4: Get default barangay from Barangay model
                                print(f"DEBUG: No matching BHW profile found, getting default barangay")
                                
                                # Try to get 'Anabu' barangay from Barangay model
                                try:
                                    barangay = Barangay.objects.get(name__iexact='Anabu')
                                    print(f"DEBUG: Found Anabu barangay: {barangay}")
                                except Barangay.DoesNotExist:
                                    # If Anabu doesn't exist, get the first available barangay
                                    barangay = Barangay.objects.first()
                                    if barangay:
                                        print(f"DEBUG: Using first available barangay: {barangay}")
                                    else:
                                        # If no barangays exist, create one or show error
                                        print(f"DEBUG: No barangays found in database")
                                        messages.error(request, "No barangay found in system. Please contact admin to set up barangays.")
                                        return redirect('register_parent')
                else:
                    print(f"DEBUG: User role '{account.user_role}' is not authorized to register parents")
                    print(f"DEBUG: Allowed roles: {allowed_roles}")
                    messages.error(request, f"Only authorized health workers (BHW, BNS, Midwife) can register parents. Your current role is: {account.user_role}")
                    return redirect('register_parent')
                    
            except Account.DoesNotExist:
                print(f"DEBUG: No Account found with email {request.user.email}")
                print(f"DEBUG: Available Account emails: {list(Account.objects.values_list('email', flat=True))}")
                messages.error(request, f"User account not found. Please contact admin.")
                return redirect('register_parent')
        except Exception as e:
            print(f"DEBUG: Unexpected error finding BHW: {e}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            messages.error(request, "An error occurred. Please try again.")
            return redirect('register_parent')

        # Ensure we have a barangay before proceeding
        if not barangay:
            print(f"DEBUG: No barangay assigned, trying to get default barangay")
            try:
                # Try to get any barangay from the database
                barangay = Barangay.objects.first()
                if barangay:
                    print(f"DEBUG: Using fallback barangay: {barangay}")
                else:
                    messages.error(request, "No barangay available in system. Please contact admin.")
                    return redirect('register_parent')
            except Exception as e:
                print(f"DEBUG: Error getting fallback barangay: {e}")
                messages.error(request, "Unable to determine barangay assignment. Please contact admin.")
                return redirect('register_parent')
            
        print(f"DEBUG: Final barangay assignment: {barangay} (Type: {type(barangay)})")

        # ❌ Check if email already exists
        if Parent.objects.filter(email__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            messages.error(request, "A parent/user with this email already exists.")
            return redirect('register_parent')

        # ❌ Check if contact number already exists in Parent
        if Parent.objects.filter(contact_number=contact_number).exists():
            messages.error(request, "A parent with this contact number already exists.")
            return redirect('register_parent')

        # 🔐 Generate password
        raw_password = generate_password()

        try:
            # ✅ 1. Create Django User with hashed password
            user = User.objects.create_user(
                username=email,
                email=email,
                password=raw_password
            )

            # ✅ 2. Create Parent (force password change)
            parent = Parent.objects.create(
                full_name=full_name,
                email=email,
                contact_number=contact_number,
                birthdate=birthdate,
                address=address,
                barangay=barangay,  # Use the barangay we found
                must_change_password=True,
                password=raw_password,
                created_at=timezone.now()
            )

            # ✅ 3. Create Account
            account = Account.objects.create(
                email=email,
                full_name=full_name,
                contact_number=contact_number,
                address=address,
                birthdate=birthdate,
                user_role='parent',
                is_validated=False,
                is_rejected=False,
                last_activity=timezone.now(),
                password=raw_password,
                must_change_password=True
            )

            # ✅ 4. Send email (same as before)
            subject = "PPMS Parent Registration Successful"
            text_message = f"""Hello {full_name},

Your parent account has been registered in the PPMS Cluster 4 system.

Login credentials:
Email: {email}
Password: {raw_password}

Please keep this information safe.

- PPMS Cluster 4 Imus City"""

            html_message = f"""
            <html><body>
            <h2>PPMS Cluster 4 – Parent Registration</h2>
            <p>Hello <strong>{full_name}</strong>,</p>
            <p>Your parent account has been successfully registered.</p>
            <p><strong>Credentials:</strong></p>
            <ul>
              <li><strong>Email:</strong> {email}</li>
              <li><strong>Password:</strong> {raw_password}</li>
            </ul>
            <p>Keep this safe.</p>
            </body></html>
            """

            send_mail(subject, text_message, None, [email], html_message=html_message)

            messages.success(request, f"Parent registered successfully!\nEmail: {email}\nPassword: {raw_password}")
            return redirect('register_parent')

        except IntegrityError as e:
            print(f"DEBUG: IntegrityError: {e}")
            messages.error(request, "Something went wrong. Please try again.")
            return redirect('register_parent')

    return render(request, 'HTML/register_parent.html')

def get_weight_for_age_standard(age_months, sex):
    """
    Returns standard weight (kg) for age based on WHO growth standards
    """
    weight_standards = {
        'Male': {
            12: 9.6, 18: 10.9, 24: 12.2, 30: 13.4, 36: 14.3,
            42: 15.2, 48: 16.0, 54: 16.8, 60: 17.5
        },
        'Female': {
            12: 9.0, 18: 10.2, 24: 11.5, 30: 12.7, 36: 13.8,
            42: 14.8, 48: 15.8, 54: 16.8, 60: 17.7
        }
    }
    
    if sex in weight_standards:
        ages = list(weight_standards[sex].keys())
        closest_age = min(ages, key=lambda x: abs(x - age_months))
        return weight_standards[sex][closest_age]
    return None

def get_height_for_age_standard(age_months, sex):
    """
    Returns standard height (cm) for age based on WHO growth standards
    """
    height_standards = {
        'Male': {
            12: 75.7, 18: 82.3, 24: 87.8, 30: 92.4, 36: 96.5,
            42: 100.4, 48: 104.1, 54: 107.7, 60: 111.2
        },
        'Female': {
            12: 74.2, 18: 80.7, 24: 86.4, 30: 91.1, 36: 95.1,
            42: 99.0, 48: 102.7, 54: 106.4, 60: 109.9
        }
    }
    
    if sex in height_standards:
        ages = list(height_standards[sex].keys())
        closest_age = min(ages, key=lambda x: abs(x - age_months))
        return height_standards[sex][closest_age]
    return None

def calculate_z_score(actual_value, standard_value, standard_deviation):
    """
    Calculate Z-score for growth parameters
    """
    if standard_value and standard_deviation:
        return (actual_value - standard_value) / standard_deviation
    return None

def interpret_z_score(z_score):
    """
    Interpret Z-score according to WHO standards
    """
    if z_score is None:
        return "N/A"
    elif z_score < -3:
        return "Severely low"
    elif -3 <= z_score < -2:
        return "Moderately low"
    elif -2 <= z_score <= 2:
        return "Normal"
    elif 2 < z_score <= 3:
        return "Above normal"
    else:
        return "Severely high"

def generate_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def change_password_first(request):
    if request.method == 'POST':
        email = request.session.get('email', '').strip()
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not email:
            messages.error(request, "Session expired. Please log in again.")
            return redirect('login')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('change_password_first')

        try:
            user = User.objects.get(username=email)
            user.set_password(new_password)
            user.save()

            parent = Parent.objects.get(email=email)
            parent.must_change_password = False
            parent.save()

            messages.success(request, "Password updated successfully! You can now log in.")
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, "User not found.")
        except Parent.DoesNotExist:
            messages.error(request, "Parent record not found.")

        return redirect('change_password_first')

    return render(request, 'HTML/parent_change_password.html')


def growth_checker(request):
    return render(request, 'HTML/growthcheck.html')


def growth_chart(request):
    return render(request, 'HTML/growth_chart.html')

@login_required
def history(request):
    try:
        account = Account.objects.get(email=request.user.email)
        barangay = account.barangay

        now = timezone.now()
        yesterday = now - timedelta(days=1)

        # Optional: delete old logs
        ParentActivityLog.objects.filter(barangay=barangay, timestamp__lt=yesterday).delete()
        PreschoolerActivityLog.objects.filter(barangay=barangay, timestamp__lt=yesterday).delete()

        # Get logs
        parent_logs = ParentActivityLog.objects.filter(barangay=barangay).select_related('parent').order_by('-timestamp')
        preschooler_logs = PreschoolerActivityLog.objects.filter(barangay=barangay).order_by('-timestamp')

        # ✅ Paginate each log type
        parent_paginator = Paginator(parent_logs, 10)
        preschooler_paginator = Paginator(preschooler_logs, 10)

        parent_page_number = request.GET.get('parent_page')
        preschooler_page_number = request.GET.get('preschooler_page')

        parent_logs_page = parent_paginator.get_page(parent_page_number)
        preschooler_logs_page = preschooler_paginator.get_page(preschooler_page_number)

        return render(request, 'HTML/history.html', {
            'account': account,
            'parent_logs': parent_logs_page,
            'preschooler_logs': preschooler_logs_page,
        })

    except Account.DoesNotExist:
        return render(request, 'HTML/history.html', {
            'parent_logs': [],
            'preschooler_logs': [],
        })


def admin_logs(request):
    if request.session.get('user_role') != 'admin':
        return redirect('login')

    now = timezone.now()
    yesterday = now - timedelta(days=1)

    # Delete logs older than 1 day
    ParentActivityLog.objects.filter(timestamp__lt=yesterday).delete()
    PreschoolerActivityLog.objects.filter(timestamp__lt=yesterday).delete()

    parent_logs_all = ParentActivityLog.objects.select_related('parent', 'barangay').order_by('-timestamp')
    preschooler_logs_all = PreschoolerActivityLog.objects.select_related('barangay').order_by('-timestamp')

    # Paginate
    parent_paginator = Paginator(parent_logs_all, 10)  # 10 per page
    preschooler_paginator = Paginator(preschooler_logs_all, 20)

    parent_page = request.GET.get('parent_page')
    preschooler_page = request.GET.get('preschooler_page')

    context = {
        'parent_logs': parent_paginator.get_page(parent_page),
        'preschooler_logs': preschooler_paginator.get_page(preschooler_page),
    }

    return render(request, 'HTML/admin_logs.html', context)

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User  # your Django User model

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)
        account = None

        if user is None:
            # Fallback to raw password
            try:
                account = Account.objects.get(email=email)
                if account.password != password:
                    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
            except Account.DoesNotExist:
                return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

            # 👇 if raw password matched, generate a token for mobile
            # pick some user to tie the JWT to
            # (better: ensure each Account links to an auth.User)
            user = User.objects.first()  

        else:
            # normal auth user matched
            try:
                account = Account.objects.get(email=email)
            except Account.DoesNotExist:
                return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        # ✅ issue tokens (works for both raw + auth)
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful",
            "account_id": account.account_id,
            "full_name": account.full_name,
            "user_role": account.user_role,
            "is_validated": account.is_validated,
            "email": account.email,
            "must_change_password": getattr(account, "must_change_password", False),

            # 🔑 tokens for mobile
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)




@method_decorator(csrf_exempt, name='dispatch')
class RegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        # Force JSON parsing
        if hasattr(request, '_body'):
            import json
            try:
                json_data = json.loads(request.body)
                request._full_data = json_data
            except:
                pass
        
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                account = serializer.save()
                return Response({
                    'message': 'Account created successfully',
                    'account': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response({
                    'error': 'Failed to create account',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def admin_dashboard_stats(request):
    """Get admin dashboard statistics"""
    try:
        # Total registered users (all accounts)
        total_registered = Account.objects.count()
        
        # Health workers count
        health_workers = Account.objects.filter(
            user_role__iexact='healthworker', 
            is_validated=True
        ).count()
        
        # Total preschoolers (not archived)
        total_preschoolers = Preschooler.objects.filter(is_archived=False).count()
        
        # Total barangays
        barangay_count = Barangay.objects.count()
        
        return Response({
            'total_registered': total_registered,
            'health_workers': health_workers,
            'total_preschoolers': total_preschoolers,
            'barangay_count': barangay_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to load dashboard stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def admin_recent_activity(request):
    """Get recent activity for admin dashboard"""
    try:
        activities = []
        
        # Get recent account registrations (last 7 days)
        recent_accounts = Account.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        for acc in recent_accounts:
            activities.append({
                'id': acc.account_id,
                'title': 'New Account Registration',
                'description': f'{acc.full_name} registered as {acc.user_role}',
                'timestamp': acc.created_at.isoformat(),
                'type': 'account'
            })
        
        # Get recent preschooler registrations
        recent_preschoolers = Preschooler.objects.filter(
            date_registered__gte=timezone.now() - timedelta(days=7),
            is_archived=False
        ).order_by('-date_registered')[:10]
        
        for child in recent_preschoolers:
            activities.append({
                'id': child.preschooler_id,
                'title': 'New Preschooler Registration',
                'description': f'{child.first_name} {child.last_name} registered in {child.barangay.name if child.barangay else "Unknown"}',
                'timestamp': child.date_registered.isoformat(),
                'type': 'preschooler'
            })
        
        # Get recent vaccinations (confirmed schedules)
        recent_vaccinations = VaccinationSchedule.objects.filter(
            confirmed_by_parent=True,
            administered_date__gte=timezone.now().date() - timedelta(days=7)
        ).order_by('-administered_date')[:5]
        
        for vax in recent_vaccinations:
            activities.append({
                'id': vax.id,
                'title': 'Vaccination Completed',
                'description': f'{vax.vaccine_name} administered to {vax.preschooler.first_name} {vax.preschooler.last_name}',
                'timestamp': timezone.make_aware(
                    timezone.datetime.combine(vax.administered_date, timezone.datetime.min.time())
                ).isoformat(),
                'type': 'vaccination'
            })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response({
            'activities': activities[:15]  # Return top 15 activities
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to load recent activity: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def admin_nutritional_overview(request):
    """Get nutritional status overview for admin dashboard"""
    try:
        # Get all preschoolers with BMI records
        preschoolers = Preschooler.objects.filter(is_archived=False).prefetch_related('bmi_set')
        
        nutritional_summary = {
            'normal': 0,
            'underweight': 0,
            'overweight': 0,
            'severely_underweight': 0,
            'obese': 0,
        }
        
        total_with_records = 0
        
        for preschooler in preschoolers:
            # Get latest BMI record
            latest_bmi = preschooler.bmi_set.order_by('-date_recorded').first()
            
            if latest_bmi:
                total_with_records += 1
                bmi_value = latest_bmi.bmi_value
                
                if bmi_value < 13:
                    nutritional_summary['severely_underweight'] += 1
                elif 13 <= bmi_value < 14.9:
                    nutritional_summary['underweight'] += 1
                elif 14.9 <= bmi_value <= 17.5:
                    nutritional_summary['normal'] += 1
                elif 17.6 <= bmi_value <= 18.9:
                    nutritional_summary['overweight'] += 1
                elif bmi_value >= 19:
                    nutritional_summary['obese'] += 1
        
        return Response({
            'nutritional_status': nutritional_summary,
            'total_with_records': total_with_records
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to load nutritional overview: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def admin_notifications(request):
    """Get notifications for admin dashboard"""
    try:
        notifications = []
        unread_count = 0
        
        # Pending account validations
        pending_accounts = Account.objects.filter(
            is_validated=False,
            is_rejected=False,
            user_role__iexact='healthworker'
        ).order_by('-created_at')
        
        for acc in pending_accounts:
            notifications.append({
                'id': acc.account_id,
                'type': 'validation_required',
                'title': 'Account Validation Required',
                'message': f'{acc.full_name} needs account validation',
                'timestamp': acc.created_at.isoformat(),
                'is_read': False
            })
            unread_count += 1
        
        # Recent preschooler registrations that need attention
        recent_preschoolers = Preschooler.objects.filter(
            date_registered__gte=timezone.now() - timedelta(days=3),
            is_archived=False,
            is_notif_read=False
        ).order_by('-date_registered')[:10]
        
        for child in recent_preschoolers:
            notifications.append({
                'id': child.preschooler_id,
                'type': 'new_registration',
                'title': 'New Preschooler Registration',
                'message': f'{child.first_name} {child.last_name} registered in {child.barangay.name if child.barangay else "Unknown"}',
                'timestamp': child.date_registered.isoformat(),
                'is_read': child.is_notif_read
            })
            if not child.is_notif_read:
                unread_count += 1
        
        # Low vaccine stock alerts (if applicable)
        try:
            from WebApp.models import VaccineStock
            low_stock = VaccineStock.objects.filter(available_stock__lt=10)
            
            for stock in low_stock:
                notifications.append({
                    'id': f'stock_{stock.id}',
                    'type': 'low_stock',
                    'title': 'Low Vaccine Stock',
                    'message': f'{stock.vaccine_name} in {stock.barangay.name if stock.barangay else "system"} is running low ({stock.available_stock} remaining)',
                    'timestamp': stock.last_updated.isoformat(),
                    'is_read': False
                })
                unread_count += 1
        except:
            pass  # VaccineStock model might not exist in all implementations
        
        # Sort notifications by timestamp (most recent first)
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response({
            'notifications': notifications[:20],  # Return top 20 notifications
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to load notifications: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@csrf_exempt
def get_user_profile(request):
    """Get current user's profile data"""
    try:
        # Get email from query parameter with validation
        email = request.GET.get('email', '').strip()
        
        if not email:
            logger.warning("Profile request without email parameter")
            return Response({
                'success': False,
                'error': 'Email parameter required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            logger.warning(f"Invalid email format: {email}")
            return Response({
                'success': False,
                'error': 'Invalid email format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch account with related data
        account = Account.objects.select_related('barangay', 'profile_photo').get(email=email)
        
        serializer = ProfileSerializer(account, context={'request': request})
        
        response_data = {
            'success': True,
            'data': {
                'account_id': account.account_id,
                'full_name': account.full_name or "",
                'email': account.email or "",
                'contact_number': account.contact_number or "",
                'address': account.address or "",
                'birthdate': account.birthdate.isoformat() if account.birthdate else None,
                'user_role': account.user_role or "",
                'barangay': {
                    'id': account.barangay.id if account.barangay else None,
                    'name': account.barangay.name if account.barangay else None,
                    'location': account.barangay.location if account.barangay else None,
                } if account.barangay else None,
                'profile_photo_url': serializer.get_profile_photo_url(account),
                'is_validated': account.is_validated,
                'created_at': account.created_at.isoformat() if account.created_at else None
            }
        }
        
        logger.info(f"Profile retrieved successfully for email: {email}")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Account.DoesNotExist:
        logger.warning(f"Account not found for email: {email}")
        return Response({
            'success': False,
            'error': 'Account not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error retrieving profile for {email}: {str(e)}")
        return Response({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@csrf_exempt
def update_user_profile(request):
    """Update user profile with enhanced validation + token + email fallback"""
    try:
        # ---------------- AUTHORIZATION ----------------
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'success': False,
                'error': 'Authorization token required'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(' ')[1]
        # TODO: Add your token validation logic here (e.g., decode JWT)

        # ---------------- REQUEST DATA ----------------
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Email can come from query params or request body
        email = request.GET.get('email', '').strip()
        if not email:
            email = data.get('email', '').strip() if data.get('email') else ""

        if not email:
            logger.warning("Profile update request without email")
            return Response({
                'success': False,
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ---------------- EMAIL VALIDATION ----------------
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            logger.warning(f"Invalid email format in update: {email}")
            return Response({
                'success': False,
                'error': 'Invalid email format'
            }, status=status.HTTP_400_BAD_REQUEST)

        account = Account.objects.select_related('barangay').get(email=email)

        # ---------------- VALIDATIONS ----------------
        validation_errors = []

        # Full name validation
        if 'full_name' in data:
            full_name = str(data['full_name']).strip()
            if not full_name:
                validation_errors.append('Full name cannot be empty')
            elif len(full_name) > 100:
                validation_errors.append('Full name must be less than 100 characters')
            else:
                account.full_name = full_name

        # Address validation
        if 'address' in data:
            address = str(data['address']).strip() if data['address'] else ""
            if len(address) > 255:
                validation_errors.append('Address must be less than 255 characters')
            else:
                account.address = address

        # Contact number validation
        if 'contact_number' in data:
            contact = str(data['contact_number']).strip() if data['contact_number'] else ""
            if contact:  # Only validate if not empty
                if len(contact) not in [11, 12]:
                    validation_errors.append('Contact number must be 11 or 12 digits')
                elif not contact.isdigit():
                    validation_errors.append('Contact number must contain only digits')
                elif not (contact.startswith('09') or contact.startswith('639')):
                    validation_errors.append('Contact number must start with 09 or 639')
                else:
                    account.contact_number = contact
            else:
                account.contact_number = ""

        # Birthdate validation
        if 'birthdate' in data:
            birthdate_str = data['birthdate']
            if birthdate_str:
                try:
                    from datetime import datetime, date
                    birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
                    if birthdate > date.today():
                        validation_errors.append('Birthdate cannot be in the future')
                    else:
                        account.birthdate = birthdate
                except ValueError:
                    validation_errors.append('Invalid birthdate format. Use YYYY-MM-DD')
            else:
                account.birthdate = None

        # Stop early if validation fails
        if validation_errors:
            logger.warning(f"Validation errors for {email}: {validation_errors}")
            return Response({
                'success': False,
                'error': '; '.join(validation_errors)
            }, status=status.HTTP_400_BAD_REQUEST)

        # ---------------- BARANGAY HANDLING ----------------
        if 'barangay_id' in data and data['barangay_id']:
            try:
                barangay = Barangay.objects.get(id=int(data['barangay_id']))
                old_barangay = account.barangay
                account.barangay = barangay

                if account.user_role and account.user_role.lower() == 'parent':
                    try:
                        parent = Parent.objects.get(email=account.email)
                        parent.barangay = barangay
                        parent.save()
                        Preschooler.objects.filter(parent_id=parent).update(barangay=barangay)
                        logger.info(f"Updated barangay for parent and children: {email}")
                    except Parent.DoesNotExist:
                        logger.warning(f"Parent record not found for account: {email}")
                        pass
            except (Barangay.DoesNotExist, ValueError, TypeError):
                logger.warning(f"Invalid barangay_id: {data.get('barangay_id')}")
                return Response({
                    'success': False,
                    'error': 'Selected barangay does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)

        # ---------------- SAVE ----------------
        account.save()
        logger.info(f"Profile updated successfully for: {email}")

        # Serialize updated account
        serializer = ProfileSerializer(account, context={'request': request})

        response_data = {
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'account_id': account.account_id,
                'full_name': account.full_name or "",
                'email': account.email or "",
                'contact_number': account.contact_number or "",
                'address': account.address or "",
                'birthdate': account.birthdate.isoformat() if account.birthdate else None,
                'user_role': account.user_role or "",
                'barangay': {
                    'id': account.barangay.id if account.barangay else None,
                    'name': account.barangay.name if account.barangay else None,
                    'location': account.barangay.location if account.barangay else None,
                } if account.barangay else None,
                'profile_photo_url': serializer.get_profile_photo_url(account),
                'is_validated': account.is_validated,
                'created_at': account.created_at.isoformat() if account.created_at else None
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Account.DoesNotExist:
        logger.warning(f"Account not found for update: {request.GET.get('email', data.get('email', 'unknown'))}")
        return Response({
            'success': False,
            'error': 'Account not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return Response({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error updating profile: {str(e)}")
        return Response({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@csrf_exempt
def get_barangays(request):
    """Get list of all barangays"""
    try:
        barangays = Barangay.objects.all().order_by('name')
        barangay_list = []
        
        for barangay in barangays:
            barangay_list.append({
                'id': barangay.id,
                'name': barangay.name,
                'location': barangay.location or ''
            })
        
        return Response({
            'success': True,
            'barangays': barangay_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def parent_dashboard_api(request):
    """Get parent dashboard data"""
    try:
        # Get parent by email
        parent = get_object_or_404(Parent, email=request.user.email)
        
        # Get preschoolers
        preschoolers_data = []
        preschoolers_raw = Preschooler.objects.filter(
            parent_id=parent,
            is_archived=False
        ).prefetch_related('bmi_set', 'temperature_set')
        
        today = date.today()
        
        for p in preschoolers_raw:
            # Calculate age
            birth_date = p.birth_date
            age_years = today.year - birth_date.year
            age_months = today.month - birth_date.month
            
            if today.day < birth_date.day:
                age_months -= 1
            if age_months < 0:
                age_years -= 1
                age_months += 12
            
            # Get latest BMI and temperature
            latest_bmi = p.bmi_set.order_by('-date_recorded').first()
            latest_temp = p.temperature_set.order_by('-date_recorded').first()
            
            # Determine nutritional status
            nutritional_status = "N/A"
            if latest_bmi:
                bmi_value = latest_bmi.bmi_value
                if bmi_value < 13:
                    nutritional_status = "Severely Underweight"
                elif 13 <= bmi_value < 14.9:
                    nutritional_status = "Underweight"
                elif 14.9 <= bmi_value <= 17.5:
                    nutritional_status = "Normal"
                elif 17.6 <= bmi_value <= 18.9:
                    nutritional_status = "Overweight"
                elif bmi_value >= 19:
                    nutritional_status = "Obese"
            
            preschooler_data = {
                'preschooler_id': p.preschooler_id,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'sex': p.sex,
                'birth_date': p.birth_date.strftime('%Y-%m-%d'),
                'age': age_years,
                'age_months': age_months,
                'address': p.address,
                'nutritional_status': nutritional_status,
                'barangay': p.barangay.name if p.barangay else None,
                'profile_photo': p.profile_photo.url if p.profile_photo else None,
                'latest_bmi': {
                    'bmi_id': latest_bmi.bmi_id,
                    'weight': latest_bmi.weight,
                    'height': latest_bmi.height,
                    'bmi_value': latest_bmi.bmi_value,
                    'date_recorded': latest_bmi.date_recorded.strftime('%Y-%m-%d')
                } if latest_bmi else None,
                'latest_temperature': {
                    'temperature_id': latest_temp.temperature_id,
                    'temperature_value': latest_temp.temperature_value,
                    'date_recorded': latest_temp.date_recorded.strftime('%Y-%m-%d')
                } if latest_temp else None
            }
            preschoolers_data.append(preschooler_data)
        
        # Get upcoming vaccination schedules
        upcoming_schedules = VaccinationSchedule.objects.filter(
            preschooler__in=preschoolers_raw,
            confirmed_by_parent=False,
            scheduled_date__gte=timezone.now().date()
        ).select_related('preschooler').order_by('scheduled_date')
        
        schedules_data = []
        for schedule in upcoming_schedules:
            schedules_data.append({
                'id': schedule.id,
                'preschooler': {
                    'preschooler_id': schedule.preschooler.preschooler_id,
                    'first_name': schedule.preschooler.first_name,
                    'last_name': schedule.preschooler.last_name
                },
                'vaccine_name': schedule.vaccine_name,
                'doses': schedule.doses,
                'required_doses': schedule.required_doses,
                'scheduled_date': schedule.scheduled_date.strftime('%Y-%m-%d'),
                'next_vaccine_schedule': schedule.next_vaccine_schedule.strftime('%Y-%m-%d') if schedule.next_vaccine_schedule else None,
                'confirmed_by_parent': schedule.confirmed_by_parent,
                'administered_date': schedule.administered_date.strftime('%Y-%m-%d') if schedule.administered_date else None,
                'lapsed': schedule.lapsed
            })
        
        # Parent info
        parent_info = {
            'full_name': parent.full_name,
            'email': parent.email,
            'contact_number': parent.contact_number,
            'barangay': parent.barangay.name if parent.barangay else None
        }
        
        return Response({
            'preschoolers': preschoolers_data,
            'upcoming_schedules': schedules_data,
            'parent_info': parent_info
        }, status=status.HTTP_200_OK)
        
    except Parent.DoesNotExist:
        return Response({
            'error': 'Parent not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to load dashboard data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def confirm_vaccination_api(request):
    """Confirm vaccination schedule"""
    try:
        schedule_id = request.data.get('schedule_id')
        if not schedule_id:
            return Response({
                'success': False,
                'error': 'Schedule ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the schedule and verify it belongs to the parent
        schedule = get_object_or_404(VaccinationSchedule, id=schedule_id)
        
        # Verify the schedule belongs to this parent
        if schedule.preschooler.parent_id.email != request.user.email:
            return Response({
                'success': False,
                'error': 'Unauthorized access'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Confirm the schedule
        schedule.confirmed_by_parent = True
        schedule.administered_date = timezone.now().date()
        schedule.save()
        
        # Create next dose if needed
        if (schedule.next_vaccine_schedule and 
            schedule.doses < schedule.required_doses):
            
            # Check if next dose already exists
            existing = VaccinationSchedule.objects.filter(
                preschooler=schedule.preschooler,
                vaccine_name=schedule.vaccine_name,
                doses=schedule.doses + 1
            ).exists()
            
            if not existing:
                VaccinationSchedule.objects.create(
                    preschooler=schedule.preschooler,
                    vaccine_name=schedule.vaccine_name,
                    doses=schedule.doses + 1,
                    required_doses=schedule.required_doses,
                    scheduled_date=schedule.next_vaccine_schedule,
                    scheduled_by=schedule.scheduled_by,
                    confirmed_by_parent=False
                )
        
        return Response({
            'success': True,
            'message': 'Vaccination confirmed successfully'
        }, status=status.HTTP_200_OK)
        
    except VaccinationSchedule.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Vaccination schedule not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to confirm vaccination: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def preschooler_detail_api(request, preschooler_id):
    """Get detailed preschooler information"""
    try:
        # Get preschooler and verify it belongs to the parent
        preschooler = get_object_or_404(
            Preschooler,
            preschooler_id=preschooler_id,
            parent_id__email=request.user.email,
            is_archived=False
        )
        
        # Calculate age
        today = date.today()
        birth_date = preschooler.birth_date
        age_years = today.year - birth_date.year
        age_months = today.month - birth_date.month
        
        if today.day < birth_date.day:
            age_months -= 1
        if age_months < 0:
            age_years -= 1
            age_months += 12
        
        # Get BMI history
        bmi_history = []
        for bmi in preschooler.bmi_set.order_by('-date_recorded')[:10]:
            bmi_history.append({
                'bmi_id': bmi.bmi_id,
                'weight': bmi.weight,
                'height': bmi.height,
                'bmi_value': bmi.bmi_value,
                'date_recorded': bmi.date_recorded.strftime('%Y-%m-%d')
            })
        
        # Get temperature history
        temp_history = []
        for temp in preschooler.temperature_set.order_by('-date_recorded')[:10]:
            temp_history.append({
                'temperature_id': temp.temperature_id,
                'temperature_value': temp.temperature_value,
                'date_recorded': temp.date_recorded.strftime('%Y-%m-%d')
            })
        
        # Get vaccination history
        vaccination_history = []
        for vax in preschooler.vaccination_schedules.all().order_by('-scheduled_date'):
            vaccination_history.append({
                'id': vax.id,
                'vaccine_name': vax.vaccine_name,
                'doses': vax.doses,
                'required_doses': vax.required_doses,
                'scheduled_date': vax.scheduled_date.strftime('%Y-%m-%d'),
                'confirmed_by_parent': vax.confirmed_by_parent,
                'administered_date': vax.administered_date.strftime('%Y-%m-%d') if vax.administered_date else None
            })
        
        # Nutritional status
        latest_bmi = preschooler.bmi_set.order_by('-date_recorded').first()
        nutritional_status = "N/A"
        if latest_bmi:
            bmi_value = latest_bmi.bmi_value
            if bmi_value < 13:
                nutritional_status = "Severely Underweight"
            elif 13 <= bmi_value < 14.9:
                nutritional_status = "Underweight"
            elif 14.9 <= bmi_value <= 17.5:
                nutritional_status = "Normal"
            elif 17.6 <= bmi_value <= 18.9:
                nutritional_status = "Overweight"
            elif bmi_value >= 19:
                nutritional_status = "Obese"
        
        preschooler_data = {
            'preschooler_id': preschooler.preschooler_id,
            'first_name': preschooler.first_name,
            'last_name': preschooler.last_name,
            'sex': preschooler.sex,
            'birth_date': preschooler.birth_date.strftime('%Y-%m-%d'),
            'age': age_years,
            'age_months': age_months,
            'address': preschooler.address,
            'nutritional_status': nutritional_status,
            'barangay': preschooler.barangay.name if preschooler.barangay else None,
            'profile_photo': preschooler.profile_photo.url if preschooler.profile_photo else None,
            'place_of_birth': preschooler.place_of_birth,
            'birth_weight': preschooler.birth_weight,
            'birth_height': preschooler.birth_height
        }
        
        return Response({
            'preschooler': preschooler_data,
            'vaccination_history': vaccination_history,
            'bmi_history': bmi_history,
            'temperature_history': temp_history
        }, status=status.HTTP_200_OK)
        
    except Preschooler.DoesNotExist:
        return Response({
            'error': 'Preschooler not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to load preschooler details: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def manage_announcements(request):
    """
    View to display all announcements with options to add, edit, delete
    """
    try:
        announcements = Announcement.objects.all().order_by('-created_at')
    except Exception as e:
        messages.error(request, 'Error loading announcements. Please ensure the database is properly set up.')
        announcements = []
    
    context = {
        'announcements': announcements,
        'account': request.user,
    }
    
    return render(request, 'HTML/manage_announcements.html', context)

def add_announcement(request):
    """
    View to add a new announcement with manual user handling
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image', None)
        
        if title and content:
            try:
                # Manual user retrieval
                if hasattr(request, 'user') and request.user.is_authenticated:
                    # Get the actual User object from the database
                    user_obj = User.objects.get(id=request.user.id)
                    created_by = user_obj
                else:
                    created_by = None
                
                announcement = Announcement.objects.create(
                    title=title,
                    content=content,
                    image=image,
                    is_active=is_active,
                    created_by=created_by,
                    created_at=timezone.now()
                )
                messages.success(request, 'Announcement added successfully!')
                
            except User.DoesNotExist:
                messages.error(request, 'User not found. Please log in again.')
            except Exception as e:
                messages.error(request, f'Error creating announcement: {str(e)}')
        else:
            messages.error(request, 'Title and content are required!')
    
    return redirect('manage_announcements')

def edit_announcement(request, announcement_id):
    """
    View to edit an existing announcement with image replacement support
    """
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        announcement.title = request.POST.get('title')
        announcement.content = request.POST.get('content')
        announcement.priority = request.POST.get('priority', 'normal')
        announcement.is_active = request.POST.get('is_active') == 'on'
        announcement.updated_at = timezone.now()
        
        # Handle image replacement
        new_image = request.FILES.get('image', None)
        if new_image:
            # Delete old image if it exists
            if announcement.image:
                try:
                    # Delete the old image file from storage
                    import os
                    if os.path.exists(announcement.image.path):
                        os.remove(announcement.image.path)
                except Exception as e:
                    # Log the error but don't fail the update
                    print(f"Error deleting old image: {str(e)}")
            
            # Assign new image
            announcement.image = new_image
        
        if announcement.title and announcement.content:
            try:
                announcement.save()
                messages.success(request, 'Announcement updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating announcement: {str(e)}')
        else:
            messages.error(request, 'Title and content are required!')
    
    return redirect('manage_announcements')

def delete_announcement(request, announcement_id):
    """
    View to delete an announcement
    """
    if request.method == 'POST':
        try:
            announcement = get_object_or_404(Announcement, id=announcement_id)
            
            # Delete associated image file if it exists
            if announcement.image:
                try:
                    import os
                    if os.path.exists(announcement.image.path):
                        os.remove(announcement.image.path)
                except Exception as e:
                    print(f"Error deleting image file: {str(e)}")
            
            announcement.delete()
            messages.success(request, 'Announcement deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting announcement: {str(e)}')
    
    return redirect('manage_announcements')

def registered_barangays(request):
    # Get search query
    query = request.GET.get("search", "").strip()
    
    # Fetch barangays with optional search - ordered by most recent first
    barangays = Barangay.objects.all().order_by("-date_created")  # ✅ Order by date_created
    
    if query:
        barangays = barangays.filter(
            Q(name__icontains=query) | 
            Q(location__icontains=query) |
            Q(email__icontains=query) |
            Q(health_center__icontains=query)
        )
    
    # Pagination (10 barangays per page)
    paginator = Paginator(barangays, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "barangays": page_obj,
    }
    return render(request, "HTML/barangay_list.html", context)

@csrf_exempt
def get_announcement_data(request, announcement_id):
    """
    API endpoint to get announcement data for editing (AJAX)
    """
    if request.method == 'GET':
        try:
            announcement = get_object_or_404(Announcement, id=announcement_id)
            data = {
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'priority': announcement.priority,
                'is_active': announcement.is_active,
                'image_url': announcement.image.url if announcement.image else None,
            }
            return JsonResponse({'status': 'success', 'data': data})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def get_latest_weight(request):
    """Return the latest weight data from hardware"""
    try:
        
        latest_weight = 0.0  # Get from your hardware source
        
        return JsonResponse({'weight': latest_weight})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_latest_temp(request):
    """Return the latest temperature data from hardware"""
    try:
        # Replace this with your actual logic to get temperature from hardware/database
        latest_temp = 0.0  # Get from your hardware source
        
        return JsonResponse({'temperature': latest_temp})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_latest_distance(request):
    """Return the latest distance data from hardware"""
    try:
        # Replace this with your actual logic to get distance from hardware/database
        latest_distance = 0.0  # Get from your hardware source
        
        return JsonResponse({'distance': latest_distance})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    







# ✅ API: Change Password on First Login
@api_view(['POST'])
@permission_classes([AllowAny])
def api_change_password_first(request):
    email = request.data.get('email', '').strip()
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not email or not new_password or not confirm_password:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # ✅ Update Django User password
        user = User.objects.get(username=email)
        user.set_password(new_password)
        user.save()

        # ✅ Update Account must_change_password flag
        try:
            account = Account.objects.get(email=email, user_role="parent")
            account.must_change_password = False
            account.password = make_password(new_password)  # keep sync
            account.save()
        except Account.DoesNotExist:
            pass

        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    



@api_view(["GET"])
@permission_classes([AllowAny])
def get_preschoolers(request):
    print("Request reached get_preschoolers:", request.method)
    preschoolers = Preschooler.objects.all()
    serializer = PreschoolerResponseSerializer(preschoolers, many=True)
    return Response(serializer.data)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_profile_photo(request):
    account = request.user.account
    if 'image' in request.FILES:
        photo, created = ProfilePhoto.objects.get_or_create(account=account)
        photo.image = request.FILES['image']
        photo.save()
        return Response({"success": True, "image_url": photo.image.url})
    return Response({"success": False, "error": "No image provided"}, status=400)