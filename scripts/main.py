import json
import sys

import requests

if __name__ == '__main__':
    readme_file = sys.argv[1]
    if readme_file == '':
        readme_file = 'README.md'
    token = sys.argv[2]
    if token == '':
        sys.exit(1)

    headers = {
        'Authorization': f'bearer {token}'
    }

    req = '''
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

    res = requests.post('https://api.github.com/graphql', json.dumps({ 'query': req }), headers=headers)
    if not res.ok:
        print(res.status_code)
        print(res.text)
        sys.exit(1)

    data = res.json()['data']['viewer']
    print(data)

