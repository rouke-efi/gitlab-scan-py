import gitlab
import re
import os
import logging
import argparse

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



class GitLabTerraformAnalyzer:
    def __init__(self, gitlab_url, private_token, output_dir):
        self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token)
        self.output_dir = output_dir

    def get_group_by_path(self, path):
        try:
            return self.gl.groups.get(path)
        except gitlab.exceptions.GitlabGetError:
            print(f"Error: Group not found at path '{path}'. Please check the path and your permissions.")
            return None

    def search_projects_recursively(self, group, target_name='iac-terraform'):
        projects = []
        group_projects = group.projects.list(search=target_name, all=True)
        projects.extend([p for p in group_projects if p.name == target_name])
        
        subgroups = group.subgroups.list(all=True)
        for subgroup in subgroups:
            full_subgroup = self.gl.groups.get(subgroup.id)
            projects.extend(self.search_projects_recursively(full_subgroup, target_name))
        
        return projects

    def get_file_content(self, project, file_path):
        try:
            file_content = project.files.get(file_path=file_path, ref='main')
            return file_content.decode().decode('utf-8')
        except gitlab.exceptions.GitlabGetError:
            return None

    def analyze_project(self, project):
        module_name = project.path  # Using project path as module name
        version_json_content = self.get_file_content(project, 'version.json')
        
        result = {
            "project_url": project.web_url,
            "module_name": module_name,
            "version": None
        }
        
        if version_json_content:
            try:
                version_data = json.loads(version_json_content)
                # Handle both possible JSON structures
                if isinstance(version_data, list):
                    version_data = version_data[0]
                result["version"] = version_data.get("version")
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in version.json for project {project.web_url}")
        
        return result

    def run_analysis(self, group_path):
        group = self.get_group_by_path(group_path)
        if not group:
            return

        print(f"Searching for 'iac-terraform' projects in {group.full_path} and all its subgroups...")
        projects = self.search_projects_recursively(group)
        print(f"Found {len(projects)} 'iac-terraform' projects.")

        results = []
        for project in projects:
            results.append(self.analyze_project(project))

        self.write_results(results)

    def write_results(self, results):
        output_file = os.path.join(self.output_dir, 'terraform_modules_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Analysis results have been written to {os.path.abspath(output_file)}")

def main():
    parser = argparse.ArgumentParser(description="Analyze Terraform modules in GitLab")
    parser.add_argument("--gitlab-url", required=True, help="GitLab instance URL")
    parser.add_argument("--private-token", required=True, help="GitLab private token")
    parser.add_argument("--group-path", required=True, help="Path to the GitLab group to analyze")
    parser.add_argument("--output-dir", required=True, help="Directory to store output files")
    
    args = parser.parse_args()

    analyzer = GitLabTerraformAnalyzer(args.gitlab_url, args.private_token, args.output_dir)
    analyzer.run_analysis(args.group_path)

if __name__ == "__main__":
    main()