from django.contrib import admin
from .models import City, Bus, BoardingPoint, Coupon, Booking, Passenger, Review

class BoardingPointInline(admin.TabularInline):
    model = BoardingPoint
    extra = 1

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'number', 'bus_type', 'from_city', 'to_city', 'dep_time', 'arr_time', 'fare', 'is_active')
    list_filter = ('category', 'from_city', 'to_city', 'is_active')
    search_fields = ('name', 'number', 'from_city__name', 'to_city__name')
    inlines = [BoardingPointInline]

class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 0
    readonly_fields = ('name', 'age', 'gender', 'seat_number')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('pnr', 'lead_passenger_name', 'phone', 'bus', 'travel_date', 'seats_csv', 'total_fare', 'payment_mode', 'status', 'booked_at')
    list_filter = ('status', 'travel_date', 'payment_mode', 'bus')
    search_fields = ('pnr', 'lead_passenger_name', 'phone', 'email', 'bus__name')
    inlines = [PassengerInline]

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'max_discount', 'min_fare', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'is_popular')
    list_filter = ('state', 'is_popular')
    search_fields = ('name', 'state')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'route', 'bus_type', 'verified', 'created_at')
    list_filter = ('rating', 'verified')
    search_fields = ('name', 'route', 'comment')
