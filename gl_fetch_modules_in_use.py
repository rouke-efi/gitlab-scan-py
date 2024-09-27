import gitlab
import os
import json
import re
import time
from dotenv import load_dotenv

class GitLabTerraformModuleAnalyzer:
    def __init__(self):
        load_dotenv()
        self.gitlab_url = os.environ.get('GITLAB_URL')
        self.private_token = os.environ.get('GITLAB_GROUP_TOKEN')
        self.group_path = os.environ.get('GITLAB_GROUP_PATH')
        self.output_dir = os.environ.get('OUTPUT_DIR', '/output')

        if not all([self.gitlab_url, self.private_token, self.group_path]):
            raise ValueError("Missing required environment variables. Please check your .env file.")

        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.private_token)
        self.rate_limit_remaining = None
        self.rate_limit_reset_time = None

    def api_call(self, func, *args, **kwargs):
        while True:
            if self.rate_limit_remaining is not None and self.rate_limit_remaining < 5:
                wait_time = max(self.rate_limit_reset_time - time.time(), 0)
                if wait_time > 0:
                    print(f"Rate limit approaching. Waiting for {wait_time:.2f} seconds.")
                    time.sleep(wait_time + 1)  # Add 1 second buffer

            try:
                result = func(*args, **kwargs)

                # Update rate limit info
                if hasattr(self.gl, 'rate_limit'):
                    self.rate_limit_remaining = self.gl.rate_limit.remaining
                    self.rate_limit_reset_time = self.gl.rate_limit.reset_time

                return result
            except gitlab.exceptions.GitlabRateLimitError as e:
                print(f"Rate limit exceeded. Waiting for {e.retry_after} seconds.")
                time.sleep(e.retry_after)

    def search_iac_terraform_projects(self, group):
        iac_terraform_projects = []
        projects = self.api_call(group.projects.list, all=True)
        for project in projects:
            if project.name == 'iac-terraform':
                full_project = self.api_call(self.gl.projects.get, project.id)
                iac_terraform_projects.append(full_project)

        subgroups = self.api_call(group.subgroups.list, all=True)
        for subgroup in subgroups:
            full_subgroup = self.api_call(self.gl.groups.get, subgroup.id)
            iac_terraform_projects.extend(self.search_iac_terraform_projects(full_subgroup))

        return iac_terraform_projects

    def clean_source_url(self, source):
        # Remove 'git::' prefix if present
        source = re.sub(r'^git::', '', source)
        # Remove '.git' suffix if present
        source = re.sub(r'\.git(?:\?ref=.*)?$', '', source)
        return source

    def get_module_versions(self, project):
        module_versions = {}
        try:
            main_tf_content = self.api_call(
                project.files.get,
                file_path='main.tf',
                ref='main'
            ).decode().decode('utf-8')
            
            # Updated pattern
            pattern = r'module\s+"([^"]+)"\s+{[^}]*source\s*=\s*"([^"]+?)(?:\?ref=(v?[^"]+))?"'
            
            matches = re.finditer(pattern, main_tf_content, re.DOTALL)
            for match in matches:
                module_name = match.group(1)
                module_source = self.clean_source_url(match.group(2))
                module_version = match.group(3) if match.group(3) else "Not specified"
                module_versions[module_name] = {
                    "source": module_source,
                    "version": module_version
                }

        except gitlab.exceptions.GitlabGetError:
            print(f"Error: Unable to fetch main.tf for project {project.path_with_namespace}")
        except Exception as e:
            print(f"Error processing main.tf for project {project.path_with_namespace}: {str(e)}")

        return module_versions

    def analyze_projects(self):
        main_group = self.api_call(self.gl.groups.get, self.group_path)
        iac_terraform_projects = self.search_iac_terraform_projects(main_group)

        results = []
        for project in iac_terraform_projects:
            module_versions = self.get_module_versions(project)
            results.append({
                "project_path": project.path_with_namespace,
                "modules": module_versions
            })

        return results

    def run_analysis(self):
        results = self.analyze_projects()
        self.write_results(results)

    def write_results(self, results):
        os.makedirs(self.output_dir, exist_ok=True)
        output_file = os.path.join(self.output_dir, 'terraform_module_usage.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Analysis results have been written to {os.path.abspath(output_file)}")

def main():
    try:
        analyzer = GitLabTerraformModuleAnalyzer()
        analyzer.run_analysis()
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()