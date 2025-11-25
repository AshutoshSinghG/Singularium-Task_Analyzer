"""
Comprehensive test suite for Smart Task Analyzer backend.
Tests scoring algorithm, API endpoints, and edge cases.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from .scoring import (
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score,
    calculate_dependency_score,
    calculate_final_score,
    detect_circular_dependencies
)
from .utils import validate_task_data, add_task_ids


class ScoreCalculationTests(TestCase):
    """Test individual scoring functions"""
    
    def test_urgency_score_overdue(self):
        """Test that overdue tasks get maximum urgency"""
        past_date = date.today() - timedelta(days=5)
        score, explanation = calculate_urgency_score(past_date)
        self.assertEqual(score, 10.0)
        self.assertIn('OVERDUE', explanation)
    
    def test_urgency_score_today(self):
        """Test that tasks due today get very high urgency"""
        today = date.today()
        score, explanation = calculate_urgency_score(today)
        self.assertEqual(score, 9.0)
        self.assertIn('TODAY', explanation)
    
    def test_urgency_score_future(self):
        """Test that future tasks get decreasing urgency"""
        future_date = date.today() + timedelta(days=1)
        score1, _ = calculate_urgency_score(future_date)
        
        far_future = date.today() + timedelta(days=30)
        score2, _ = calculate_urgency_score(far_future)
        
        self.assertGreater(score1, score2)
    
    def test_importance_score_valid(self):
        """Test importance score with valid values"""
        score, explanation = calculate_importance_score(8)
        self.assertEqual(score, 8.0)
        self.assertIn('importance', explanation.lower())
    
    def test_importance_score_invalid(self):
        """Test importance score with invalid values"""
        score, explanation = calculate_importance_score(15)
        self.assertEqual(score, 5.0)  # Default
        self.assertIn('Invalid', explanation)
    
    def test_effort_score_quick_win(self):
        """Test that quick tasks get high effort score"""
        score, explanation = calculate_effort_score(0.5)
        self.assertEqual(score, 10.0)
        self.assertIn('Quick win', explanation)
    
    def test_effort_score_large_task(self):
        """Test that large tasks get low effort score"""
        score1, _ = calculate_effort_score(1.0)
        score2, _ = calculate_effort_score(10.0)
        self.assertGreater(score1, score2)
    
    def test_dependency_score_no_blockers(self):
        """Test dependency score when task blocks nothing"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]}
        ]
        score, explanation = calculate_dependency_score(2, tasks)
        self.assertEqual(score, 3.0)
        self.assertIn('No tasks', explanation)
    
    def test_dependency_score_blocks_tasks(self):
        """Test dependency score when task blocks others"""
        tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': []},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [1]}
        ]
        score, explanation = calculate_dependency_score(1, tasks)
        self.assertGreater(score, 6.0)
        self.assertIn('Blocks', explanation)


class CircularDependencyTests(TestCase):
    """Test circular dependency detection"""
    
    def test_no_circular_dependencies(self):
        """Test tasks with no cycles"""
        tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': []},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [2]}
        ]
        has_cycles, cycles = detect_circular_dependencies(tasks)
        self.assertFalse(has_cycles)
        self.assertEqual(len(cycles), 0)
    
    def test_simple_circular_dependency(self):
        """Test detection of simple cycle (A -> B -> A)"""
        tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': [2]},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]}
        ]
        has_cycles, cycles = detect_circular_dependencies(tasks)
        self.assertTrue(has_cycles)
        self.assertGreater(len(cycles), 0)
    
    def test_complex_circular_dependency(self):
        """Test detection of complex cycle (A -> B -> C -> A)"""
        tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': [3]},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [2]}
        ]
        has_cycles, cycles = detect_circular_dependencies(tasks)
        self.assertTrue(has_cycles)


