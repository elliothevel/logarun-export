import datetime
from unittest import mock

import vcr

from logarun_export import export_date_range, main


@vcr.use_cassette('tests/cassettes/export.yaml',
                  filter_post_data_parameters=['Password'])
def test_export_date_range():
    data = export_date_range('testaccount1',
                             '',
                             datetime.date(2017, 7, 13),
                             datetime.date(2017, 7, 15),
                             delay=0)

    assert data == [
        {'title': 'Cross Train',
         'activities': {'Bike': {'Distance': '0.00',
                                 'Time': '00:30:00',
                                 'Pace': '',
                                 'Distance Units': 'Mile(s)'},
                        'Swim': {'Distance': '0.00',
                                 'Time': '00:40:00',
                                 'Pace': '',
                                 'Distance Units': 'Yard(s)'}},
         'note': 'Biked and swam.',
         'date': '2017-07-13'},
        {'title': 'Off',
         'activities': {'Health': {'Morning Pulse': '0 bpm',
                                   'Body Fat %': '0.00',
                                   'Sleep Hours': '8.00 hrs.',
                                   'Weight': '0.00 lbs.'}},
         'note': 'No Note',
         'date': '2017-07-14'},
        {'title': 'Saturday Run',
         'activities': {'Run': {'Distance': '8.00',
                                'Time': '01:00:01',
                                'Shoes': '',
                                'Distance Units': 'Mile(s)',
                                'Pace': '00:07:30.12 /mile',
                                'Avg HR': '0.0'},
                        'Health': {'Morning Pulse': '0 bpm',
                                   'Body Fat %': '0.00',
                                   'Sleep Hours': '8.00 hrs.',
                                   'Weight': '0.00 lbs.'}},
         'note': 'Easy run',
         'date': '2017-07-15'}
    ]


@mock.patch('logarun_export.json.dump')
@mock.patch('logarun_export.export_date_range')
@mock.patch('logarun_export.parse_args')
def test_main(mock_parse, mock_export, mock_dump):
    export_data = [
        {'date': '2017-07-14', 'title': 'No title', 'activities': []},
        {'date': '2017-07-15', 'title': 'No title', 'activities': []}
    ]
    mock_parse.return_value = mock.Mock(username='username',
                                        password='password',
                                        start=datetime.date(2017, 7, 14),
                                        end=datetime.date(2017, 7, 15),
                                        output=None)
    mock_export.return_value = export_data

    with mock.patch('logarun_export.open', mock.mock_open()) as m:
        main()

    mock_export.assert_called_with('username',
                                   'password',
                                   datetime.date(2017, 7, 14),
                                   datetime.date(2017, 7, 15))
    m.assert_called_once_with('logarun_export_20170714_20170715.json', 'w')
    mock_dump.assert_called_once_with(export_data,
                                      m(),
                                      indent=4,
                                      sort_keys=True)
