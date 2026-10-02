from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import City, Bus, PassengerUser, AdminSetting, Booking
from .views import generate_upi_payment_qr, generate_ticket_qr
import urllib.parse

class UPIPaymentQRTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.city1 = City.objects.create(name="Mumbai", state="Maharashtra")
        self.city2 = City.objects.create(name="Pune", state="Maharashtra")
        self.bus = Bus.objects.create(
            id="B101",
            name="Shriji Express",
            number="MH12AB1234",
            bus_type="AC Sleeper (2+1)",
            from_city=self.city1,
            to_city=self.city2,
            dep_time="06:00",
            arr_time="09:30",
            fare=850.00,
            total_seats=30
        )
        self.passenger = PassengerUser.objects.create(
            name="Rahul Sharma",
            phone="9876543210",
            password="pass"
        )
        self.admin_setting = AdminSetting.get_credentials()
        self.admin_setting.upi_id = "testshriji@upi"
        self.admin_setting.merchant_name = "Shriji Travels Fleet"
        self.admin_setting.save()

    def test_generate_upi_payment_qr_uri_and_amount(self):
        upi_link, qr_data_uri = generate_upi_payment_qr(
            upi_id="testshriji@upi",
            payee_name="Shriji Travels Fleet",
            amount=892.50,
            transaction_note="Bus Booking Seats L1"
        )
        self.assertTrue(upi_link.startswith("upi://pay?"))
        self.assertIn("am=892.50", upi_link)
        self.assertIn("pa=testshriji%40upi", upi_link)
        self.assertIn("cu=INR", upi_link)
        self.assertTrue(qr_data_uri.startswith("data:image/png;base64,"))

    def test_checkout_page_renders_dynamic_upi_qr(self):
        # Set session
        session = self.client.session
        session['passenger_user_id'] = self.passenger.id
        session.save()

        response = self.client.post(reverse('checkout'), {
            'bus_id': self.bus.id,
            'travel_date': timezone.now().date().isoformat(),
            'selected_seats': 'L1,L2',
            'lead_name': 'Rahul Sharma',
            'phone': '9876543210',
            'email': 'rahul@example.com',
            'boarding_point': 'Mumbai Central',
            'dropping_point': 'Pune Swargate',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('upi_qr_data_uri', response.context)
        self.assertIn('upi_link', response.context)
        self.assertIn('total_fare', response.context)
        
        # 2 seats * 850 = 1700, GST 5% = 85, total = 1785.00
        total_fare = response.context['total_fare']
        self.assertEqual(total_fare, 1785.00)
        self.assertIn(f"am=1785.00", response.context['upi_link'])
        self.assertContains(response, "1785.00 Pre-Encoded")
        self.assertContains(response, "testshriji@upi")
