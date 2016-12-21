#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import requests
import requests.auth
import urllib
import sys

REVIEW_COUNT = 0


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


def _review(url, auth, method, change_id, data, dryrun):
    global REVIEW_COUNT
    REVIEW_COUNT += 1
    print('Voting : %s' % (data))
    print('On     : %s' % (change_id))

    if dryrun:
        print('        : ...skipping as this is a dry run')
    else:
        method = getattr(requests, method)
        r = method(url, auth=auth,
                   headers={'Content-Type': 'application/json'},
                   json=data)
        if r.status_code == 200:
            print('Status : OK')
        else:
            print('Status : Failed')
            print('       : %s' % (r))
            print('       : %s' % (r.text))


def vote_on_change(host, auth, change, msg, vote, workflow, dryrun=True):
    change_id = change['id']
    revision_id = change['revisions'].keys()[0]
    url = ('https://%s/a/changes/%s/revisions/%s/review'
           % (host, change_id, revision_id))
    data = {'message': msg,
            'labels': {'Code-Review': vote,
                       'Workflow': workflow}}

    _review(url, auth, 'post', change_id, data, dryrun)


def abandon_change(host, auth, change, msg, dryrun=True):
    change_id = change['id']
    url = ('https://%s/a/changes/%s/abandon' % (host, change_id))
    data = {'message': msg}

    _review(url, auth, 'post', change_id, data, dryrun)


def change_topic(host, auth, change, topic, dryrun=True):
    change_id = change['id']
    url = ('https://%s/a/changes/%s/topic' % (host, change_id))
    data = {'topic': topic}

    _review(url, auth, 'put', change_id, data, dryrun)


def main(args):
    global REVIEW_COUNT

    auth = requests.auth.HTTPDigestAuth(args.user, args.password)
    for change in get_reviews(args.host, args.query):
        if args.abandon:
            abandon_change(args.host, auth, change, args.msg,
                           args.bravery != 'high')
        elif args.topic:
            change_topic(args.host, auth, change, args.topic,
                         args.bravery != 'high')
        else:
            vote_on_change(args.host, auth, change, args.msg, args.vote,
                           args.workflow, args.bravery != 'high')

        if args.limit > 0 and REVIEW_COUNT >= args.limit:
            print('Review limit hit, stopping early')
            return 0

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
    fu = parser.add_mutually_exclusive_group()
    fu.add_argument('--msg', dest='msg',
                    help=('Review comment'))
    fu.add_argument('--topic', dest='topic',
                    help='Update the topic on all reviews to ...')
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
    parser.add_argument('--abandon', dest='abandon', default=False,
                        action='store_true',
                        help=('Abandon matching changes'))
    parser.add_argument('--limit', dest='limit', default=0, type=int,
                        help=('The maximum number of reviews to '
                              'post. 0 for no limit.'))

    args, extras = parser.parse_known_args()

    sys.exit(main(args))
