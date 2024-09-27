import gitlab
import os
import json
import time
from dotenv import load_dotenv

class GitLabTerraformAnalyzer:
    def __init__(self):
        load_dotenv()
        self.gitlab_url = os.environ.get('GITLAB_URL')
        self.private_token = os.environ.get('GITLAB_GROUP_TOKEN')
        self.output_dir = os.environ.get('OUTPUT_DIR', '/output')
        self.group_path = os.environ.get('GITLAB_GROUP_PATH')

        if not all([self.gitlab_url, self.private_token, self.group_path, self.output_dir]):
            raise ValueError("Missing required environment variables. Please check your .env file.")

        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.private_token)
        self.rate_limit_remaining = None
        self.rate_limit_reset_time = None

    def api_call(self, func, *args, **kwargs):
        while True:
            if self.rate_limit_remaining is not None and self.rate_limit_remaining < 5:
                wait_time = self.rate_limit_reset_time - time.time()
                if wait_time > 0:
                    print(f"Rate limit approaching. Waiting for {wait_time:.2f} seconds.")
                    time.sleep(wait_time + 1)  # Add 1 second buffer

            result = func(*args, **kwargs)

            # Update rate limit info
            if hasattr(self.gl, 'rate_limit'):
                self.rate_limit_remaining = self.gl.rate_limit.remaining
                self.rate_limit_reset_time = self.gl.rate_limit.reset_time

            return result

    def get_group_by_path(self, path):
        try:
            return self.api_call(self.gl.groups.get, path)
        except gitlab.exceptions.GitlabGetError:
            print(f"Error: Group not found at path '{path}'. Please check the path and your permissions.")
            return None

    def search_terraform_subgroups(self, group):
        terraform_subgroups = []
        all_subgroups = self.api_call(group.subgroups.list, all=True)
        
        for subgroup in all_subgroups:
            full_subgroup = self.api_call(self.gl.groups.get, subgroup.id)
            if full_subgroup.name == 'terraform':
                terraform_subgroups.append(full_subgroup)
            terraform_subgroups.extend(self.search_terraform_subgroups(full_subgroup))
        
        return terraform_subgroups

    def search_terraform_projects(self, group):
        terraform_projects = []
        projects = self.api_call(group.projects.list, all=True)
        for project in projects:
            full_project = self.api_call(self.gl.projects.get, project.id)
            if self.project_has_terraform_files(full_project):
                terraform_projects.append(full_project)
        return terraform_projects

    def project_has_terraform_files(self, project):
        try:
            self.api_call(project.files.get, file_path='main.tf', ref='main')
            self.api_call(project.files.get, file_path='version.json', ref='main')
            return True
        except gitlab.exceptions.GitlabGetError:
            return False

    def get_file_content(self, project, file_path):
        try:
            file_content = self.api_call(project.files.get, file_path=file_path, ref='main')
            return file_content.decode().decode('utf-8')
        except gitlab.exceptions.GitlabGetError:
            return None

    def analyze_project(self, project):
        module_name = project.path
        version_json_content = self.get_file_content(project, 'version.json')
        
        result = {
            "project_url": project.web_url,
            "module_name": module_name,
            "version": None
        }
        
        if version_json_content:
            try:
                version_data = json.loads(version_json_content)
                if isinstance(version_data, list):
                    version_data = version_data[0]
                result["version"] = version_data.get("module_version")
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in version.json for project {project.web_url}")
        
        return result

    def run_analysis(self):
        main_group = self.get_group_by_path(self.group_path)
        if not main_group:
            return

        print(f"Searching for 'terraform' subgroups in {main_group.full_path} and all its subgroups...")
        terraform_subgroups = self.search_terraform_subgroups(main_group)
        print(f"Found {len(terraform_subgroups)} 'terraform' subgroups.")

        results = []
        for subgroup in terraform_subgroups:
            print(f"Searching for Terraform projects in subgroup: {subgroup.full_path}")
            projects = self.search_terraform_projects(subgroup)
            print(f"Found {len(projects)} Terraform projects in {subgroup.full_path}")
            for project in projects:
                results.append(self.analyze_project(project))

        self.write_results(results)

    def write_results(self, results):
        os.makedirs(self.output_dir, exist_ok=True)
        output_file = os.path.join(self.output_dir, 'terraform_modules_analysis.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Analysis results have been written to {os.path.abspath(output_file)}")

def main():
    try:
        analyzer = GitLabTerraformAnalyzer()
        analyzer.run_analysis()
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()