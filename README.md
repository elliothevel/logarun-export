## LogARun Export
[LogARun.com](http://www.logarun.com) is a great site for tracking runs and
other fitness activities. Unfortunately, it lack features for exporting and
reporting on your data. `logarun_export` extracts logs from LogARun for offline
backup and analysis.

### Usage
`logarun_export` runs as a Python script that downloads all logs in a given
date range. To run the script, clone this repository, install the dependencies,
and store your LogARun credentials in the `LOGARUN_USERNAME` and
`LOGARUN_PASSWORD` environment variables. The do
```
$ python logarun_export.py <start-date> <end-date>
```
A JSON file will be created with information about all activities and notes for
the days in the given range.
