import gitlab
import re
import os
import logging

# Configure logging for the 'gitlab' logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('gitlab')
logger.setLevel(logging.DEBUG)
gitlab_url = os.environ.get('GITLAB_URL')
private_token = os.environ.get('GITLAB_GROUP_TOKEN')
# Optionally, configure logging for 'urllib3' to see HTTP requests
logging.getLogger('urllib3').setLevel(logging.DEBUG)
terraform_sp_path = os.environ.get('GROUP_NAME')
gl = gitlab.Gitlab(gitlab_url, private_token=private_token)

def get_group_by_path(path):
    try:
        return gl.groups.get(path)
    except gitlab.exceptions.GitlabGetError:
        print(f"Error: Group not found at path '{path}'. Please check the path and your permissions.")
        return None

def search_projects_recursively(group, target_name='iac-terraform'):
    projects = []
    
    # Search for projects in the current group
    group_projects = group.projects.list(search=target_name, all=True)
    projects.extend([p for p in group_projects if p.name == target_name])
    
    # Recursively search in subgroups
    subgroups = group.subgroups.list(all=True)
    for subgroup in subgroups:
        # We need to get the full group object to access its projects
        full_subgroup = gl.groups.get(subgroup.id)
        projects.extend(search_projects_recursively(full_subgroup, target_name))
    
    return projects

def main():
    print(f"Attempting to access group at path: {terraform_sp_path}")
    terraform_sp_group = get_group_by_path(terraform_sp_path)
    if not terraform_sp_group:
        return

    print(f"Successfully accessed group: {terraform_sp_group.full_path}")
    print(f"Searching for 'iac-terraform' projects in {terraform_sp_group.full_path} and all its subgroups...")
    
    iac_projects = search_projects_recursively(terraform_sp_group)

    print(f"\nFound {len(iac_projects)} 'iac-terraform' projects:")
    for project in iac_projects:
        print(f"Project: {project.name}, Path: {project.path_with_namespace}")

    print(f"\nGitLab Python library version: {gitlab.__version__}")
    print(f"GitLab server version: {gl.version()}")

if __name__ == "__main__":
    main()