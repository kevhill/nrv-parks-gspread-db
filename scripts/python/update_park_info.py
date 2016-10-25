import requests
import psycopg2
import os
import StringIO
import csv
import json

from urlparse import urlparse

DATABASE_URL =  os.environ.get('DATABASE_URL')
parsed_db_url = urlparse(DATABASE_URL)
user_password, host = parsed_db_url.netloc.split('@')
user, password = user_password.split(':')
database = parsed_db_url.path.split('/')[1]

SCHEMA = os.environ.get('DATABASE_SCHEMA')
PARK_INFO_CSV_URL = os.environ.get('PARK_INFO_CSV_URL')

r = requests.get(PARK_INFO_CSV_URL)

def query_to_dict(cur, columns, table, where=None):
    query_str = "SELECT {col_str} FROM {table}".format(
        col_str = ', '.join(columns),
        table = table
        )
    if where:
        query_str += " WHERE " + where
    cur.execute(query_str)

    return [{key: val for key, val in zip(columns, record)} for record in cur]


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

parsers = {
    'Location': location_parser,
    'Name': lambda val, _: { 'park_name': val },
    'Alternative Names': lambda val, _: { 'alternate_names': json.dumps([{ 'name': v.strip() } for v in val.split(',')]) } if val else None,
    'ID': lambda val, _: { 'id': int(val) } if val else None,
    'OSM ID': osm_info_parser,
    'OSM TYPE': lambda val, _: None,
    'Amenities and Activities': lambda val, _: { 'amenities': val.split(',') } if val else None,
}

if __name__ == "__main__":

    conn = psycopg2.connect(host=host, database=database, user=user, password=password)

    # first, read a bunch of data from the db
    with conn.cursor() as cur:

        parks = query_to_dict(cur, ['id', 'park_name'], SCHEMA + '.parks')
        stewards = query_to_dict(cur, ['id', 'steward_name'], SCHEMA + '.stewards')
        amenity_types = query_to_dict(cur, ['id', 'amenity_name'], SCHEMA + '.amenity_type')
        amenities = query_to_dict(cur, ['id', 'park_id', 'amenity_type_id'], SCHEMA + '.amenities')

    # some parsers we can't build until after we have this data
    parsers.update(
        {
            'Steward': lambda val, _: { 'steward_id': (row['id'] for row in stewards if row['steward_name'] == val).next()},

        }
    )

    raw_data = list(csv.DictReader(r.content.split('\n')))

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