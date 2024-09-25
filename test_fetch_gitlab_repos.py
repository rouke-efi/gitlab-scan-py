import unittest
from unittest.mock import Mock, patch
import gitlab
from fetch_gitlab_repos import get_group_by_path, search_projects_recursively  # Replace with your actual script name

class TestGitLabProjectSearch(unittest.TestCase):

    def setUp(self):
        # Create a mock GitLab instance
        self.gl_mock = Mock(spec=gitlab.Gitlab)
        # Create a mock Groups manager
        self.gl_mock.groups = Mock(spec=gitlab.v4.objects.GroupManager)
        # Create a mock Group
        self.group_mock = Mock(spec=gitlab.v4.objects.Group)
        self.group_mock.id = 1  # Add id attribute to group mock
        # Create a mock Project
        self.project_mock = Mock(spec=gitlab.v4.objects.Project)
        self.project_mock.id = 100  # Add id attribute to project mock

    def test_get_group_by_path_success(self):
        self.gl_mock.groups.get.return_value = self.group_mock
        with patch('fetch_gitlab_repos.gl', self.gl_mock):  # Replace with your actual script name
            result = get_group_by_path('test/path')
        self.assertEqual(result, self.group_mock)

    def test_get_group_by_path_not_found(self):
        self.gl_mock.groups.get.side_effect = gitlab.exceptions.GitlabGetError()
        with patch('fetch_gitlab_repos.gl', self.gl_mock):  # Replace with your actual script name
            result = get_group_by_path('non/existent/path')
        self.assertIsNone(result)

    def test_search_projects_recursively_no_projects(self):
        self.group_mock.projects = Mock()
        self.group_mock.projects.list.return_value = []
        self.group_mock.subgroups = Mock()
        self.group_mock.subgroups.list.return_value = []
        
        with patch('fetch_gitlab_repos.gl', self.gl_mock):  # Replace with your actual script name
            result = search_projects_recursively(self.group_mock)
        
        self.assertEqual(result, [])
        self.group_mock.projects.list.assert_called_once_with(search='iac-terraform', all=True)
        self.group_mock.subgroups.list.assert_called_once_with(all=True)

    def test_search_projects_recursively_with_projects(self):
        self.project_mock.name = 'iac-terraform'
        self.group_mock.projects = Mock()
        self.group_mock.projects.list.return_value = [self.project_mock]
        self.group_mock.subgroups = Mock()
        self.group_mock.subgroups.list.return_value = []
        
        with patch('fetch_gitlab_repos.gl', self.gl_mock):  # Replace with your actual script name
            result = search_projects_recursively(self.group_mock)
        
        self.assertEqual(result, [self.project_mock])
        self.group_mock.projects.list.assert_called_once_with(search='iac-terraform', all=True)
        self.group_mock.subgroups.list.assert_called_once_with(all=True)

    def test_search_projects_recursively_with_subgroups(self):
        self.project_mock.name = 'iac-terraform'
        subgroup_mock = Mock(spec=gitlab.v4.objects.Group)
        subgroup_mock.id = 2  # Add id attribute to subgroup mock
        subgroup_mock.projects = Mock()
        subgroup_mock.projects.list.return_value = [self.project_mock]
        subgroup_mock.subgroups = Mock()
        subgroup_mock.subgroups.list.return_value = []
        
        self.group_mock.projects = Mock()
        self.group_mock.projects.list.return_value = []
        self.group_mock.subgroups = Mock()
        self.group_mock.subgroups.list.return_value = [subgroup_mock]
        self.gl_mock.groups.get.return_value = subgroup_mock
        
        with patch('fetch_gitlab_repos.gl', self.gl_mock):  # Replace with your actual script name
            result = search_projects_recursively(self.group_mock)
        
        self.assertEqual(result, [self.project_mock])
        self.group_mock.projects.list.assert_called_once_with(search='iac-terraform', all=True)
        self.group_mock.subgroups.list.assert_called_once_with(all=True)
        subgroup_mock.projects.list.assert_called_once_with(search='iac-terraform', all=True)

if __name__ == '__main__':
    unittest.main()