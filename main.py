from __future__ import print_function
import csv
from datetime import date
from vietname_lunar_calendar import *
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/calendar.settings.readonly',
          'https://www.googleapis.com/auth/calendar.events.readonly',
          'https://www.googleapis.com/auth/calendar.events',
          ]



def get_calendars(service):
    page_token = None
    calendars = []
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        calendars.extend(calendar_list.get('items', []))
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    return calendars


def get_time_zone(service):
    setting = service.settings().get(setting='timezone').execute()

    return setting['value']


def get_primary_calendar(calendars):
    for calendar in calendars:
        if calendar.get('primary', False):
            return calendar


def is_exist(calendars, name):
    for calendar in calendars:
        if name == calendar['summary']:
            return calendar
    return None


def create_calendar(service, name, time_zone):
    calendar = {
        'summary': name,
        'timeZone': time_zone,
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    return created_calendar
    

def create_event(service, calendar, event_body):
    event = service.events().insert(calendarId=calendar, body=event_body).execute()


def event_exist(sevice, calendar, event_body):
    try:
        event = service.events().get(calendarId=calendar, eventId=event_body['id']).execute()
        return True
    except:
        return False

def event_delete(sevice, calendar, event_body):
    event = service.events().delete(calendarId=calendar, eventId=event_body['id']).execute()
    

def event_update(sevice, calendar, event_body):
    event_id = event_body['id']
    del event_body['id']
    event = service.events().update(calendarId=calendar, eventId=event_id, body=event_body).execute()

def auth():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


class LunarEvent(object):
    def __init__(self, dd, mm, year, title, alarms):
        self.dd = dd
        self.mm = mm
        self.year = year
        self.title = title
        self.alarms = alarms
        solar_date = L2S(self.dd, self.mm, self.year, 0)
        self.solar_date = date(solar_date[2], solar_date[1], solar_date[0])


    def alarms_to_reminders(self):
        reminders = []
        for alarm in self.alarms:
            reminders.append({
                'method': 'popup',
                'minutes': 24 * 60 * alarm - 9 * 60
            })
        reminders.append({
            'method': 'popup',
            'minutes': 0
        })
        return reminders

    def gen_id(self):
        new_id = self.title.replace(' ', '').lower() + '' + self.solar_date.strftime('%Y%m%d')
        return new_id
    
    def to_event_body(self):
        event = {
            'summary': self.title,
            'id': self.gen_id(),
            'start': {
                'date': self.solar_date.isoformat(),
            },
            'end': {
                'date': self.solar_date.isoformat(),
            },
            'reminders': {
                'useDefault': False,
                'overrides': self.alarms_to_reminders()
            },
        }
        return event
        
        
def read_events(file_name):
    ret = []
    with open(file_name) as fp:
        csv_reader = csv.reader(fp, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                print(row)
                line_count += 1
                row[0] = [int(x) for x in row[0].strip().split('/')]
                row[-1] = [int(x) for x in row[-1].strip().split(' ')]
                ret.append(row)
    return ret


def main():
    calendar_name = "AmLich1"
    number_years = 10
    service = auth()
    time_zone = get_time_zone(service)
    calendars = get_calendars(service)
    calendar = is_exist(calendars, calendar_name)
    if calendar is None:
        calendar = create_calendar(service, calendar_name, time_zone)
    
    events = read_events('events.csv')
    today = date.today()
    year = today.year
    create_events = []
    for event in events:
        for offset in range(number_years):
            new_event = LunarEvent(event[0][0], event[0][-1], year + offset, 
                                   event[1], event[-1])
            create_events.append(new_event)
    
    for event in create_events:
        if event_exist(service, calendar['id'], event.to_event_body()):
            event_update(service, calendar['id'], event.to_event_body())
        else:
            create_event(service, calendar['id'], event.to_event_body())
        pass
        
        
if __name__ == "__main__":
    main()
    new_date = date(2020, 1, 28)
    dd = new_date.day
    mm = new_date.month
    year = new_date.year
    jd = jdFromDate(dd, mm, year)
    print(jd)
    print(jdToDate(jd))
    print(S2L(dd, mm, year))
    print(L2S(4, 1, 2020, 0))
    events = read_events('events.csv')
    print(events)