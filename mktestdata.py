#!/usr/bin/env python3
import csv
import sys


HEADER = [
    'name',
    'email',
    'ticket_id',
    'isspeaker',
    'istrainer',
    'isposterauth',
    'isadmin',
    'isloc',
    'ispoc',
    'isvolunteer',
]
PEOPLE = [
    {
        'name': 'Pablo Mellado',
        'email': 'mellado@iram.es',
        'ticket_id': 'mellado@iram.es',
        'isspeaker': False,
        'istrainer': False,
        'isposterauth': True,
        'isadmin': False,
        'isloc': True,
        'ispoc': False,
        'isvolunteer': False,
    },
    {
        'name': 'Jose Enrique Ruiz',
        'email': 'jer@iaa.es',
        'ticket_id': 'jer@iaa.es',
        'isspeaker': False,
        'istrainer': True,
        'isposterauth': False,
        'isadmin': True,
        'isloc': True,
        'ispoc': True,
        'isvolunteer': False,
    },
    {
        'name': 'Francesco Pierfederici',
        'email': 'fpierfed@iram.es',
        'ticket_id': 'fpierfed@iram.es',
        'isspeaker': False,
        'istrainer': False,
        'isposterauth': False,
        'isadmin': True,
        'isloc': True,
        'ispoc': True,
        'isvolunteer': False,
    },
    {
        'name': 'Alicia Gambetta',
        'email': 'info@aliciagambetta.com',
        'ticket_id': 'info@aliciagambetta.com',
        'isspeaker': False,
        'istrainer': True,
        'isposterauth': False,
        'isadmin': False,
        'isloc': True,
        'ispoc': False,
        'isvolunteer': False,
    },
]

writer = csv.DictWriter(sys.stdout, fieldnames=HEADER)
writer.writeheader()
for person in PEOPLE:
    writer.writerow(person)
