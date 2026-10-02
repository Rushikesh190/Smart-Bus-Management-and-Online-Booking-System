from .models import PassengerUser

def passenger_context(request):
    passenger_id = request.session.get('passenger_user_id')
    logged_in_passenger = None
    if passenger_id:
        try:
            logged_in_passenger = PassengerUser.objects.get(id=passenger_id)
        except PassengerUser.DoesNotExist:
            request.session.pop('passenger_user_id', None)
            
    return {
        'current_passenger': logged_in_passenger,
        'is_passenger_logged_in': logged_in_passenger is not None,
    }
