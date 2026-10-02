from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('search/', views.search_buses_view, name='search_buses'),
    path('seats/<str:bus_id>/', views.seat_selection_view, name='seat_selection'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirm-booking/', views.confirm_booking_view, name='confirm_booking'),
    path('ticket/<str:pnr>/', views.ticket_view, name='ticket_detail'),
    
    # Live Tracking URL with support for /live-tracking/ and /track/<pnr>/ (for direct WhatsApp link clicks)
    path('live-tracking/', views.live_tracking_view, name='live_tracking'),
    path('track/<str:pnr>/', views.live_tracking_view, name='track_pnr'),
    
    # Passenger Login / Register / Logout
    path('passenger/login/', views.passenger_login_view, name='passenger_login'),
    path('passenger/register/', views.passenger_register_view, name='passenger_register'),
    path('passenger/logout/', views.passenger_logout_view, name='passenger_logout'),

    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('cancel-booking/<str:pnr>/', views.cancel_booking_view, name='cancel_booking'),
    path('offers/', views.offers_view, name='offers'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/export-csv/', views.export_bookings_csv, name='export_bookings_csv'),
    path('api/validate-coupon/', views.api_validate_coupon, name='api_validate_coupon'),
]
