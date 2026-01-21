from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def my_acconunt(request):
    return render(request, 'accounts/my_account.html')