import requests, json
from bs4 import BeautifulSoup

# Base URL for GitHub
BASE_URL = 'https://github.com/'
USER_ID = 0

# Function to get user information
def get_user_info(username):
    url = BASE_URL + username
    url_search_page = f"https://github.com/search?q="+ username + "&type=users"

    response = requests.get(url)
    response_search = requests.get(url_search_page)
    
    if response.status_code == 200 & response_search.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        json_data = response_search.json()

        company_element = soup.find('span', class_='p-org')

        if company_element:
            company_name = company_element.text.strip()
        else:
            company_name = None

        type = 'User' if soup.find('a', {'data-tab-item': 'stars'}) else 'Organization'

        if type == "User":
            card = soup.find('ul', class_='vcard-details')
            blog_element = card.find('a', rel='nofollow me')

            if blog_element:
                blog = blog_element.text.strip()
            else:
                blog = None
        else:
            blog_element = soup.find('a', rel="nofollow", itemprop="url")

            if blog_element:
                blog = blog_element.text.strip()
            else:
                blog = None

        if type == "User":
            user_id_tag = soup.find('meta', attrs={'name': 'octolytics-dimension-user_id'})
            USER_ID = int(user_id_tag['content']) if user_id_tag is not None and 'content' in user_id_tag.attrs else None
        else:
            hovercard_tag = soup.find('meta', attrs={'name': 'hovercard-subject-tag'})
            if hovercard_tag:
                content = hovercard_tag['content']
                organization_id = int(content.split(':')[1])
                USER_ID = organization_id


        if type == 'User':
            followers = soup.findAll('span', class_='text-bold color-fg-default')
            if len(followers) > 1 and followers[1].text:
                followers = int(followers[1].text.strip())
            else:
                followers = 0
        else:
            followers = 0

        try:
            username = json_data["payload"]["results"][0]["hl_login"].replace("<em>", "").replace("</em>", "")
        except KeyError:
            username = username

        if type == 'User':
            user_info = {
                'login': username if username else None,
                'id': USER_ID if USER_ID else None,
                'avatar_url': "https://avatars.githubusercontent.com/u/"+ str(USER_ID) + "?v=4",
                'url': "https://api.github.com/users/" + username,
                'html_url': url if url else None,
                'type': type,
                'name': soup.find('span', class_='p-name').text.strip() if soup.find('span', class_='p-name') else None,
                'company': company_name if company_name else None,
                'blog': blog,
                'location': soup.find('span', class_='p-label').text.strip() if soup.find('span', class_='p-label') else None,
                'bio': soup.find('div', class_='user-profile-bio').text.strip() if soup.find('div', class_='user-profile-bio') and soup.find('div', class_='user-profile-bio').text else None,
                'twitter_username': soup.find('a', href=lambda href: href and href.startswith('https://twitter.com/')).text.strip()[1:] if soup.find('a', href=lambda href: href and href.startswith('https://twitter.com/')) else None,
                'public_repos': int(soup.find('span', class_='Counter').text.strip()) if soup.find('span', class_='Counter') and soup.find('span', class_='Counter').text.strip() else 0,
                'followers': int(json_data["payload"]["results"][0]["followers"]),
                'following': followers

            } 
        else:
            user_info = {
                'login': username if username else None,
                'id': USER_ID if USER_ID else None,
                'avatar_url': "https://avatars.githubusercontent.com/u/"+ str(USER_ID) + "?v=4",
                'url': "https://api.github.com/users/" + username,
                'html_url': url if url else None,
                'type': type,
                'name': soup.find('h1', class_='h2 lh-condensed').text.strip() if soup.find('h1', class_='h2 lh-condensed') else None,
                'company': company_name if company_name else None,
                'blog': blog,
                'location': soup.find('span', itemprop='location').get_text(strip=True) if soup.find('span', itemprop='location') else None,
                'bio': json_data["payload"]["results"][0]["profile_bio"],
                'twitter_username': soup.find('a', class_='Link--primary', text=True, href=True).text.strip() if soup.find('a', class_='Link--primary', text=True, href=True) else None,
                'public_repos': int(json_data["payload"]["results"][0]["repos"]),
                'followers': int(json_data["payload"]["results"][0]["followers"]),
                'following': 0,
            }

        if type == None:
            type = 'User'
        
        return user_info, type
    return None, None

