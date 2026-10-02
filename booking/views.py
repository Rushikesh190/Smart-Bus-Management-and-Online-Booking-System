import csv
import json
import io
import base64
import urllib.parse
from datetime import datetime, date
import qrcode
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import City, Bus, BoardingPoint, Coupon, Booking, Passenger, Review, PassengerUser, AdminSetting


def generate_upi_payment_qr(upi_id, payee_name, amount, transaction_note="Bus Ticket Payment"):
    """
    Generates standard UPI deep link and scannable base64 PNG QR Code image.
    When scanned by PhonePe / Google Pay / Paytm / BHIM, the exact ticket price (amount)
    will automatically appear in the user's UPI app.
    """
    params = {
        'pa': upi_id,
        'pn': payee_name,
        'am': f"{float(amount):.2f}",
        'cu': 'INR',
        'tn': transaction_note,
    }
    upi_link = f"upi://pay?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A192F", back_color="#FFFFFF")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    qr_data_uri = f"data:image/png;base64,{qr_base64}"
    
    return upi_link, qr_data_uri


def generate_ticket_qr(qr_text):
    """
    Generates scannable base64 PNG QR Code image for ticket verification.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A192F", back_color="#FFFFFF")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{qr_base64}"

def home_view(request):
    cities = City.objects.all()
    popular_cities = City.objects.filter(is_popular=True)[:8]
    featured_buses = Bus.objects.filter(is_active=True)[:6]
    coupons = Coupon.objects.filter(is_active=True)
    reviews = Review.objects.all()[:4]
    
    total_buses = Bus.objects.filter(is_active=True).count()
    total_bookings = Booking.objects.count()
    today_str = timezone.now().date().isoformat()

    context = {
        'cities': cities,
        'popular_cities': popular_cities,
        'featured_buses': featured_buses,
        'coupons': coupons,
        'reviews': reviews,
        'total_buses': total_buses,
        'total_bookings': total_bookings,
        'today_str': today_str,
    }
    return render(request, 'booking/home.html', context)


def search_buses_view(request):
    from_city_name = request.GET.get('from_city', '').strip()
    to_city_name = request.GET.get('to_city', '').strip()
    travel_date_str = request.GET.get('travel_date', '').strip()
    category = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort_by', 'recommended')
    time_slot = request.GET.get('time_slot', '')
    max_fare = request.GET.get('max_fare', '')

    try:
        travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date() if travel_date_str else timezone.now().date()
    except ValueError:
        travel_date = timezone.now().date()

    buses_qs = Bus.objects.filter(is_active=True)

    if from_city_name and to_city_name:
        buses_qs = buses_qs.filter(
            from_city__name__icontains=from_city_name,
            to_city__name__icontains=to_city_name
        )
    elif from_city_name:
        buses_qs = buses_qs.filter(from_city__name__icontains=from_city_name)
    elif to_city_name:
        buses_qs = buses_qs.filter(to_city__name__icontains=to_city_name)

    if category and category != 'all':
        buses_qs = buses_qs.filter(category=category)

    if max_fare:
        try:
            buses_qs = buses_qs.filter(fare__lte=float(max_fare))
        except ValueError:
            pass

    # Time slot filtering
    buses_list = list(buses_qs)
    if time_slot:
        filtered = []
        for b in buses_list:
            try:
                hour = int(b.dep_time.split(':')[0])
                if time_slot == 'morning' and (6 <= hour < 12):
                    filtered.append(b)
                elif time_slot == 'afternoon' and (12 <= hour < 18):
                    filtered.append(b)
                elif time_slot == 'evening' and (18 <= hour < 23):
                    filtered.append(b)
                elif time_slot == 'night' and (hour >= 23 or hour < 6):
                    filtered.append(b)
            except (ValueError, IndexError):
                filtered.append(b)
        buses_list = filtered

    # Sorting
    if sort_by == 'cheapest':
        buses_list.sort(key=lambda x: x.fare)
    elif sort_by == 'earliest':
        buses_list.sort(key=lambda x: x.dep_time)
    elif sort_by == 'rating':
        buses_list.sort(key=lambda x: x.rating, reverse=True)

    # Attach dynamic seats available for the date
    buses_with_seats = []
    for b in buses_list:
        buses_with_seats.append({
            'bus': b,
            'available_seats': b.available_seats_count(travel_date),
            'booked_seats': b.booked_seats_for_date(travel_date),
        })

    cities = City.objects.all()

    context = {
        'buses_with_seats': buses_with_seats,
        'from_city': from_city_name,
        'to_city': to_city_name,
        'travel_date': travel_date,
        'travel_date_str': travel_date.isoformat(),
        'category': category,
        'sort_by': sort_by,
        'time_slot': time_slot,
        'max_fare': max_fare,
        'cities': cities,
        'total_found': len(buses_with_seats),
    }
    return render(request, 'booking/search_results.html', context)


def seat_selection_view(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id, is_active=True)
    travel_date_str = request.GET.get('date', timezone.now().date().isoformat())
    
    try:
        travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
    except ValueError:
        travel_date = timezone.now().date()

    booked_seats = bus.booked_seats_for_date(travel_date)
    boarding_points = bus.points.filter(point_type='boarding')
    dropping_points = bus.points.filter(point_type='dropping')
    coupons = Coupon.objects.filter(is_active=True)

    # Check if passenger is logged in
    passenger_id = request.session.get('passenger_user_id')
    logged_passenger = None
    if passenger_id:
        logged_passenger = PassengerUser.objects.filter(id=passenger_id).first()

    context = {
        'bus': bus,
        'travel_date': travel_date,
        'travel_date_str': travel_date.isoformat(),
        'booked_seats': booked_seats,
        'booked_seats_json': json.dumps(booked_seats),
        'boarding_points': boarding_points,
        'dropping_points': dropping_points,
        'coupons': coupons,
        'is_sleeper': bus.category == Bus.SLEEPER or bus.decks == 2,
        'logged_passenger': logged_passenger,
    }
    return render(request, 'booking/seat_selection.html', context)


# ==============================================================================
# PASSENGER AUTHENTICATION (LOGIN & REGISTRATION)
# ==============================================================================
def passenger_login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('home')
    
    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()
        password = request.POST.get('password', '').strip()

        # Find passenger by phone or email
        passenger = PassengerUser.objects.filter(Q(phone=login_id) | Q(email=login_id)).first()
        if passenger and passenger.password == password:
            request.session['passenger_user_id'] = passenger.id
            request.session['passenger_user_name'] = passenger.name
            messages.success(request, f"Welcome back, {passenger.name}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid mobile number/email or password. Please try again or create an account.")

    return render(request, 'booking/passenger_login.html', {'next_url': next_url})


def passenger_register_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('home')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not name or not phone or not password:
            messages.error(request, "Full Name, Mobile Number, and Password are required.")
            return render(request, 'booking/passenger_register.html', {'next_url': next_url})

        if PassengerUser.objects.filter(phone=phone).exists():
            messages.error(request, "An account with this mobile number already exists. Please log in.")
            return redirect(f"{reverse('passenger_login')}?next={next_url}")

        passenger = PassengerUser.objects.create(
            name=name,
            phone=phone,
            email=email if email else None,
            password=password
        )
        request.session['passenger_user_id'] = passenger.id
        request.session['passenger_user_name'] = passenger.name
        messages.success(request, f"Account created successfully! Welcome to Shriji Travels, {passenger.name}.")
        return redirect(next_url)

    return render(request, 'booking/passenger_register.html', {'next_url': next_url})


def passenger_logout_view(request):
    request.session.pop('passenger_user_id', None)
    request.session.pop('passenger_user_name', None)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ==============================================================================
# CHECKOUT & PAYMENT VERIFICATION
# ==============================================================================
def checkout_view(request):
    if request.method != 'POST':
        return redirect('home')

    # Ensure passenger login before checkout
    passenger_id = request.session.get('passenger_user_id')
    if not passenger_id:
        bus_id = request.POST.get('bus_id')
        travel_date_str = request.POST.get('travel_date')
        messages.info(request, "Please log in or create a passenger account before proceeding to secure payment.")
        return redirect(f"{reverse('passenger_login')}?next={reverse('seat_selection', kwargs={'bus_id': bus_id})}?date={travel_date_str}")

    logged_passenger = PassengerUser.objects.filter(id=passenger_id).first()

    bus_id = request.POST.get('bus_id')
    bus = get_object_or_404(Bus, id=bus_id)
    
    travel_date_str = request.POST.get('travel_date')
    selected_seats_str = request.POST.get('selected_seats', '')
    lead_name = request.POST.get('lead_name', '').strip() or (logged_passenger.name if logged_passenger else '')
    phone = request.POST.get('phone', '').strip() or (logged_passenger.phone if logged_passenger else '')
    email = request.POST.get('email', '').strip() or (logged_passenger.email if logged_passenger and logged_passenger.email else '')
    boarding_point = request.POST.get('boarding_point', '')
    dropping_point = request.POST.get('dropping_point', '')
    coupon_code = request.POST.get('coupon_code', '').strip().upper()

    seats_list = [s.strip() for s in selected_seats_str.split(',') if s.strip()]
    if not seats_list:
        messages.error(request, "Please select at least one seat to proceed.")
        return redirect(f"{reverse('seat_selection', kwargs={'bus_id': bus.id})}?date={travel_date_str}")

    try:
        travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
    except ValueError:
        travel_date = timezone.now().date()

    already_booked = [s for s in seats_list if s in bus.booked_seats_for_date(travel_date)]
    if already_booked:
        messages.error(request, f"Seat(s) {', '.join(already_booked)} are already booked. Please pick other seats.")
        return redirect(f"{reverse('seat_selection', kwargs={'bus_id': bus.id})}?date={travel_date_str}")

    # Fare calculation
    seat_count = len(seats_list)
    base_fare = float(bus.fare) * seat_count
    discount_amount = 0.0

    if coupon_code:
        try:
            cp = Coupon.objects.get(code=coupon_code, is_active=True)
            discount_amount = float(cp.calculate_discount(base_fare))
        except Coupon.DoesNotExist:
            coupon_code = ''

    gst_amount = round((base_fare - discount_amount) * 0.05, 2)
    total_fare = max(0.0, base_fare - discount_amount + gst_amount)

    # Collect passenger data
    passengers_data = []
    for i, seat in enumerate(seats_list):
        p_name = request.POST.get(f'pass_name_{i}', lead_name if i == 0 else f'Passenger {i+1}')
        p_age = request.POST.get(f'pass_age_{i}', '28')
        p_gender = request.POST.get(f'pass_gender_{i}', 'Male')
        passengers_data.append({
            'name': p_name,
            'age': p_age,
            'gender': p_gender,
            'seat': seat
        })

    # Admin / Merchant UPI Details
    admin_creds = AdminSetting.get_credentials()
    upi_id = admin_creds.upi_id or 'shrijitravels@upi'
    merchant_name = admin_creds.merchant_name or 'Shriji Travels Fleet'
    
    # Generate dynamic UPI QR Code with exact booking ticket price
    txn_note = f"Shriji Coach {bus.number} Seats {','.join(seats_list)}"
    upi_link, upi_qr_data_uri = generate_upi_payment_qr(
        upi_id=upi_id,
        payee_name=merchant_name,
        amount=total_fare,
        transaction_note=txn_note
    )

    context = {
        'bus': bus,
        'travel_date': travel_date,
        'travel_date_str': travel_date.isoformat(),
        'seats_list': seats_list,
        'seats_csv': ','.join(seats_list),
        'lead_name': lead_name,
        'phone': phone,
        'email': email,
        'boarding_point': boarding_point,
        'dropping_point': dropping_point,
        'coupon_code': coupon_code,
        'base_fare': base_fare,
        'discount_amount': discount_amount,
        'gst_amount': gst_amount,
        'total_fare': total_fare,
        'passengers_data_json': json.dumps(passengers_data),
        'logged_passenger': logged_passenger,
        'upi_id': upi_id,
        'merchant_name': merchant_name,
        'upi_link': upi_link,
        'upi_qr_data_uri': upi_qr_data_uri,
    }
    return render(request, 'booking/payment.html', context)


@require_POST
def confirm_booking_view(request):
    bus_id = request.POST.get('bus_id')
    bus = get_object_or_404(Bus, id=bus_id)
    
    travel_date_str = request.POST.get('travel_date')
    travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
    
    seats_csv = request.POST.get('seats_csv', '')
    lead_name = request.POST.get('lead_name')
    phone = request.POST.get('phone')
    email = request.POST.get('email', '')
    boarding_point = request.POST.get('boarding_point')
    dropping_point = request.POST.get('dropping_point')
    coupon_used = request.POST.get('coupon_code', '')
    
    base_fare = float(request.POST.get('base_fare', 0))
    discount_amount = float(request.POST.get('discount_amount', 0))
    gst_amount = float(request.POST.get('gst_amount', 0))
    total_fare = float(request.POST.get('total_fare', 0))
    payment_mode = request.POST.get('payment_mode', 'UPI (PhonePe QR)')
    payment_utr = request.POST.get('payment_utr', '').strip()
    
    payment_id = f"PAY{timezone.now().strftime('%Y%m%d%H%M%S')}"

    # Associate with logged-in passenger
    passenger_user = None
    passenger_id = request.session.get('passenger_user_id')
    if passenger_id:
        passenger_user = PassengerUser.objects.filter(id=passenger_id).first()

    # Generate PNR and create booking
    pnr = Booking.generate_pnr()
    booking = Booking.objects.create(
        pnr=pnr,
        bus=bus,
        passenger_user=passenger_user,
        travel_date=travel_date,
        lead_passenger_name=lead_name,
        phone=phone,
        email=email,
        boarding_point=boarding_point,
        dropping_point=dropping_point,
        seats_csv=seats_csv,
        base_fare=base_fare,
        discount_amount=discount_amount,
        gst_amount=gst_amount,
        total_fare=total_fare,
        coupon_used=coupon_used if coupon_used else None,
        payment_mode=payment_mode,
        payment_id=payment_id,
        payment_utr=payment_utr if payment_utr else f"UPI{pnr}",
        payment_status="PAID",
        status="confirmed"
    )

    # Create Passenger records
    passengers_json = request.POST.get('passengers_data_json', '[]')
    try:
        passengers_data = json.loads(passengers_json)
        for p in passengers_data:
            Passenger.objects.create(
                booking=booking,
                name=p.get('name', lead_name),
                age=int(p.get('age', 28)),
                gender=p.get('gender', 'Male'),
                seat_number=p.get('seat', 'A1')
            )
    except Exception:
        for s in booking.seats_list:
            Passenger.objects.create(booking=booking, name=lead_name, seat_number=s)

    messages.success(request, f"🎉 Payment Successful & Booking Confirmed! Your PNR is {booking.pnr}")
    return redirect('ticket_detail', pnr=booking.pnr)


def ticket_view(request, pnr):
    booking = get_object_or_404(Booking, pnr=pnr.strip().upper())
    passengers = booking.passengers.all()
    
    barcode_val = f"{booking.pnr}-{'-'.join(booking.seats_list)}"
    qr_val = f"SHRIJI-PNR:{booking.pnr}|BUS:{booking.bus.number}|SEATS:{booking.seats_csv}|PAID:{booking.total_fare}"

    # Build reliable live tracking link that works both locally and in WhatsApp
    live_tracking_url = request.build_absolute_uri(reverse('live_tracking')) + f"?q={booking.pnr}"

    whatsapp_msg = (
        f"Namaste! Here is my Shriji Travels Digital E-Ticket.\n"
        f"PNR: {booking.pnr}\n"
        f"Route: {booking.bus.from_city.name} to {booking.bus.to_city.name}\n"
        f"Date: {booking.travel_date.strftime('%d %b %Y')}\n"
        f"Seats: {booking.seats_csv}\n"
        f"Live GPS Radar: {live_tracking_url}"
    )

    ticket_qr_data_uri = generate_ticket_qr(qr_val)

    context = {
        'booking': booking,
        'passengers': passengers,
        'barcode_val': barcode_val,
        'qr_val': qr_val,
        'ticket_qr_data_uri': ticket_qr_data_uri,
        'live_tracking_url': live_tracking_url,
        'whatsapp_msg': whatsapp_msg,
    }
    return render(request, 'booking/ticket.html', context)


# ==============================================================================
# ACCURATE REAL-TIME LIVE GPS RADAR & TELEMETRY
# ==============================================================================
def live_tracking_view(request, pnr=None):
    query = pnr or request.GET.get('q', '').strip().upper()
    tracking_bus = None
    booking = None

    if query:
        # Check PNR first
        try:
            booking = Booking.objects.get(pnr=query)
            tracking_bus = booking.bus
        except Booking.DoesNotExist:
            # Check Bus ID or plate
            tracking_bus = Bus.objects.filter(
                Q(id__iexact=query) | Q(number__icontains=query)
            ).first()

    if not tracking_bus:
        tracking_bus = Bus.objects.first()

    tracking_data = tracking_bus.get_live_tracking_data() if tracking_bus else {}

    context = {
        'query': query,
        'bus': tracking_bus,
        'booking': booking,
        'tracking_data': tracking_data,
    }
    return render(request, 'booking/live_tracking.html', context)


def my_bookings_view(request):
    phone = request.GET.get('phone', '').strip()
    pnr = request.GET.get('pnr', '').strip().upper()
    
    passenger_id = request.session.get('passenger_user_id')
    logged_passenger = None
    if passenger_id:
        logged_passenger = PassengerUser.objects.filter(id=passenger_id).first()

    bookings = []

    if pnr:
        bookings = Booking.objects.filter(pnr=pnr)
    elif phone:
        bookings = Booking.objects.filter(phone=phone)
    elif logged_passenger:
        # Auto list logged in passenger's bookings
        bookings = Booking.objects.filter(Q(passenger_user=logged_passenger) | Q(phone=logged_passenger.phone))

    context = {
        'bookings': bookings,
        'phone': phone or (logged_passenger.phone if logged_passenger else ''),
        'pnr': pnr,
        'searched': bool(phone or pnr or logged_passenger),
        'logged_passenger': logged_passenger,
    }
    return render(request, 'booking/my_bookings.html', context)


@require_POST
def cancel_booking_view(request, pnr):
    booking = get_object_or_404(Booking, pnr=pnr.strip().upper())
    
    if booking.status == 'cancelled':
        messages.warning(request, f"Booking {booking.pnr} is already cancelled.")
    else:
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.refund_amount = round(float(booking.total_fare) * 0.90, 2)
        booking.save()
        messages.success(request, f"Booking {booking.pnr} cancelled successfully. Refund of ₹{booking.refund_amount} initiated.")

    return redirect('my_bookings')


def offers_view(request):
    coupons = Coupon.objects.filter(is_active=True)
    return render(request, 'booking/offers.html', {'coupons': coupons})


def reviews_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        rating = int(request.POST.get('rating', 5))
        route = request.POST.get('route', '').strip()
        comment = request.POST.get('comment', '').strip()
        bus_type = request.POST.get('bus_type', 'Shriji Grand Luxury Coach')
        
        if name and comment:
            Review.objects.create(
                name=name, rating=rating, route=route, comment=comment, bus_type=bus_type, verified=True
            )
            messages.success(request, "Thank you! Your travel review has been published.")
            return redirect('reviews')

    reviews = Review.objects.all()
    return render(request, 'booking/reviews.html', {'reviews': reviews})


# ==============================================================================
# ADMIN OPERATIONS DASHBOARD WITH DYNAMIC CREDENTIALS & EDIT FEATURE
# ==============================================================================
def admin_dashboard_view(request):
    admin_creds = AdminSetting.get_credentials()
    is_authenticated = request.session.get('is_fleet_admin', False)

    # Admin Login Post
    if request.method == 'POST' and 'admin_login' in request.POST:
        input_user = request.POST.get('admin_username', '').strip()
        input_pass = request.POST.get('admin_password', '').strip()

        if input_user == admin_creds.username and input_pass == admin_creds.password:
            request.session['is_fleet_admin'] = True
            is_authenticated = True
            messages.success(request, f"Welcome back, {admin_creds.username}!")
        else:
            messages.error(request, "Invalid Admin Username or Password. Please try again.")

    # Admin Logout
    if request.GET.get('action') == 'logout':
        request.session['is_fleet_admin'] = False
        return redirect('admin_dashboard')

    # Edit Admin Credentials & Payment Settings Form
    if is_authenticated and request.method == 'POST' and 'edit_credentials' in request.POST:
        new_user = request.POST.get('new_admin_username', '').strip()
        new_pass = request.POST.get('new_admin_password', '').strip()
        confirm_pass = request.POST.get('confirm_admin_password', '').strip()
        new_upi_id = request.POST.get('new_upi_id', '').strip()
        new_merchant_name = request.POST.get('new_merchant_name', '').strip()

        if not new_user or not new_pass:
            messages.error(request, "Admin username and password cannot be empty.")
        elif new_pass != confirm_pass:
            messages.error(request, "New password and confirmation password do not match.")
        else:
            admin_creds.username = new_user
            admin_creds.password = new_pass
            if new_upi_id:
                admin_creds.upi_id = new_upi_id
            if new_merchant_name:
                admin_creds.merchant_name = new_merchant_name
            admin_creds.save()
            messages.success(request, "Admin credentials & UPI Receiver settings successfully updated!")
            return redirect('admin_dashboard')

    # Add New Coach Form
    if is_authenticated and request.method == 'POST' and 'add_bus' in request.POST:
        name = request.POST.get('bus_name')
        number = request.POST.get('bus_number').upper()
        bus_type = request.POST.get('bus_type')
        from_city_id = request.POST.get('from_city')
        to_city_id = request.POST.get('to_city')
        dep_time = request.POST.get('dep_time')
        arr_time = request.POST.get('arr_time')
        fare = request.POST.get('fare')
        total_seats = int(request.POST.get('total_seats', 30))

        bus_id = f"B{Bus.objects.count() + 101}"
        from_c = City.objects.get(id=from_city_id)
        to_c = City.objects.get(id=to_city_id)

        new_bus = Bus.objects.create(
            id=bus_id,
            name=name,
            number=number,
            bus_type=bus_type,
            category=Bus.SLEEPER if 'Sleeper' in bus_type else Bus.SEATER,
            decks=2 if 'Sleeper' in bus_type else 1,
            from_city=from_c,
            to_city=to_c,
            dep_time=dep_time,
            arr_time=arr_time,
            duration="4h 00m",
            fare=fare,
            total_seats=total_seats,
            is_active=True
        )
        BoardingPoint.objects.create(bus=new_bus, point_type='boarding', time=dep_time, location=f"{from_c.name} Central Terminal")
        BoardingPoint.objects.create(bus=new_bus, point_type='dropping', time=arr_time, location=f"{to_c.name} Central Terminal")

        messages.success(request, f"New coach {new_bus.name} ({new_bus.number}) deployed to live network!")
        return redirect('admin_dashboard')

    # Admin KPI Metrics
    total_buses = Bus.objects.filter(is_active=True).count()
    all_bookings = Booking.objects.all()
    confirmed_bookings = all_bookings.filter(status='confirmed')
    total_revenue = sum(b.total_fare for b in confirmed_bookings)
    seats_sold = sum(len(b.seats_list) for b in confirmed_bookings)

    buses = Bus.objects.all()
    cities = City.objects.all()

    context = {
        'is_authenticated': is_authenticated,
        'admin_creds': admin_creds,
        'total_buses': total_buses,
        'total_bookings': all_bookings.count(),
        'confirmed_bookings_count': confirmed_bookings.count(),
        'total_revenue': total_revenue,
        'seats_sold': seats_sold,
        'buses': buses,
        'bookings': all_bookings[:30],
        'cities': cities,
    }
    return render(request, 'booking/admin_dashboard.html', context)


def export_bookings_csv(request):
    if not request.session.get('is_fleet_admin', False):
        return redirect('admin_dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Shriji_Bookings_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['PNR', 'Passenger Name', 'Phone', 'Route', 'Date', 'Seats', 'Fare (INR)', 'Payment Mode', 'Payment UTR', 'Status'])

    for b in Booking.objects.all():
        writer.writerow([
            b.pnr,
            b.lead_passenger_name,
            b.phone,
            f"{b.bus.from_city.name} -> {b.bus.to_city.name}",
            b.travel_date.isoformat(),
            b.seats_csv,
            b.total_fare,
            b.payment_mode,
            b.payment_utr or 'N/A',
            b.status
        ])

    return response


def api_validate_coupon(request):
    code = request.GET.get('code', '').strip().upper()
    fare = float(request.GET.get('fare', 0))

    try:
        cp = Coupon.objects.get(code=code, is_active=True)
        if fare < cp.min_fare:
            return JsonResponse({'valid': False, 'message': f'Minimum fare of ₹{cp.min_fare} required for this coupon.'})
        discount = cp.calculate_discount(fare)
        return JsonResponse({
            'valid': True,
            'code': cp.code,
            'discount': discount,
            'message': f'✓ {cp.description} applied! Saved ₹{int(discount)}'
        })
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid or expired promo code.'})
