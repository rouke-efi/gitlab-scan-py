import unittest
from unittest.mock import patch, Mock
import os
import json
from your_script_name import GitLabTerraformAnalyzer  # Replace with your actual script name

class TestGitLabTerraformAnalyzer(unittest.TestCase):

    @patch.dict(os.environ, {
        'GITLAB_URL': 'https://gitlab.com',
        'GITLAB_PRIVATE_TOKEN': 'test_token',
        'GITLAB_GROUP_PATH': 'test/group',
        'OUTPUT_DIR': '/tmp/output'
    })
    def setUp(self):
        self.analyzer = GitLabTerraformAnalyzer()

    @patch('gitlab.Gitlab')
    def test_initialization(self, mock_gitlab):
        self.assertEqual(self.analyzer.output_dir, '/tmp/output')
        self.assertEqual(self.analyzer.group_path, 'test/group')
        mock_gitlab.assert_called_once_with('https://gitlab.com', private_token='test_token')

    @patch.dict(os.environ, {})
    def test_initialization_missing_env_vars(self):
        with self.assertRaises(ValueError):
            GitLabTerraformAnalyzer()

    @patch('gitlab.Gitlab')
    def test_get_group_by_path_success(self, mock_gitlab):
        mock_group = Mock()
        mock_gitlab.return_value.groups.get.return_value = mock_group
        
        result = self.analyzer.get_group_by_path('test/group')
        
        self.assertEqual(result, mock_group)
        mock_gitlab.return_value.groups.get.assert_called_once_with('test/group')

    @patch('gitlab.Gitlab')
    def test_get_group_by_path_not_found(self, mock_gitlab):
        mock_gitlab.return_value.groups.get.side_effect = gitlab.exceptions.GitlabGetError()
        
        result = self.analyzer.get_group_by_path('non/existent/group')
        
        self.assertIsNone(result)

    @patch('gitlab.Gitlab')
    def test_search_projects_recursively(self, mock_gitlab):
        mock_group = Mock()
        mock_project = Mock()
        mock_project.name = 'iac-terraform'
        mock_group.projects.list.return_value = [mock_project]
        mock_group.subgroups.list.return_value = []
        
        result = self.analyzer.search_projects_recursively(mock_group)
        
        self.assertEqual(result, [mock_project])
        mock_group.projects.list.assert_called_once_with(search='iac-terraform', all=True)
        mock_group.subgroups.list.assert_called_once_with(all=True)

    @patch('gitlab.Gitlab')
    def test_get_file_content_success(self, mock_gitlab):
        mock_project = Mock()
        mock_file = Mock()
        mock_file.decode.return_value.decode.return_value = '{"version": "v1.0.0"}'
        mock_project.files.get.return_value = mock_file
        
        result = self.analyzer.get_file_content(mock_project, 'version.json')
        
        self.assertEqual(result, '{"version": "v1.0.0"}')
        mock_project.files.get.assert_called_once_with(file_path='version.json', ref='main')

    @patch('gitlab.Gitlab')
    def test_get_file_content_not_found(self, mock_gitlab):
        mock_project = Mock()
        mock_project.files.get.side_effect = gitlab.exceptions.GitlabGetError()
        
        result = self.analyzer.get_file_content(mock_project, 'non_existent.json')
        
        self.assertIsNone(result)

    @patch('gitlab.Gitlab')
    @patch.object(GitLabTerraformAnalyzer, 'get_file_content')
    def test_analyze_project(self, mock_get_file_content, mock_gitlab):
        mock_project = Mock()
        mock_project.path = 'test-module'
        mock_project.web_url = 'https://gitlab.com/test/test-module'
        mock_get_file_content.return_value = '{"version": "v1.0.0"}'
        
        result = self.analyzer.analyze_project(mock_project)
        
        expected_result = {
            "project_url": "https://gitlab.com/test/test-module",
            "module_name": "test-module",
            "version": "v1.0.0"
        }
        self.assertEqual(result, expected_result)

    @patch('gitlab.Gitlab')
    @patch.object(GitLabTerraformAnalyzer, 'get_group_by_path')
    @patch.object(GitLabTerraformAnalyzer, 'search_projects_recursively')
    @patch.object(GitLabTerraformAnalyzer, 'analyze_project')
    @patch.object(GitLabTerraformAnalyzer, 'write_results')
    def test_run_analysis(self, mock_write_results, mock_analyze_project, 
                          mock_search_projects, mock_get_group, mock_gitlab):
        mock_group = Mock()
        mock_project = Mock()
        mock_get_group.return_value = mock_group
        mock_search_projects.return_value = [mock_project]
        mock_analyze_project.return_value = {"test": "result"}
        
        self.analyzer.run_analysis()
        
        mock_get_group.assert_called_once_with('test/group')
        mock_search_projects.assert_called_once_with(mock_group)
        mock_analyze_project.assert_called_once_with(mock_project)
        mock_write_results.assert_called_once_with([{"test": "result"}])

    @patch('json.dump')
    def test_write_results(self, mock_json_dump):
        results = [{"test": "result"}]
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            self.analyzer.write_results(results)
        
        mock_open.assert_called_once_with('/tmp/output/terraform_modules_analysis.json', 'w')
        mock_json_dump.assert_called_once()

if __name__ == '__main__':
    unittest.main()