import requests
from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class Schedule:

    def __init__(self):
        # GCal Scopes
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        # Get schedule page
        self.url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/4e9f4c0e-7119-463d-afbf-0347d32bcf26'
        r = requests.get(self.url)
        # Parse table to json object
        self.soup = [[cell.text or cell.img for cell in row("td")]
                     for row in BeautifulSoup(r.text, 'html.parser')("tr")]
        return

    def extract_image(self, schedule):
        # Extract event image links only
        imagelink = []
        for race in schedule:
            imagetag = str(race)
            m = re.search(r'src=\"(.*)\" ', imagetag)
            imagelink.append(m.group(1))
        # Returning imagelink for debugging
        return imagelink

    def extract_info(self, schedule):
        # Extract full event info
        eventinfo = []
        for race in schedule:
            event = []
            # Categorize cells
            imagetag = str(race)
            main = str(race[1])
            extra = str(race[2])

            # Imagelink from imagetag
            imagelink = re.search(r'src=\"(.*)\" ', imagetag)

            # Extract date from main
            racedate_m = re.search(
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', main)
            racedate = racedate_m.group()
            date_time_obj = datetime.datetime.strptime(
                racedate, '%Y-%m-%d %H:%M:%S')
            # Convert from UTC to CST
            date_time_obj = date_time_obj - timedelta(hours=5)

            # Grand Prix Name from main
            gp = re.search(r'\n(\w+ GP|\w+ \w+ GP)\n', main)

            # Race Length from extra
            length = re.search(r'Race\sLength:(.*)\n\n\n\n\n', extra)

            # Append to list
            event.append(str(date_time_obj))
            event.append(gp.group(1))
            event.append(length.group(1))
            event.append(imagelink.group(1))
            eventinfo.append(event)
        return eventinfo

    def upcoming_gcal_events(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file(
                'token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('calendar', 'v3', credentials=creds)
            # Call the Calendar API
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            print('Getting the upcoming 10 events')
            events_result = service.events().list(calendarId='s1pshnma6bbvuv9lo628cv4heo@group.calendar.google.com', timeMin=now,
                                                  maxResults=10, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                print('No upcoming events found.')
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                print(calendars)
                return
            # Prints the start and name of the next 10 events
            for event in events:
                start = event['start'].get(
                    'dateTime', event['start'].get('date'))
                print(start, event['summary'])

        except HttpError as error:
            print('An error occurred: %s' % error)


class Updater:
    def update():
        return 0


# New Schedule object and do things
schedule = Schedule()
# link = schedule.extractImage(schedule.soup)
info = schedule.extract_info(schedule.soup)

# Debug output
# - First race
# - List of image links
# - Full event info
# print(schedule.soup[0])
# print(link)
print(info)
schedule.upcoming_gcal_events()
