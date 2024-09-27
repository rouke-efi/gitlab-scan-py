import unittest
from unittest.mock import patch, Mock, MagicMock
import os
import json
import gitlab
from gl_terraform_analyzer import GitLabTerraformAnalyzer  # Replace with your actual script name

class TestGitLabTerraformAnalyzer(unittest.TestCase):

    @patch.dict(os.environ, {
        'GITLAB_URL': 'https://gitlab.com',
        'GITLAB_GROUP_TOKEN': 'test_token',
        'GITLAB_GROUP_PATH': 'test/group',
        'OUTPUT_DIR': '/tmp/output'
    })
    def setUp(self):
        # Create a more detailed mock structure
        self.gl_mock = Mock(spec=gitlab.Gitlab)
        self.gl_mock.groups = Mock()
        self.gl_mock.groups.get = Mock()
        self.gl_mock.projects = Mock()
        self.gl_mock.projects.get = Mock()

        with patch('gitlab.Gitlab', return_value=self.gl_mock):
            self.analyzer = GitLabTerraformAnalyzer()

    def test_initialization(self):
        self.assertEqual(self.analyzer.gitlab_url, 'https://gitlab.com')
        self.assertEqual(self.analyzer.private_token, 'test_token')
        self.assertEqual(self.analyzer.group_path, 'test/group')
        self.assertEqual(self.analyzer.output_dir, '/tmp/output')
        self.assertIsInstance(self.analyzer.gl, Mock)

    @patch.dict(os.environ, {})
    def test_initialization_missing_env_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                GitLabTerraformAnalyzer()

    def test_get_group_by_path_success(self):
        mock_group = Mock()
        self.gl_mock.groups.get.return_value = mock_group
        
        result = self.analyzer.get_group_by_path('test/group')
        
        self.assertEqual(result, mock_group)
        self.gl_mock.groups.get.assert_called_once_with('test/group')

    def test_get_group_by_path_not_found(self):
        self.gl_mock.groups.get.side_effect = gitlab.exceptions.GitlabGetError()
        
        result = self.analyzer.get_group_by_path('non/existent/group')
        
        self.assertIsNone(result)

#    def test_search_terraform_subgroups(self):
#        mock_group = Mock()
#        mock_subgroup1 = Mock(name='terraform', id=1)
#        mock_subgroup2 = Mock(name='not_terraform', id=2)
#        mock_subgroup3 = Mock(name='terraform', id=3)
#        
#        # Mock the subgroups.list method to return a list
#        mock_group.subgroups.list.return_value = [mock_subgroup1, mock_subgroup2, mock_subgroup3]
#        
#        # Mock the gl.groups.get method
#        self.gl_mock.groups.get.side_effect = [mock_subgroup1, mock_subgroup2, mock_subgroup3]
#        
#        # Mock the recursive call
#        with patch.object(self.analyzer, 'search_terraform_subgroups') as mock_recursive:
#            mock_recursive.return_value = [mock_subgroup3]
#            
#            result = self.analyzer.search_terraform_subgroups(mock_group)
#        
#        self.assertEqual(result, [mock_subgroup1, mock_subgroup3])
#        mock_group.subgroups.list.assert_called_once_with(all=True)
#        self.gl_mock.groups.get.assert_any_call(1)
#        self.gl_mock.groups.get.assert_any_call(2)

    def test_search_terraform_projects(self):
        mock_group = Mock()
        mock_project1 = Mock(id=1)
        mock_project2 = Mock(id=2)
        mock_group.projects.list.return_value = [mock_project1, mock_project2]
        self.gl_mock.projects.get.side_effect = [mock_project1, mock_project2]
        
        with patch.object(self.analyzer, 'project_has_terraform_files') as mock_has_files:
            mock_has_files.side_effect = [True, False]
            result = self.analyzer.search_terraform_projects(mock_group)
        
        self.assertEqual(result, [mock_project1])
        mock_group.projects.list.assert_called_once_with(all=True)

    def test_project_has_terraform_files(self):
        mock_project = Mock()
        mock_project.files = Mock()
        mock_project.files.get.side_effect = [Mock(), Mock()]
        
        result = self.analyzer.project_has_terraform_files(mock_project)
        
        self.assertTrue(result)
        mock_project.files.get.assert_any_call(file_path='main.tf', ref='main')
        mock_project.files.get.assert_any_call(file_path='version.json', ref='main')

    @patch('time.sleep')
    def test_api_call_rate_limit(self, mock_sleep):
        self.analyzer.rate_limit_remaining = 3
        self.analyzer.rate_limit_reset_time = 100
        mock_func = Mock()
        mock_func.return_value = "test_result"
        
        with patch('time.time', return_value=50):
            result = self.analyzer.api_call(mock_func, "arg1", kwarg1="kwarg1")
        
        mock_sleep.assert_called_once_with(51)
        self.assertEqual(result, "test_result")

    # Add more test methods as needed

if __name__ == '__main__':
    unittest.main()