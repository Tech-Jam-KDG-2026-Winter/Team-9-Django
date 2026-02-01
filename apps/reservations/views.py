from django.shortcuts import render

def new_reservation(request):
    return render(request, "reservations/new.html")
# Create your views here.
