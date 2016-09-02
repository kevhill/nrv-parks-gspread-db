import requests
import psycopg2
import os
import StringIO
import csv
import json

PARK_INFO_CSV_URL = os.environ.get('PARK_INFO_CSV_URL')

r = requests.get(PARK_INFO_CSV_URL)

def location_parser(val, row):
	if val:
		return { 'point_location': map(float, val.split(',')) }
	else:
		return None

def osm_info_parser(val, row):
	if val:
		output = {}
		osm_info = output.setdefault('osm_info', [])
		osm_types = row['OSM Type'].split(';')

		for i, v in enumerate(val.split(';')):
			osm_type = osm_types[i] if i < len(osm_types) and osm_types[i] else None
			osm_info.append({ 'osm_id': v, 'osm_type': osm_type })

		return { 'osm_info': json.dumps(output)}

	else:
		return None

raw_data = list(csv.DictReader(r.content.split('\n')))

parsers = {
	'Location': location_parser,
	'Name': lambda val, row: { 'park_name': val },
	'Alternative Names': lambda val, row: { 'alternate_names': json.dumps([{ 'name': v.strip() } for v in val.split(',')]) } if val else None,
	'ID': lambda val, row: { 'id': int(val) } if val else None,
	'OSM ID': osm_info_parser,
	'OSM TYPE': lambda val, row: None,
	'Amenities and Activities': lambda val, row: { 'amenities': val.split(',') } if val else None,
}

parsed_data = []
for row in raw_data:
	new_row = {}
	for key, val in row.iteritems():
		if key in parsers:
			entry = parsers[key](val, row)
			#print key, val, entry
			if entry:
				new_row.update(entry)
		elif val:
			new_row[key.lower().replace(' ', '_')] = val

	parsed_data.append(new_row)