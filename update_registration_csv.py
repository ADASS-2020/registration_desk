import csv
import os
import shutil
import time
import gspread


FNAME = 'registration.csv'
# Mapping from spreadsheet to registration csv
FIELDS = {
    'name': lambda r: f'{r["Name"]} {r["Surname"]}',
    'email': lambda r: r['Email'],
    'ticket_id': lambda r: r['Reference'],
    'isspeaker': lambda r: r['SPEAKER'] == 'Yes',
    'istrainer': lambda r: r['TRAINER'] == 'Yes',
    'isposterauth': lambda r: r['POSTER AUTHOR'] == 'Yes',
    'isadmin': lambda r: r['ADMIN'] == 'Yes',
    'isloc': lambda r: r['LOC'] == 'Yes',
    'ispoc': lambda r: r['POC'] == 'Yes',
    'isvolunteer': lambda r: r['VOLUNTEER'] == 'Yes',
}


def backup_existing_file(fname):
    bkp_name = f'{fname}-{time.time()}'
    while os.path.exists(bkp_name):
        time.sleep(1)
        bkp_name = f'{fname}-{time.time()}'
    shutil.copyfile(fname, bkp_name)


gc = gspread.service_account()
wks = gc.open('ADASS XXX Registrations').sheet1
records = wks.get_all_records()

# Just save a backup of the current file.
if os.path.exists(FNAME):
    backup_existing_file(FNAME)

# The ADASS Reg. spreadsheet has a number of keys which we do not need and
# some that we need. The bot CSV has the following format
# name,email,regid,isspeaker,istrainer,isposterauth,isadmin,isloc,ispoc,isvolunteer
with open(FNAME, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=list(FIELDS.keys()))
    writer.writeheader()

    # Write each row, skipping the first one which is a header of sorts.
    for rec in records[1:]:
        if not rec['Name']:
            continue
        writer.writerow({k: fn(rec) for k, fn in FIELDS.items()})
