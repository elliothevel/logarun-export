"""Utility for exporting data from LogARun.com."""
import argparse
import json
import logging
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta

import bs4
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


log = logging.getLogger(__name__)


_BASE_URL = 'http://www.logarun.com/'
_ACTIVITY_REGEX = re.compile('ctl00_Content_c_applications_act[0-9+]_c_app$')
_TAG_LOCATIONS = {
    'note': ['p', {'id': 'ctl00_Content_c_note_c_note'}],
    'title': ['tr', {'class', 'editTblDayTitle'}],
    'activity_title': ['div', {'class': 'title'}],
    'activity_fields': ['span', {'class': 'field'}],
    'activity_tags': [
        'div',
        {'id': lambda name: _ACTIVITY_REGEX.match(str(name))}
    ]
}
_DISTANCE_UNITS = ('Mile(s)', 'Kilometer(s)', 'Yard(s)')


def _get_text(tag):
    """Extract and clean text from a BS4 tag."""
    return tag.get_text().strip(' \n')


def _login(session, username, password):
    """Authenticate a session by posting login information."""
    data = {
        'LoginName': username,
        'Password': password,
        'SubmitLogon': 'true',
        'LoginNow': 'Login'
    }
    response = session.post(_BASE_URL + 'logon.aspx', data=data)
    response.raise_for_status()


def _parse_log(soup):
    """Parse the contents of a daily log entry."""
    activities = defaultdict(dict)

    for tag in soup.findAll(*_TAG_LOCATIONS['activity_tags']):
        name = _get_text(tag.find(*_TAG_LOCATIONS['activity_title']))

        for field_tag in tag.findAll(*_TAG_LOCATIONS['activity_fields']):
            label = field_tag.find('label')
            value = _get_text(field_tag.find('span'))

            # Special case for units, which have no label.
            if label is None and value in _DISTANCE_UNITS:
                label = 'Distance Units'
            else:
                label = _get_text(label)

            activities[name][label] = value

    return {
        'note': _get_text(soup.find(*_TAG_LOCATIONS['note'])),
        'title': _get_text(soup.find(*_TAG_LOCATIONS['title'])),
        'activities': activities
    }


def _export_date(session, username, date):
    """Download and parse the log for a single day."""
    url = '/'.join((_BASE_URL + 'calendars',
                    username,
                    date.strftime('%Y/%m/%d')))
    response = session.get(url)
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.content, 'html.parser')
    return {'date': str(date), **_parse_log(soup)}


def export_date_range(username, password, start_date, end_date, delay=1):
    """Export logs in an inclusive date range."""
    data = []
    with requests.Session() as session:
        retries = Retry(total=5,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        _login(session, username, password)
        log.info('Logged in user %s', username)

        log.info('Exporting logs from %s to %s', start_date, end_date)
        for day in range((end_date - start_date).days + 1):
            date = start_date + timedelta(days=day)
            data.append(_export_date(session, username, date))
            log.info('Exported log for %s', date)
            time.sleep(delay)

    return data


def _date_type_validator(date):
    try:
        return datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            '{} is not a date format'.format(date))


def _maybe_default_output_name(filename, start_date, end_date):
    """Return the given filename or create a default one."""
    if filename is not None:
        return filename
    else:
        return ('logarun_export_{}_{}.json'
                .format(start_date.strftime('%Y%m%d'),
                        end_date.strftime('%Y%m%d')))


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Export LogARun data.')
    parser.add_argument('start',
                        type=_date_type_validator,
                        help=('Export logs since this date. Should be in '
                              'the form YYYY-MM-DD.'))
    parser.add_argument('-e', '--end',
                        type=_date_type_validator,
                        default=datetime.today().strftime('%Y-%m-%d'),
                        help=('Export logs up to and including this date. '
                              'Should be of the form YYYY-MM-DD. Defaults '
                              'to today.')),
    parser.add_argument('-u', '--username',
                        default=os.getenv('LOGARUN_USERNAME'),
                        help=('LogARun username. If not given, the value of '
                              'the `LOGARUN_USERNAME` environment variable '
                              'will be used.'))
    parser.add_argument('-p', '--password',
                        default=os.getenv('LOGARUN_PASSWORD'),
                        help=('LogARun password. If not given, the value of '
                              'the `LOGARUN_PASSWORD` environment variable '
                              'will be used.'))
    parser.add_argument('-o', '--output',
                        help=('Write exported logs to this file. Defaults to '
                              'a standard format that includes the date '
                              'range covered by the export.'))
    return parser.parse_args()


def main():
    """Run an export and write results to a file."""
    args = parse_args()

    if not all((args.username, args.password)):
        raise RuntimeError('Must specify a username and password via '
                           'command-line arguments or the environment')

    data = export_date_range(args.username,
                             args.password,
                             args.start,
                             args.end)

    fname = _maybe_default_output_name(args.output, args.start, args.end)
    log.info('Writing output to %s', fname)
    with open(fname, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


if __name__ == '__main__':
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
