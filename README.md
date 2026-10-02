# 🚌 Shriji Travels — Full-Stack Django & Bootstrap 5 Bus Booking Platform

A modern, full-featured, enterprise-grade Bus Booking, Telemetry, and Fleet Management web application built exclusively with **Python, Django, HTML5, CSS3, and Bootstrap 5**.

---

## 🌟 Tech Stack

- **Backend Framework**: Python 3.14 + Django 6.1
- **Frontend UI & Styling**: HTML5, Custom CSS3 Design System, Bootstrap 5.3
- **Database**: SQLite3 (ORM with Migrations & Management Commands)
- **Interactive Features**: Dynamic Seat Matrices, Canvas Confetti, SVG QR/Barcode Engine, AI Travel Chatbot

---

## 🚀 How to Run the Django Application

### 1. Install Dependencies
```bash
pip install django
```

### 2. Apply Migrations & Seed Sample Fleet Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 3. Start the Django Development Server
```bash
python manage.py runserver
```

### 4. Open in Browser
Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔑 Key Features & Views

| View Name | Route | Description |
|---|---|---|
| **Home Page** | `/` | Hero section, route radar, search console, featured fleet, offers & FAQ |
| **Search Results** | `/search/` | Multi-faceted filter sidebar (Time slots, Coach class, Amenities, Fare slider), Sorting |
| **Seat Selection** | `/seats/<bus_id>/` | Interactive coach floor plan (Lower & Upper Deck sleeper toggle, 2+2 layout), dynamic passenger forms, live promo discount calculator |
| **Checkout & Payment** | `/checkout/` | Multi-gateway simulator (UPI QR Code with timer, Credit/Debit card with 3D preview, Net Banking, Cash on Boarding) |
| **Digital E-Ticket** | `/ticket/<pnr>/` | Airline-grade printable digital ticket with SVG QR code & barcode, WhatsApp sharing |
| **Live GPS Radar** | `/live-tracking/` | Real-time animated road waypoints, speedometer telemetry (74 km/h), driver call & SOS |
| **My Bookings** | `/my-bookings/` | Lookup tickets by phone/PNR, instant cancellation with automated 90% refund |
| **Offers & Deals** | `/offers/` | Coupon cards with 1-click copy code (`SHRIJI20`, `FIRST50`, `FESTIVE100`, etc.) |
| **Customer Reviews** | `/reviews/` | Verified customer testimonials and review submission form |
| **Admin Operations** | `/admin-dashboard/` | KPI counters, fleet schedule manager, deploy coach form, bookings table, CSV Export |
| **Django Admin** | `/django-admin/` | Standard Django admin interface |

---

## 🔐 Admin Credentials

- **Fleet Portal Password**: `admin123`
- **Django Superuser**: `admin` / `admin123`

---

&copy; 2026 Shriji Travels Network Private Limited. All Rights Reserved.
