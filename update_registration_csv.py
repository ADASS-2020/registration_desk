from collections import defaultdict
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
                        host="pretalx.adass2020.es",
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
email_typeids = defaultdict(list)
cur = conn.cursor()
cur.execute(sql)
records = cur.fetchall()
for row in records:
    email_typeids[row[3].lower()].append(row[1])
conn.close()

gc = gspread.service_account()
wks = gc.open('ADASS XXX Registrations').sheet1
records = wks.get_all_records()
# Skip the header
records = records[1:]

# Just save a backup of the current file.
if os.path.exists(FNAME):
    backup_existing_file(FNAME)

# Process all the registration entries in one go and then write to disk. We do
# this since a person might have >1 contribution and the above SQL query would
# simply return multiple rows in that case.
missing = 0
# email -> record
people = {}
for rec in records:
    if not rec['Name']:
        continue
    if not rec['Reference']:
        missing += 1
        continue

    # Make sure to strip all values!
    for k in rec:
        if isinstance(rec[k], str):
            rec[k] = rec[k].strip()

    # Here we do things differently based on whether this entry is not in
    # people or we are seeing it again.
    email = rec['Email'].lower()
    if email not in people:
        # It is a new record!
        people[email] = rec

    # fetch speakers and posters authors
    for type_id in email_typeids[email]:
        if type_id == 13 or type_id == 18:
            people[email]['POSTER'] = "Yes"
        else:
            people[email]['SPEAKER'] = "Yes"

# The ADASS Reg. spreadsheet has a number of keys which we do not need and
# some that we need. The bot CSV has the following format
# name,email,regid,isspeaker,istrainer,isposterauth,isadmin,isloc,ispoc,isvolunteer
n = 0
with open(FNAME, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=list(FIELDS.keys()))
    writer.writeheader()

    # Write each row
    for rec in people.values():
        writer.writerow({k: fn(rec) for k, fn in FIELDS.items()})
        n += 1
print(f'Written {n} records, missing {missing}')