class AnalyzeEndpointTests(TestCase):
    """Test /api/tasks/analyze/ endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.analyze_url = '/api/tasks/analyze/'
    
    def test_analyze_valid_tasks(self):
        """Test analyzing valid tasks"""
        data = {
            'tasks': [
                {
                    'title': 'Fix login bug',
                    'due_date': str(date.today() + timedelta(days=2)),
                    'estimated_hours': 3,
                    'importance': 8,
                    'dependencies': []
                },
                {
                    'title': 'Update documentation',
                    'due_date': str(date.today() + timedelta(days=7)),
                    'estimated_hours': 1,
                    'importance': 5,
                    'dependencies': []
                }
            ],
            'strategy': 'SMART_BALANCE'
        }
        
        response = self.client.post(self.analyze_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        self.assertIn('strategy', response.data)
        self.assertEqual(len(response.data['tasks']), 2)
        
        # Check that tasks are sorted by score
        tasks = response.data['tasks']
        for i in range(len(tasks) - 1):
            self.assertGreaterEqual(
                tasks[i]['priority_score'],
                tasks[i + 1]['priority_score']
            )
    
    def test_analyze_empty_tasks(self):
        """Test error handling for empty task list"""
        data = {'tasks': []}
        response = self.client.post(self.analyze_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_analyze_missing_fields(self):
        """Test error handling for tasks missing required fields"""
        data = {
            'tasks': [
                {
                    'title': 'Incomplete task',
                    # Missing due_date, estimated_hours, importance
                }
            ]
        }
        response = self.client.post(self.analyze_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_analyze_with_circular_dependencies(self):
        """Test that circular dependencies are detected"""
        data = {
            'tasks': [
                {
                    'id': 1,
                    'title': 'Task A',
                    'due_date': str(date.today() + timedelta(days=5)),
                    'estimated_hours': 2,
                    'importance': 7,
                    'dependencies': [2]
                },
                {
                    'id': 2,
                    'title': 'Task B',
                    'due_date': str(date.today() + timedelta(days=5)),
                    'estimated_hours': 2,
                    'importance': 7,
                    'dependencies': [1]
                }
            ]
        }
        
        response = self.client.post(self.analyze_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_circular_dependencies'])
    
    def test_analyze_different_strategies(self):
        """Test different sorting strategies produce different results"""
        base_tasks = [
            {
                'title': 'Quick task',
                'due_date': str(date.today() + timedelta(days=10)),
                'estimated_hours': 0.5,  # Very quick
                'importance': 3,  # Low importance
                'dependencies': []
            },
            {
                'title': 'Important task',
                'due_date': str(date.today() + timedelta(days=10)),
                'estimated_hours': 8,  # Long task
                'importance': 10,  # High importance
                'dependencies': []
            }
        ]
        
        # Test FASTEST_WINS
        response1 = self.client.post(
            self.analyze_url,
            {'tasks': base_tasks, 'strategy': 'FASTEST_WINS'},
            format='json'
        )
        
        # Test HIGH_IMPACT
        response2 = self.client.post(
            self.analyze_url,
            {'tasks': base_tasks, 'strategy': 'HIGH_IMPACT'},
            format='json'
        )
        
        # For FASTEST_WINS, quick task should score higher
        fastest_tasks = response1.data['tasks']
        # For HIGH_IMPACT, important task should score higher
        impact_tasks = response2.data['tasks']
        
        # Strategies should produce different orderings
        self.assertNotEqual(
            fastest_tasks[0]['title'],
            impact_tasks[0]['title']
        )


class SuggestEndpointTests(TestCase):
    """Test /api/tasks/suggest/ endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.suggest_url = '/api/tasks/suggest/'
    
    def test_suggest_top_tasks(self):
        """Test that suggest returns top 3 tasks"""
        data = {
            'tasks': [
                {
                    'title': f'Task {i}',
                    'due_date': str(date.today() + timedelta(days=i)),
                    'estimated_hours': i,
                    'importance': 10 - i,
                    'dependencies': []
                }
                for i in range(1, 6)  # 5 tasks
            ]
        }
        
        response = self.client.post(self.suggest_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('top_tasks', response.data)
        self.assertEqual(len(response.data['top_tasks']), 3)
        self.assertEqual(response.data['total_tasks_analyzed'], 5)
        
        # Check that each task has a recommendation
        for task in response.data['top_tasks']:
            self.assertIn('recommendation', task)
    
    def test_suggest_get_method(self):
        """Test GET method returns helpful message"""
        response = self.client.get(self.suggest_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)


class EdgeCaseTests(TestCase):
    """Test edge cases and data validation"""
    
    def test_validate_task_missing_title(self):
        """Test validation fails for missing title"""
        task = {
            'due_date': '2025-12-01',
            'estimated_hours': 2,
            'importance': 5
        }
        is_valid, errors = validate_task_data(task)
        self.assertFalse(is_valid)
        self.assertTrue(any('title' in str(e).lower() for e in errors))
    
    def test_validate_task_invalid_date_format(self):
        """Test validation fails for invalid date format"""
        task = {
            'title': 'Test task',
            'due_date': '12/01/2025',  # Wrong format
            'estimated_hours': 2,
            'importance': 5
        }
        is_valid, errors = validate_task_data(task)
        self.assertFalse(is_valid)
    
    def test_validate_task_negative_hours(self):
        """Test validation fails for negative estimated hours"""
        task = {
            'title': 'Test task',
            'due_date': '2025-12-01',
            'estimated_hours': -2,
            'importance': 5
        }
        is_valid, errors = validate_task_data(task)
        self.assertFalse(is_valid)
    
    def test_validate_task_importance_out_of_range(self):
        """Test validation fails for importance out of range"""
        task = {
            'title': 'Test task',
            'due_date': '2025-12-01',
            'estimated_hours': 2,
            'importance': 15  # Out of range
        }
        is_valid, errors = validate_task_data(task)
        self.assertFalse(is_valid)
    
    def test_add_task_ids(self):
        """Test that add_task_ids assigns sequential IDs"""
        tasks = [
            {'title': 'Task 1'},
            {'title': 'Task 2'},
            {'title': 'Task 3'}
        ]
        result = add_task_ids(tasks)
        for i, task in enumerate(result):
            self.assertEqual(task['id'], i + 1)
