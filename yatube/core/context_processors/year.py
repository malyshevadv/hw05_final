from datetime import datetime


def year(request):
    cur_year = datetime.today().year
    return {
        'year': cur_year
    }
