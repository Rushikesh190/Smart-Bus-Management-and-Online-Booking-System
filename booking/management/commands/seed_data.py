from django.core.management.base import BaseCommand
from booking.models import City, Bus, BoardingPoint, Coupon, Booking, Passenger, Review
from django.utils import timezone
from datetime import date

class Command(BaseCommand):
    help = 'Seeds initial fleet, cities, coupons, and reviews into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding Shriji Travels database...")

        # 1. Cities
        cities_data = [
            ("Nashik", "Maharashtra", True),
            ("Mumbai", "Maharashtra", True),
            ("Pune", "Maharashtra", True),
            ("Nagpur", "Maharashtra", True),
            ("Aurangabad (Chhatrapati Sambhaji Nagar)", "Maharashtra", True),
            ("Shirdi", "Maharashtra", True),
            ("Kolhapur", "Maharashtra", True),
            ("Indore", "Madhya Pradesh", True),
            ("Surat", "Gujarat", True),
            ("Goa (Panaji)", "Goa", True),
            ("Ahmedabad", "Gujarat", True),
            ("Vadodara", "Gujarat", True),
        ]
        city_objs = {}
        for name, state, pop in cities_data:
            c, _ = City.objects.get_or_create(name=name, defaults={'state': state, 'is_popular': pop})
            city_objs[name] = c

        # 2. Coupons
        coupons_data = [
            ("SHRIJI20", "percent", 20, 200, 400, "20% OFF up to ₹200 on all luxury sleeper coaches"),
            ("FIRST50", "flat", 50, 50, 300, "Flat ₹50 OFF on your first booking"),
            ("FESTIVE100", "flat", 100, 100, 600, "Flat ₹100 OFF festive special discount"),
            ("SUPERBUS", "percent", 15, 150, 500, "15% OFF up to ₹150 for frequent travelers"),
            ("ROYAL120", "flat", 120, 120, 700, "Flat ₹120 OFF on Shriji Royal Multi-Axle routes"),
        ]
        for code, dtype, val, maxd, minf, desc in coupons_data:
            Coupon.objects.get_or_create(
                code=code,
                defaults={'discount_type': dtype, 'value': val, 'max_discount': maxd, 'min_fare': minf, 'description': desc}
            )

        # 3. Buses
        buses_data = [
            {
                "id": "B101",
                "name": "Shriji Superfast Grand Express",
                "operator": "Shriji Luxury Fleet",
                "number": "MH12 AB 4521",
                "bus_type": "AC Seater (2+2)",
                "category": "Seater",
                "decks": 1,
                "from_city": city_objs["Nashik"],
                "to_city": city_objs["Mumbai"],
                "dep_time": "06:00",
                "arr_time": "09:30",
                "duration": "3h 30m",
                "fare": 550.00,
                "rating": 4.9,
                "review_count": 384,
                "total_seats": 36,
                "amenities_csv": "wifi,charging,water,live_tracking,emergency_sos,reading_light,blanket",
                "driver_name": "Santosh Deshmukh",
                "driver_phone": "+91 98234 11223",
                "current_speed": "74 km/h",
                "next_stop": "Igatpuri Toll Plaza",
                "boarding_points": [
                    ("05:45", "Dwarka Circle, Shriji Lounge", "Opp. Hotel Dwarka"),
                    ("06:00", "Nashik Road Bus Station", "Platform 4 Exit"),
                    ("06:20", "Pathardi Phata", "Flyover Junction"),
                ],
                "dropping_points": [
                    ("08:45", "Thane - Teen Hath Naka", "Near Eternity Mall"),
                    ("09:10", "Dadar East - Shriji Terminal", "Near Swami Narayan Temple"),
                    ("09:30", "Borivali East", "National Park Bridge"),
                ]
            },
            {
                "id": "B102",
                "name": "Shriji Maharaja Multi-Deck AC Sleeper",
                "operator": "Shriji Royal Class",
                "number": "MH15 CD 7788",
                "bus_type": "AC Sleeper (2+1)",
                "category": "Sleeper",
                "decks": 2,
                "from_city": city_objs["Nashik"],
                "to_city": city_objs["Pune"],
                "dep_time": "22:30",
                "arr_time": "04:00",
                "duration": "5h 30m",
                "fare": 680.00,
                "rating": 4.8,
                "review_count": 290,
                "total_seats": 30,
                "amenities_csv": "wifi,charging,blanket,pillow,water,live_tracking,movie_screen",
                "driver_name": "Gajanan Patil",
                "driver_phone": "+91 94222 88765",
                "current_speed": "68 km/h",
                "next_stop": "Sangamner Bypass",
                "boarding_points": [
                    ("22:15", "Dwarka Circle Lounge", "Shriji Corporate Office"),
                    ("22:30", "Nashik Road Station", "Gate 1"),
                ],
                "dropping_points": [
                    ("03:30", "Bhosari - Landewadi", "Flyover Pillar 42"),
                    ("04:00", "Swargate Bus Stand", "Laxmi Narayan Cinema"),
                ]
            },
            {
                "id": "B103",
                "name": "Shriji Express Grand Class",
                "operator": "Shriji Standard Express",
                "number": "MH20 XY 1122",
                "bus_type": "Non-AC Seater (2+2)",
                "category": "Seater",
                "decks": 1,
                "from_city": city_objs["Nashik"],
                "to_city": city_objs["Aurangabad (Chhatrapati Sambhaji Nagar)"],
                "dep_time": "07:15",
                "arr_time": "11:00",
                "duration": "3h 45m",
                "fare": 340.00,
                "rating": 4.6,
                "review_count": 175,
                "total_seats": 40,
                "amenities_csv": "charging,water,emergency_sos,live_tracking",
                "driver_name": "Rameshwar Jadhav",
                "driver_phone": "+91 98811 44332",
                "current_speed": "65 km/h",
                "next_stop": "Waluj MIDC",
                "boarding_points": [
                    ("07:00", "CBS Central Bus Station", "Platform 2"),
                ],
                "dropping_points": [
                    ("11:00", "CIDCO Bus Stand", "Opp. City Mall"),
                ]
            },
            {
                "id": "B104",
                "name": "Shriji Star Multi-Axle AC Sleeper",
                "operator": "Shriji Gold Line",
                "number": "MH31 GH 9090",
                "bus_type": "AC Sleeper (2+1)",
                "category": "Sleeper",
                "decks": 2,
                "from_city": city_objs["Pune"],
                "to_city": city_objs["Nagpur"],
                "dep_time": "19:30",
                "arr_time": "08:00",
                "duration": "12h 30m",
                "fare": 1150.00,
                "rating": 4.9,
                "review_count": 520,
                "total_seats": 36,
                "amenities_csv": "wifi,charging,blanket,pillow,water,live_tracking,cctv,emergency_sos",
                "driver_name": "Mahesh Bhonsle",
                "driver_phone": "+91 97654 33211",
                "current_speed": "95 km/h",
                "next_stop": "Samruddhi Expressway Food Plaza",
                "boarding_points": [
                    ("19:00", "Wakad - Hinjawadi Flyover", "Ginger Hotel"),
                    ("19:30", "Viman Nagar", "Four Points Sheraton"),
                ],
                "dropping_points": [
                    ("08:00", "Ganeshpeth Bus Stand", "Shriji Office 3"),
                ]
            },
            {
                "id": "B105",
                "name": "Shriji Royal Multi-Axle Luxury Sleeper",
                "operator": "Shriji Royal Class",
                "number": "MH04 JK 5566",
                "bus_type": "AC Sleeper (2+1)",
                "category": "Sleeper",
                "decks": 2,
                "from_city": city_objs["Mumbai"],
                "to_city": city_objs["Goa (Panaji)"],
                "dep_time": "20:00",
                "arr_time": "07:30",
                "duration": "11h 30m",
                "fare": 1250.00,
                "rating": 4.9,
                "review_count": 640,
                "total_seats": 30,
                "amenities_csv": "wifi,charging,blanket,pillow,water,live_tracking,sanitized_restroom_stops",
                "driver_name": "Anthony D'Souza",
                "driver_phone": "+91 98221 00987",
                "current_speed": "70 km/h",
                "next_stop": "Sawantwadi Bypass",
                "boarding_points": [
                    ("19:30", "Borivali East - National Park", "Opp. Omkareshwar Temple"),
                    ("20:00", "Sion Circle - Shriji Office", "Near Chhatrapati Shivaji Statue"),
                ],
                "dropping_points": [
                    ("07:30", "Panaji KTC Bus Stand", "Platform 1"),
                ]
            },
            {
                "id": "B106",
                "name": "Shriji Sai Darshan Electric Luxury AC",
                "operator": "Shriji Green Fleet",
                "number": "MH15 LM 3344",
                "bus_type": "AC Seater (2+2)",
                "category": "Seater",
                "decks": 1,
                "from_city": city_objs["Shirdi"],
                "to_city": city_objs["Pune"],
                "dep_time": "14:00",
                "arr_time": "18:30",
                "duration": "4h 30m",
                "fare": 380.00,
                "rating": 4.8,
                "review_count": 210,
                "total_seats": 40,
                "amenities_csv": "wifi,charging,water,live_tracking,emergency_sos",
                "driver_name": "Kishore Sonawane",
                "driver_phone": "+91 93700 44556",
                "current_speed": "75 km/h",
                "next_stop": "Ahmednagar Bypass",
                "boarding_points": [
                    ("13:45", "Shirdi Temple Gate 2", "Shriji Pilgrimage Desk"),
                ],
                "dropping_points": [
                    ("18:30", "Shivajinagar Station", "Near Sancheti Hospital"),
                ]
            },
            {
                "id": "B107",
                "name": "Shriji Diamond BharatBenz Luxury Coach",
                "operator": "Shriji Diamond Fleet",
                "number": "GJ05 NP 2211",
                "bus_type": "AC Sleeper (2+1)",
                "category": "Sleeper",
                "decks": 2,
                "from_city": city_objs["Surat"],
                "to_city": city_objs["Mumbai"],
                "dep_time": "07:30",
                "arr_time": "13:30",
                "duration": "6h 00m",
                "fare": 650.00,
                "rating": 4.7,
                "review_count": 310,
                "total_seats": 30,
                "amenities_csv": "wifi,charging,blanket,water,live_tracking",
                "driver_name": "Pravin Patel",
                "driver_phone": "+91 99090 12345",
                "current_speed": "80 km/h",
                "next_stop": "Talasari Toll Plaza",
                "boarding_points": [
                    ("07:15", "Kadodara Char Rasta", "Shriji Travels Hub"),
                ],
                "dropping_points": [
                    ("13:30", "Andheri East - Gundavali", "Near Metro Station"),
                ]
            },
            {
                "id": "B108",
                "name": "Shriji Intercity Royal Multi-Axle",
                "operator": "Shriji Luxury Fleet",
                "number": "MP09 QR 6677",
                "bus_type": "AC Sleeper (2+1)",
                "category": "Sleeper",
                "decks": 2,
                "from_city": city_objs["Indore"],
                "to_city": city_objs["Nashik"],
                "dep_time": "19:00",
                "arr_time": "05:30",
                "duration": "10h 30m",
                "fare": 920.00,
                "rating": 4.8,
                "review_count": 440,
                "total_seats": 30,
                "amenities_csv": "wifi,charging,blanket,pillow,water,live_tracking,movie_screen",
                "driver_name": "Vikram Rajput",
                "driver_phone": "+91 98260 77889",
                "current_speed": "82 km/h",
                "next_stop": "Dhule Bypass",
                "boarding_points": [
                    ("18:45", "Vijay Nagar Square", "Near Brilliant Convention Centre"),
                ],
                "dropping_points": [
                    ("05:30", "CBS Stand Nashik", "Main Gate"),
                ]
            }
        ]

        for bdata in buses_data:
            bps = bdata.pop("boarding_points")
            dps = bdata.pop("dropping_points")
            bus_obj, _ = Bus.objects.get_or_create(id=bdata["id"], defaults=bdata)

            # Boarding Points
            for t, loc, lm in bps:
                BoardingPoint.objects.get_or_create(
                    bus=bus_obj, point_type='boarding', time=t, location=loc, landmark=lm
                )
            # Dropping Points
            for t, loc, lm in dps:
                BoardingPoint.objects.get_or_create(
                    bus=bus_obj, point_type='dropping', time=t, location=loc, landmark=lm
                )

        # 4. Reviews
        reviews_data = [
            ("Dr. Ananya Kulkarni", 5, "Nashik → Mumbai", "The Shriji Grand Express ride was exceptionally smooth! Punctual departure, crystal clean coach, and the live GPS tracking made pickup seamless. Highly recommended!", "Shriji Grand AC Seater"),
            ("Rohit Deshpande", 5, "Mumbai → Goa", "Best luxury sleeper service on the Konkan highway. Fresh blankets, clean pillows, safe driving throughout the night, and pleasant crew.", "Royal Multi-Axle AC Sleeper"),
            ("Pooja Mehta", 5, "Pune → Nagpur", "Traveled along Samruddhi Expressway. The bus arrived 15 mins before time! Super comfortable sleeper berths with personal charging ports and reading light.", "Star Multi-Axle AC Sleeper"),
            ("Karan Johar", 5, "Indore → Nashik", "Clean rest stop, very polite driver, and instant digital e-ticket with barcode. Shriji Travels is my default choice now.", "Intercity Luxury Sleeper"),
        ]
        for name, rat, rt, com, bt in reviews_data:
            Review.objects.get_or_create(name=name, route=rt, defaults={'rating': rat, 'comment': com, 'bus_type': bt, 'verified': True})

        # 5. Sample Booking
        sample_bus = Bus.objects.get(id="B101")
        if not Booking.objects.filter(pnr="SJ240001").exists():
            bk = Booking.objects.create(
                pnr="SJ240001",
                bus=sample_bus,
                travel_date=timezone.now().date(),
                lead_passenger_name="Rajesh Sharma",
                phone="9823456789",
                email="rajesh.sharma@example.com",
                boarding_point="Dwarka Circle, Shriji Lounge (05:45 AM)",
                dropping_point="Dadar East - Shriji Terminal (09:10 AM)",
                seats_csv="A1,A2",
                base_fare=1100.00,
                discount_amount=100.00,
                gst_amount=50.00,
                total_fare=1050.00,
                coupon_used="FESTIVE100",
                payment_mode="UPI",
                payment_id="PAY9921448",
                payment_status="PAID",
                status="confirmed"
            )
            Passenger.objects.create(booking=bk, name="Rajesh Sharma", age=34, gender="Male", seat_number="A1")
            Passenger.objects.create(booking=bk, name="Sunita Sharma", age=31, gender="Female", seat_number="A2")

        self.stdout.write(self.style.SUCCESS("Shriji Travels Database successfully populated!"))
