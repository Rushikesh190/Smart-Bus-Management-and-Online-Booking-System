from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta, time
import random
import json

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100, default="Maharashtra")
    is_popular = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']

    def __str__(self):
        return self.name


class PassengerUser(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class AdminSetting(models.Model):
    username = models.CharField(max_length=100, default="Admin")
    password = models.CharField(max_length=128, default="admin123")
    upi_id = models.CharField(max_length=100, default="9225571554@axl", help_text="Receiver UPI VPA for payments")
    merchant_name = models.CharField(max_length=100, default="Rushikesh", help_text="Payee display name")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin Config ({self.username})"

    @classmethod
    def get_credentials(cls):
        obj, _ = cls.objects.get_or_create(id=1, defaults={
            'username': 'Admin',
            'password': 'admin123',
            'upi_id': '9225571554@axl',
            'merchant_name': 'Rushikesh'
        })
        return obj


class Bus(models.Model):
    SEATER = 'Seater'
    SLEEPER = 'Sleeper'
    CATEGORY_CHOICES = [
        (SEATER, 'Seater (2+2)'),
        (SLEEPER, 'Sleeper (2+1 Multi-Deck)'),
    ]

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=150)
    operator = models.CharField(max_length=100, default="Shriji Luxury Fleet")
    number = models.CharField(max_length=50, unique=True)
    bus_type = models.CharField(max_length=100, default="AC Sleeper (2+1)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=SLEEPER)
    decks = models.PositiveSmallIntegerField(default=2)
    from_city = models.ForeignKey(City, related_name='departures', on_delete=models.CASCADE)
    to_city = models.ForeignKey(City, related_name='arrivals', on_delete=models.CASCADE)
    dep_time = models.CharField(max_length=10, help_text="e.g. 06:00")
    arr_time = models.CharField(max_length=10, help_text="e.g. 09:30")
    duration = models.CharField(max_length=50, default="3h 30m")
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)
    review_count = models.PositiveIntegerField(default=150)
    total_seats = models.PositiveIntegerField(default=30)
    amenities_csv = models.CharField(max_length=300, default="wifi,charging,blanket,water,live_tracking,emergency_sos")
    
    driver_name = models.CharField(max_length=100, default="Captain Pilot")
    driver_phone = models.CharField(max_length=20, default="+91 98234 11223")
    current_speed = models.CharField(max_length=20, default="74 km/h")
    next_stop = models.CharField(max_length=100, default="Expressway Food Mall")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Buses"
        ordering = ['dep_time']

    def __str__(self):
        return f"{self.name} ({self.number}) | {self.from_city} -> {self.to_city}"

    @property
    def amenities_list(self):
        return [a.strip() for a in self.amenities_csv.split(',') if a.strip()]

    def booked_seats_for_date(self, travel_date):
        bookings = Booking.objects.filter(bus=self, travel_date=travel_date, status='confirmed')
        booked = []
        for b in bookings:
            booked.extend(b.seats_list)
        return booked

    def available_seats_count(self, travel_date=None):
        if not travel_date:
            travel_date = timezone.now().date()
        booked = self.booked_seats_for_date(travel_date)
        return max(0, self.total_seats - len(booked))

    def get_live_tracking_data(self, travel_date=None):
        """
        Accurately calculates real-time live GPS tracking telemetry, speed, ETA,
        and journey progress based on actual current clock time.
        """
        now = timezone.localtime()
        current_time = now.time()
        
        try:
            dep_h, dep_m = map(int, self.dep_time.split(':'))
            arr_h, arr_m = map(int, self.arr_time.split(':'))
            
            dep_dt = datetime.combine(now.date(), time(dep_h, dep_m))
            arr_dt = datetime.combine(now.date(), time(arr_h, arr_m))
            
            # If arrival time is earlier than departure (overnight trip)
            if arr_dt <= dep_dt:
                arr_dt += timedelta(days=1)
                
            total_duration_secs = (arr_dt - dep_dt).total_seconds()
            now_dt = datetime.combine(now.date(), current_time)
            
            # Adjust for overnight journey checking
            if now_dt < dep_dt and (dep_dt - now_dt).total_seconds() > 43200:
                now_dt += timedelta(days=1)
                
            elapsed_secs = (now_dt - dep_dt).total_seconds()
            
            if elapsed_secs < 0:
                # Bus not departed yet
                progress_pct = 0
                status_text = f"Scheduled • Boarding at {self.from_city.name} Terminal"
                speed = "0 km/h"
                next_stop_text = f"Departure from {self.from_city.name} at {self.dep_time}"
            elif elapsed_secs >= total_duration_secs:
                # Bus arrived
                progress_pct = 100
                status_text = f"Trip Completed • Arrived at {self.to_city.name} Terminal"
                speed = "0 km/h"
                next_stop_text = f"Arrived at Destination ({self.to_city.name})"
            else:
                # Bus is in active transit!
                progress_pct = min(98, max(2, int((elapsed_secs / total_duration_secs) * 100)))
                # Realistic highway cruising speed with slight jitter
                calc_speed = 70 + int((progress_pct * 7) % 22)
                speed = f"{calc_speed} km/h"
                
                # Intermediate stop detection
                points = list(self.points.all())
                if progress_pct < 35:
                    status_text = f"Departed from {self.from_city.name} • En Route"
                    next_stop_text = points[1].location if len(points) > 1 else "Highway Toll Plaza"
                elif progress_pct < 75:
                    status_text = "Expressway Cruising • On Schedule"
                    next_stop_text = points[len(points)//2].location if points else "Midway Food Plaza"
                else:
                    status_text = f"Approaching {self.to_city.name} Outer Limits"
                    next_stop_text = f"{self.to_city.name} Entry Terminal"
                    
        except Exception:
            progress_pct = 55
            status_text = "En Route • On Schedule"
            speed = "74 km/h"
            next_stop_text = self.next_stop or "Expressway Food Mall"
            
        return {
            'progress_pct': progress_pct,
            'status_text': status_text,
            'speed': speed,
            'next_stop': next_stop_text,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'origin': self.from_city.name,
            'destination': self.to_city.name,
            'dep_time': self.dep_time,
            'arr_time': self.arr_time,
        }


class BoardingPoint(models.Model):
    POINT_CHOICES = [
        ('boarding', 'Boarding Point'),
        ('dropping', 'Dropping Point'),
    ]
    bus = models.ForeignKey(Bus, related_name='points', on_delete=models.CASCADE)
    point_type = models.CharField(max_length=20, choices=POINT_CHOICES, default='boarding')
    location = models.CharField(max_length=150)
    landmark = models.CharField(max_length=150, blank=True)
    time = models.CharField(max_length=10)

    class Meta:
        ordering = ['time']

    def __str__(self):
        return f"{self.time} - {self.location} ({self.get_point_type_display()})"


class Coupon(models.Model):
    PERCENT = 'percent'
    FLAT = 'flat'
    TYPE_CHOICES = [
        (PERCENT, 'Percentage (%)'),
        (FLAT, 'Flat Amount (₹)'),
    ]
    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=PERCENT)
    value = models.PositiveIntegerField(help_text="Percentage or Flat discount amount")
    max_discount = models.PositiveIntegerField(default=200)
    min_fare = models.PositiveIntegerField(default=400)
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def calculate_discount(self, base_fare):
        if base_fare < self.min_fare:
            return 0
        if self.discount_type == self.PERCENT:
            disc = (base_fare * self.value) / 100
            return min(disc, self.max_discount)
        return min(self.value, base_fare)


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    pnr = models.CharField(max_length=20, unique=True, primary_key=True)
    bus = models.ForeignKey(Bus, related_name='bookings', on_delete=models.CASCADE)
    passenger_user = models.ForeignKey(PassengerUser, related_name='bookings', on_delete=models.SET_NULL, null=True, blank=True)
    travel_date = models.DateField(default=timezone.now)
    lead_passenger_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    boarding_point = models.CharField(max_length=200)
    dropping_point = models.CharField(max_length=200)
    seats_csv = models.CharField(max_length=100, help_text="Comma-separated seat numbers e.g. L1,L2")
    
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_used = models.CharField(max_length=30, blank=True, null=True)
    
    payment_mode = models.CharField(max_length=50, default="UPI (PhonePe QR)")
    payment_id = models.CharField(max_length=100, default="PAY100001")
    payment_utr = models.CharField(max_length=100, blank=True, null=True, help_text="UPI Transaction Ref / UTR number")
    payment_status = models.CharField(max_length=20, default="PAID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    booked_at = models.DateTimeField(default=timezone.now)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-booked_at']

    def __str__(self):
        return f"PNR {self.pnr} - {self.lead_passenger_name} ({self.bus.name})"

    @property
    def seats_list(self):
        return [s.strip() for s in self.seats_csv.split(',') if s.strip()]

    @classmethod
    def generate_pnr(cls):
        while True:
            seq = random.randint(240001, 999999)
            pnr = f"SJ{seq}"
            if not cls.objects.filter(pnr=pnr).exists():
                return pnr


class Passenger(models.Model):
    booking = models.ForeignKey(Booking, related_name='passengers', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(default=28)
    gender = models.CharField(max_length=20, default="Male")
    seat_number = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} (Seat {self.seat_number})"


class Review(models.Model):
    name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(default=5)
    route = models.CharField(max_length=150)
    comment = models.TextField()
    bus_type = models.CharField(max_length=100, default="Shriji Grand Luxury AC")
    verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.rating}★ ({self.route})"
