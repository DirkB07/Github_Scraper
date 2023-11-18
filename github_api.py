from flask import Flask, Response, request, jsonify
from github_scraper import get_user_info, get_user_repos
import json, os

app = Flask(__name__)
app.config.update({
    "JSON_SORT_KEYS": False
})

# Endpoint to get user information
@app.route('/users/<string:username>', methods=['GET'])
def get_user(username):
    user_info, user_type = get_user_info(username)
    if user_info is None:
        response_data = {
        'message': "Not Found",
        'documentation_url': "https://docs.github.com/rest/users/users#get-a-user"
    }
        response_json = json.dumps(response_data, indent=2, separators=(',', ': ')) + '\n'
        response = Response(response_json, content_type='application/json')
        response.status_code = 404
        return response
    
    user_info_json = json.dumps(user_info, indent=2, separators=(',', ': ')) + '\n'
    response = Response(user_info_json, content_type='application/json')
    
    return response

# Endpoint to get user repositories
@app.route('/users/<string:username>/repos', methods=['GET'])
def get_user_repositories(username):
    user_info, user_type = get_user_info(username)
    if user_info is None:
        response_data = {
        'message': "Not Found",
        'documentation_url': "https://docs.github.com/rest/repos/repos#list-repositories-for-a-user"
    }
        response_json = json.dumps(response_data, indent=2, separators=(',', ': ')) + '\n'
        response = Response(response_json, content_type='application/json')
        response.status_code = 404
        return response
    
    sort_param = request.args.get('sort', 'full_name')  # Get 'sort' query parameter or use 'created' as default
    direction_param = request.args.get('direction')  # Get 'direction' query parameter
    
    if sort_param not in ['full_name', 'pushed']:
        return jsonify({"error": "Invalid sort parameter"}), 400
    
    if direction_param not in ['asc', 'desc']:
        direction_param = 'asc' if sort_param == 'full_name' else 'desc'

    per_page_param = int(request.args.get('per_page', 30))
    page_param = int(request.args.get('page', 1))
    
    repos = get_user_repos(username, user_type)

    if sort_param == "full_name":
        sorting_key = lambda repo: repo.get('full_name', '').lower()
    elif sort_param == "pushed":
        sorting_key = lambda repo: repo.get('pushed_at', '')

    sorted_repos = sorted(repos, key=sorting_key, reverse=(direction_param == 'desc'))

    start_index = (page_param - 1) * per_page_param
    end_index = start_index + per_page_param
    paged_repos = sorted_repos[start_index:end_index]

    repos_json = json.dumps(paged_repos, indent=2, separators=(',', ': ')) + '\n'
    response = Response(repos_json, content_type='application/json')
    
    return response

if __name__ == '__main__':
    app.run(port=int(os.environ.get('GITHUB_API_PORT', 5000)))