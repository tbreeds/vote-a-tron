#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import requests
import requests.auth
import urllib
import sys


def get_reviews(host, query):
    print('Running: %s' % (query))
    url = ('https://%s/changes/?q=%s&o=CURRENT_REVISION'
           % (host, urllib.quote_plus(query, safe='/:=><')))
    r = requests.get(url)
    if r.status_code == 200:
        data = json.loads(r.text[4:])
    else:
        data = []
    return data


def vote_on_change(host, auth, change, msg, vote, workflow, dryrun=True):
    change_id = change['id']
    revision_id = change['revisions'].keys()[0]
    url = ('https://%s/a/changes/%s/revisions/%s/review'
           % (host, change_id, revision_id))
    data = {'message': msg,
            'labels': {'Code-Review': vote,
                       'Workflow': workflow}}

    print('Voting : %s' % (data))
    print('On     : %s' % (change_id))

    if dryrun:
        print('        : ...skipping as this is a dry run')
    else:
        r = requests.post(url, auth=auth,
                          headers={'Content-Type': 'application/json'},
                          json=data)
        if r.status_code == 200:
            print('Status : OK')
        else:
            print('Status : Failed')
            print('       : %s' % (r))
            print('       : %s' % (r.text))


def main(args):
    auth = requests.auth.HTTPDigestAuth(args.user, args.password)
    for change in get_reviews(args.host, args.query):
        vote_on_change(args.host, auth, change, args.msg, args.vote,
                       args.workflow, args.bravery != 'high')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vote-a-tron')

    # FIXME: Make the required args more robust
    parser.add_argument('--user', dest='user', required=True,
                        help=('Gerrit username'))
    parser.add_argument('--password', dest='password', required=True,
                        help=('Gerrit HTTP password'))
    parser.add_argument('--query', dest='query', required=True,
                        help=('Gerrit query matching *ALL* reviews to '
                              'vote on'))
    parser.add_argument('--msg', dest='msg', required=True,
                        help=('Review comment'))
    parser.add_argument('--vote', dest='vote', default=0, type=int,
                        choices=xrange(-2, 3),
                        help=('Vote to leave default: %(default)s'))
    parser.add_argument('--workflow', dest='workflow', default=0,
                        choices=xrange(-1, 2), type=int,
                        help=('Workflow value default: %(default)s'))
    parser.add_argument('--host', dest='host',
                        default='review.openstack.org',
                        help=('Gerrit hostname default: %(default)s'))
    parser.add_argument('--bravery', dest='bravery', default='low',
                        help=('Set this to high to actually vote!'))

    args, extras = parser.parse_known_args()

    sys.exit(main(args))