# Function to get user repositories
def get_user_repos(username, type):
    repos = []
    page = 1 

    while True:

        if type == 'User':
            url = BASE_URL + username + '?page=' + str(page) + '&tab=repositories'
        else:
            url = BASE_URL + 'orgs/' + username + '/repositories' + '?page=' + str(page)

        response = requests.get(url)
        if response.status_code == 200:

            soup = BeautifulSoup(response.text, 'html.parser')

            #this if user
            if type == 'User':
                repo_elements = soup.find_all('li', itemprop='owns')
            #or if it is organization
            else:
                repo_elements = soup.find_all('div', itemprop='owns')

            if not repo_elements:
                break
            
            for repo_element in repo_elements:

                repo_name = repo_element.find('a', itemprop='name codeRepository').text.strip()

                #get the extra info here first
                additional_info = get_repo_info(username, repo_name)

                #now i should be able top use the variables i got in get repo info
                if type == 'User':
                    owner_id = int(soup.find('meta', {'name': 'octolytics-dimension-user_id'})['content'])
                else:
                    owner_id = int(soup.find('meta', attrs={'name': 'hovercard-subject-tag'})['content'].split(":")[1])

                

                repo_info = {
                    'id': additional_info.get('repo_id'),
                    'name': repo_name,
                    'full_name': f"{username}/{repo_element.find('a', itemprop='name codeRepository').text.strip()}" if repo_element.find('a', itemprop='name codeRepository') else None,
                    'owner': {
                        'login': username,
                        'id': owner_id
                    },
                    'private': True if repo_element.find('span', class_='Label--secondary') and repo_element.find('span', class_='Label--secondary').text.strip() == 'Private' else False,
                    'html_url': 'https://github.com/' + username + "/" + repo_name,
                    'description': repo_element.find('p', itemprop='description').text.strip() if repo_element.find('p', itemprop='description') else None,
                    'fork': additional_info.get('fork'),
                    'url': "https://api.github.com/repos/" + username + "/" + repo_name,
                    'homepage': additional_info.get('homepage'),
                    'language': repo_element.find('span', itemprop='programmingLanguage').text.strip() if repo_element.find('span', itemprop='programmingLanguage') else None,
                    'forks_count': int(repo_element.find('a', href=lambda href: href and '/forks' in href).text.strip().replace(',', '')) if repo_element.find('a', href=lambda href: href and '/forks' in href) else 0,
                    'stargazers_count': int(repo_element.find('a', href=lambda href: href and 'stargazers' in href).text.strip().replace(',', '')) if repo_element.find('a', href=lambda href: href and 'stargazers' in href) else 0,
                    'watchers_count': int(repo_element.find('a', href=lambda href: href and 'stargazers' in href).text.strip().replace(',', '')) if repo_element.find('a', href=lambda href: href and 'stargazers' in href) else 0,
                    'default_branch': additional_info.get('default_branch'),
                    'open_issues_count': additional_info.get('open_issues_count'),
                    'topics': additional_info.get('topics'),
                    'has_issues': additional_info.get('has_issues'),
                    'has_projects': additional_info.get('has_projects'),
                    'has_discussions': additional_info.get('has_discussions'),
                    'archived': additional_info.get('archived'),
                    'pushed_at': repo_element.find('relative-time')['datetime'].strip() if repo_element.find('relative-time') else None
                }
                repos.append(repo_info)

            page += 1
        else:
            break 

    return repos


# Function to get user repositories info
def get_repo_info(username, repo_name):

    url = BASE_URL + username + '/' + repo_name
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        topics = [

        ]

        topics_tags = soup.find_all('a', class_='topic-tag')
        for topic_tag in topics_tags:
            topic = topic_tag.text.strip()
            topics.append(topic)

        summary_element = soup.find('summary', title='Switch branches or tags')
        
        if summary_element:
            branch = summary_element.find('span', class_='css-truncate-target').text.strip()
        else:
            branch = ""


        fork_value = soup.find('meta', attrs={'name': 'octolytics-dimension-repository_is_fork'})['content']

        if fork_value == 'true':
            fork_bool = True
        else:
            fork_bool = False

        span_element = soup.find('span', class_='flex-auto min-width-0 css-truncate css-truncate-target width-fit')

        if span_element:
            link_element = span_element.find('a', class_='text-bold')
            if link_element:
                link_href = link_element['href']
            else:
                link_href = None
        else:
            link_href = None

        issues_count = int(soup.find('span', id='issues-repo-tab-count')['title'].replace(',', '')) if soup.find('span', id='issues-repo-tab-count') else 0
        
        return {
            'fork': fork_bool,
            'repo_id': int(soup.find('meta', {'name': 'hovercard-subject-tag'})['content'].split(':')[1]) if soup.find('meta', {'name': 'hovercard-subject-tag'}) else None,
            'homepage': link_href if link_href else None,
            'default_branch': branch,
            'open_issues_count': issues_count,
            'topics': topics,
            'has_issues': True if soup.find('a', id='issues-tab', class_='UnderlineNav-item') else False,
            'has_projects': True if soup.find('a', id='projects-tab', class_='UnderlineNav-item') else False,
            'has_discussions': True if soup.find('a', id='discussions-tab', class_='UnderlineNav-item') else False,
            'archived': True if soup.find('div', class_='flash flash-warn flash-full border-top-0 text-center text-bold py-2') else False
        }

    return None