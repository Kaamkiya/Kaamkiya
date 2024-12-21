import os
import json
import re
import sys

from datetime import datetime

import requests

def update(thing, content, file):
    return re.sub(f'<!--S:{thing}-->.*<!--E:{thing}-->',
                  f'<!--S:{thing}-->{content}<!--E:{thing}-->',
                  file)

if __name__ == '__main__':
    readme_file = sys.argv[1]
    if readme_file == '':
        readme_file = 'README.md'
    with open(readme_file, 'r') as f:
        contents = f.read()

    token = sys.argv[2]
    if token == '':
        sys.exit(1)

    gh_headers = {
        'Authorization': f'bearer {token}'
    }

    gh_req = '''
        query {
            viewer {
                createdAt
                    issues {
                        totalCount
                    }
                    pullRequests {
                        totalCount
                    }
                    gists(first: 100) {
                        totalCount
                        nodes {
                            stargazerCount
                        }
                    }
                    repositories(affiliations: OWNER, first: 100) {
                        totalCount
                        totalDiskUsage
                        nodes {
                            stargazerCount
                            languages(first: 40) {
                                edges {
                                    size
                                    node {
                                        name
                                    }
                                }
                            }
                        }
                    }
                    repositoriesContributedTo {
                        totalCount
                    }
                    followers {
                        totalCount
                    }
  	                following {
                        totalCount
                    }
            }
        }'''

    gh_res = requests.post('https://api.github.com/graphql', json.dumps({ 'query': gh_req }), headers=gh_headers)
    if not gh_res.ok or 'data' not in gh_res.json():
        print(gh_res.status_code)
        print(gh_res.text)
        sys.exit(1)

    data = gh_res.json()['data']['viewer']

    contents = update('ISSUES_OPENED', data['issues']['totalCount'], contents)
    contents = update('PRS_OPENED', data['pullRequests']['totalCount'], contents)
    contents = update('REPO_COUNT', data['repositories']['totalCount'], contents)
    contents = update('GIST_COUNT', data['gists']['totalCount'], contents)
    contents = update('CONTRIBUTED_TO', data['repositoriesContributedTo']['totalCount'], contents)
    contents = update('FOLLOWERS', data['followers']['totalCount'], contents)
    contents = update('FOLLOWING', data['following']['totalCount'], contents)
    contents = update('ACCOUNT_AGE',
                      datetime.now().year - int(data['createdAt'].split('-')[0]),
                      contents)
    stars = 0
    for repo in data['repositories']['nodes']:
        stars += repo['stargazerCount']
    for gist in data['gists']['nodes']:
        stars += gist['stargazerCount']
    contents = update('STARS_EARNED', stars, contents)

    if os.getenv('MT_TOKEN') != '':
        mt_headers = {
            'Authorization': f'ApeKey {os.getenv('MT_TOKEN')}'
        }
        mt_res = requests.get('https://api.monkeytype.com/results?limit=100', headers=mt_headers)

    with open(readme_file, 'w') as f:
        f.write(contents)

