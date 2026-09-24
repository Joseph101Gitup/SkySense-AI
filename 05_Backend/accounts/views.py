import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Avg

from predictions.models import PredictionRecord
from .forms import UserRegisterForm, UserLoginForm

logger = logging.getLogger(__name__)


def register_view(request):
    """
    User registration using Django's built-in UserCreationForm with secure password hashing.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the new user in directly using Django auth
            auth_login(request, user)
            messages.success(request, f"Welcome to SKYsense AI, {user.username}! Your account has been created.")
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'page_title': 'Create Researcher Account',
    })


def login_view(request):
    """
    User login using Django's built-in AuthenticationForm with password hash verification.
    Redirects to dashboard after successful authentication.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            
            # Safe redirect to next or dashboard
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'page_title': 'Researcher Sign In',
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    """
    User logout using Django's built-in auth_logout.
    """
    if request.user.is_authenticated:
        username = request.user.username
        auth_logout(request)
        messages.info(request, f"You have been signed out, {username}.")
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
def profile_view(request):
    """
    User Profile view displaying account metadata, role privileges,
    and personalized prediction activity statistics.
    Admin users can see system-wide summary.
    """
    user = request.user
    is_admin = user.is_staff or user.is_superuser

    if is_admin:
        predictions_qs = PredictionRecord.objects.all()
        user_pred_qs = PredictionRecord.objects.filter(user=user)
        total_system_predictions = predictions_qs.count()
        total_user_predictions = user_pred_qs.count()
        recent_activity = user_pred_qs.order_by('-created_at')[:8]
        avg_confidence = user_pred_qs.aggregate(avg=Avg('confidence'))['avg']
    else:
        user_pred_qs = PredictionRecord.objects.filter(user=user)
        total_system_predictions = None
        total_user_predictions = user_pred_qs.count()
        recent_activity = user_pred_qs.order_by('-created_at')[:8]
        avg_confidence = user_pred_qs.aggregate(avg=Avg('confidence'))['avg']

    avg_conf_pct = round(avg_confidence * 100, 1) if avg_confidence is not None else 0.0

    return render(request, 'accounts/profile.html', {
        'page_title': f'Researcher Profile - {user.username}',
        'user_obj': user,
        'is_admin': is_admin,
        'total_predictions': total_user_predictions,
        'total_system_predictions': total_system_predictions,
        'avg_conf_pct': avg_conf_pct,
        'recent_activity': recent_activity,
    })
