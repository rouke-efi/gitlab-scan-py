import gitlab
import os
import json
from dotenv import load_dotenv

class GitLabTerraformAnalyzer:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        gitlab_url = os.environ.get('GITLAB_URL')
        private_token = os.environ.get('GITLAB_PRIVATE_TOKEN')
        self.output_dir = os.environ.get('OUTPUT_DIR', '/output')
        self.group_path = os.environ.get('GROUP_NAME')

        if not all([gitlab_url, private_token, self.group_path]):
            raise ValueError("Missing required environment variables. Please check your .env file.")

        self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token)

    def get_group_by_path(self, path):
        try:
            return self.gl.groups.get(path)
        except gitlab.exceptions.GitlabGetError:
            print(f"Error: Group not found at path '{path}'. Please check the path and your permissions.")
            return None

    def search_projects_recursively(self, group, target_name='terraform'):
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

    def run_analysis(self):
        group = self.get_group_by_path(self.group_path)
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