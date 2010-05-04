import csv
import optparse
import os
import re
import sys
import urllib
import urllib2


class BabyNameScraper(object):

    def __init__(self, states=None, filename=None):
        """Set states to None to get national data.

        Otherwise states should be a list of two-letter
        state abbreviations.
        """
        if states:
            self.years = range(1960, 2009)
        else:
            self.years = range(1880, 2009)

        self.states = states or [None,]
        self.filename = filename

        self.fields = ['year', 'name', 'sex', 'number', 'rank', ]
        if states is not None:
            self.fields.append('state')


    def run(self):
        self.write_headers()
        for year in self.years:
            for state in self.states:
                page = self.get_page(year, state)
                for data in self.parse_page(page, state):
                    data['year'] = year
                    self.save_data(data)


    def write_headers(self):
        if self.filename:
            with open(self.filename, 'a') as fh:
                csv.writer(fh).writerow(self.fields)
        else:
            csv.writer(sys.stdout).writerow(self.fields)


    def get_page(self, year, state=None):
        """Get the content of the page listing the top 1,000 baby names 
        for the given year.
        """
        base_url = 'http://www.ssa.gov/cgi-bin'

        if state:
            query = {'year': year, 'state': state}
            path = 'namesbystate.cgi'
        else:
            query = {'year': year, 'top': 1000, 'number': 'n'}
            path = 'popularnames.cgi'

        url = os.path.join(base_url, path)
        req = urllib2.Request(url, urllib.urlencode(query))
        response = urllib2.urlopen(req)

        if response.msg == 'OK':
            return response.read()

        return None


    def parse_page(self, page, state=None):
        """Get the relevant baby-name data from the given HTML page.
        """
        rows = re.findall(r'<tr align="right">.*?<\/tr>', page, re.S)

        fields = ['rank', 'male', 'male_count', 'female', 'female_count', ]

        if state:
            regex = re.compile(r'<td(?: align="center")?>(.*?)<\/td>')
        else:
            regex = re.compile(r'<td>(?P<cell_content>.*?)<\/td>')

        for row in rows:
            data = dict(zip(fields, regex.findall(row)))
            data['state'] = state
            
            # Yield male name
            yield {'name': data['male'],
                   'sex': 'M',
                   'number': data['male_count'],
                   'rank': data['rank'], 
                   'state': data['state'], }

            # Yield female names
            yield {'name': data['female'],
                   'sex': 'F',
                   'number': data['female_count'],
                   'rank': data['rank'], 
                   'state': data['state'], }


    def save_data(self, data):
        if data.get('state', None) is None:
            del(data['state'])

        if self.filename:
            with open(self.filename, 'a') as fh:
                csv.DictWriter(fh, self.fields).writerow(data)
        else:
            csv.DictWriter(sys.stdout, self.fields).writerow(data)


ALLSTATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA',
             'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA',
             'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY',
             'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
             'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', ]


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-s',
                      '--states',
                      dest='states',
                      help='a comma-separated list of states to get data for, or ALL for all states')
    parser.add_option('-f', 
                      '--file', 
                      dest='filename',
                      help='write data to FILE (will be written to standard output if no filename is given')

    options, args = parser.parse_args()

    if options.states.lower() == 'all':
        states = ALLSTATES
    elif options.states is not None:
        states = options.states.split(',')
    else:
        states = None

    scraper = BabyNameScraper(states, options.filename).run()
