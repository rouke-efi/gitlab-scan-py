import requests
import httpx
import gitlab
import os
from collections import defaultdict

# Replace with your GitLab instance URL and personal access token
gitlab_url = os.environ.get('GITLAB_URL')
private_token = os.environ.get('GITLAB_GROUP_TOKEN')

# Replace with your group ID
group_id = os.environ.get('GROUP_ID')
group_name = os.environ.get('GROUP_NAME')

def get_projects_api():
    headers = {
       "PRIVATE-TOKEN": private_token,
       "User-Agent": "curl/7.68.0"
   }

    # Get all subgroups recursively
    subgroups_url = f"{gitlab_url}/api/v4/groups/{group_name}/subgroups?all_available=true&include_descendants=true"
    print(f"\nSUBGROUPS: {subgroups_url}")
    with httpx.Client() as client:
       response = client.get(subgroups_url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")
    subgroups = response.json()

    # Find all projects named "iac-terraform"
    iac_projects = []
    for subgroup in subgroups:
        projects_url = f"{gitlab_url}/api/v4/groups/{subgroup['id']}/projects?search=iac-terraform"
        response = requests.get(projects_url, headers=headers)
        projects = response.json()
        iac_projects.extend(projects)

    return iac_projects

def get_projects_library():
    gl = gitlab.Gitlab(gitlab_url, private_token=private_token)
    group = gl.groups.get(group_id)

    def get_all_subgroups(group):
        subgroups = []
        page = 1
        while True:
            new_subgroups = group.subgroups.list(all=True, include_descendants=True, page=page, per_page=100)
            if not new_subgroups:
                break
            subgroups.extend(new_subgroups)
            page += 1
        return subgroups

    subgroups = get_all_subgroups(group)

    iac_projects = []
    for subgroup in subgroups:
        projects = subgroup.projects.list(search='iac-terraform')
        iac_projects.extend(projects)

    return iac_projects

def compare_results(api_projects, library_projects):
    api_paths = set(project['path_with_namespace'] for project in api_projects)
    library_paths = set(project.path_with_namespace for project in library_projects)

    print("Projects found by both methods:")
    for path in api_paths.intersection(library_paths):
        print(f"  {path}")

    print("\nProjects found only by API call:")
    for path in api_paths - library_paths:
        print(f"  {path}")

    print("\nProjects found only by GitLab library:")
    for path in library_paths - api_paths:
        print(f"  {path}")

if __name__ == "__main__":
    print("Fetching projects using direct API call...")
    api_projects = get_projects_api()
    print(f"Found {len(api_projects)} projects\n")

    print("Fetching projects using GitLab Python library...")
    library_projects = get_projects_library()
    print(f"Found {len(library_projects)} projects\n")

    print("Comparing results:")
    compare_results(api_projects, library_projects)

    # Print GitLab library version
    gl = gitlab.Gitlab(gitlab_url, private_token=private_token)
    print(f"\nGitLab Python library version: {gitlab.__version__}")
    print(f"GitLab server version: {gl.version()}")