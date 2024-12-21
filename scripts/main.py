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
    readme_file = os.getenv('README')
    if readme_file == '':
        readme_file = 'README.md'
    with open(readme_file, 'r') as f:
        contents = f.read()

    token = os.getenv('GH_TOKEN')
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
                            name
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

    stars = 0
    langs = {}
    ignore_repos = os.getenv('IGNORE_REPOS').split(',')
    for repo in data['repositories']['nodes']:
        stars += repo['stargazerCount']

        if repo['name'] not in ignore_repos:
            for lang in repo['languages']['edges']:
                lang_name = lang['node']['name']
                if langs.get(lang_name, None) is None:
                    langs[lang_name] = 0
                langs[lang_name] += lang['size']

    for gist in data['gists']['nodes']:
        stars += gist['stargazerCount']

    contents = update('ISSUES_OPENED',  data['issues']['totalCount'],                    contents)
    contents = update('PRS_OPENED',     data['pullRequests']['totalCount'],              contents)
    contents = update('REPO_COUNT',     data['repositories']['totalCount'],              contents)
    contents = update('GIST_COUNT',     data['gists']['totalCount'],                     contents)
    contents = update('CONTRIBUTED_TO', data['repositoriesContributedTo']['totalCount'], contents)
    contents = update('FOLLOWERS',      data['followers']['totalCount'],                 contents)
    contents = update('FOLLOWING',      data['following']['totalCount'],                 contents)
    contents = update('ACCOUNT_AGE',
                      datetime.now().year - int(data['createdAt'].split('-')[0]),
                      contents)
    contents = update('STARS_EARNED', stars, contents)
    
    lang_fmt = os.getenv('LANG_FMT')
    lang_str = ''
    total_bytes = sum(langs.values())
    for lang in list(langs.keys()):
        lang_str += lang_fmt.replace('$name', lang).replace('$percent', str(round(langs[lang]/total_bytes, 2) * 100)) + '\n'

    contents = update('LANGUAGES', lang_str, contents)
    contents = re.sub(f'<!--S:LANGUAGES-->(.|\n)*<!--E:LANGUAGES-->',
                      f'<!--S:LANGUAGES-->{lang_str}<!--E:LANGUAGES-->',
                      contents)

    if os.getenv('MT_TOKEN') != '':
        mt_headers = {
            'Authorization': f'ApeKey {os.getenv('MT_TOKEN')}'
        }
        mt_res = requests.get('https://api.monkeytype.com/results?limit=10', headers=mt_headers)
        if not mt_res.ok:
            print(mt_res.status_code)
            print(mt_res.text)
            sys.exit(1)

        mt_data = mt_res.json()['data']
        
        mt_wpm = 0
        mt_acc = 0
        for test in mt_data:
            mt_wpm += test['wpm']
            mt_acc += test['acc']

        mt_wpm /= len(mt_data)
        mt_acc /= len(mt_data)

        contents = update('MT_WPM',      round(mt_wpm, 1), contents)
        contents = update('MT_ACCURACY', round(mt_acc, 1), contents)

        mt_res = requests.get(f'https://api.monkeytype.com/users/{mt_data[0]['name']}/profile', headers=mt_headers)
        if not mt_res.ok:
            print(mt_res.status_code)
            print(mt_res.text)
            sys.exit(1)

        mt_data = mt_res.json()['data']
        contents = update('MT_XP',     mt_data['xp'],     contents)
        contents = update('MT_STREAK', mt_data['streak'], contents)

    with open(readme_file, 'w') as f:
        f.write(contents)

