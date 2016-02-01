from django.shortcuts import render


def score(request, org = None):
    if org == None:
        return render(request, 'teams.html', {})
    else:
        return render(request, 'score.html', {'org': org})

def individual(request, id = 0):
    return render(request, 'individual.html', {'id': id})

def tutorial2(request, page = 1):
    return render(request, 'tutorial2.html', {'page': page})

def account_settings(request, page = 1):
    return render(request, 'account_settings.html', {'page': page})

def usersettings(request, pk= None, token = None):
    return render(request, 'UserSettings.html', {'pk': pk, 'token' : token})

