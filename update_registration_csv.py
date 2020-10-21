import csv
import os
import shutil
import time
import gspread
import psycopg2


FNAME = 'registration.csv'
# Mapping from spreadsheet to registration csv
FIELDS = {
    'name': lambda r: f'{r["Name"]} {r["Surname"]}',
    'email': lambda r: r['Email'],
    'ticket_id': lambda r: r['Reference'],
    'isspeaker': lambda r: r['SPEAKER'] == 'Yes',
    'istrainer': lambda r: r['TRAINER'] == 'Yes',
    'isposterauth': lambda r: r['POSTER'] == 'Yes',
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


conn = psycopg2.connect(database="pretalx",
                        user="pretalx",
                        password="",
                        host="localhost",
                        port="5432")


sql = """
SELECT 
submission_submission.title, 
submission_submission.submission_type_id,
submission_submission.paper_id, 
person_user.email
FROM 
submission_submission,
person_user
WHERE
submission_submission.main_author_id=person_user.id
AND submission_submission.state not in ('deleted', 'withdrawn')
ORDER BY email;
"""
cur = conn.cursor()
cur.execute(sql)
records = cur.fetchall()
type_ids = [row[1] for row in records]
authors_emails = [row[3] for row in records]

gc = gspread.service_account()
wks = gc.open('ADASS XXX Registrations').sheet1
records = wks.get_all_records()

# Just save a backup of the current file.
if os.path.exists(FNAME):
    backup_existing_file(FNAME)

n = 0
missing = 0
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
        if not rec['Reference']:
            missing += 1
            continue

        # fetch speakers and posters authors
        if rec['Email'] and rec['Email'] in authors_emails:
            idx = authors_emails.index(rec['Email'])
            type_id = type_ids[idx]
            if type_id == 13 or type_id == 18:
                rec['POSTER'] = "Yes"
            else:
                rec['SPEAKER'] = "Yes"

        # Make sure to strip all values!
        for k in rec:
            if isinstance(rec[k], str):
                rec[k] = rec[k].strip()

        writer.writerow({k: fn(rec) for k, fn in FIELDS.items()})
        n += 1
print(f'Written {n} records, missing {missing}')

conn.close()

