"""
Utility functions for task validation and data processing.
"""
from datetime import datetime
from typing import Dict, List, Tuple, Any


def validate_task_data(task_dict: Dict) -> Tuple[bool, List[str]]:
    """
    Comprehensive validation of task data.
    
    Args:
        task_dict: Task data dictionary
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = ['title', 'due_date', 'estimated_hours', 'importance']
    for field in required_fields:
        if field not in task_dict or task_dict[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate title
    if 'title' in task_dict:
        if not isinstance(task_dict['title'], str):
            errors.append("Title must be a string")
        elif len(task_dict['title'].strip()) == 0:
            errors.append("Title cannot be empty")
        elif len(task_dict['title']) > 255:
            errors.append("Title must be 255 characters or less")
    
    # Validate due_date
    if 'due_date' in task_dict:
        due_date = task_dict['due_date']
        if isinstance(due_date, str):
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                errors.append("Invalid due_date format. Use YYYY-MM-DD")
        elif not isinstance(due_date, datetime):
            errors.append("due_date must be a string (YYYY-MM-DD) or datetime object")
    
    # Validate estimated_hours
    if 'estimated_hours' in task_dict:
        hours = task_dict['estimated_hours']
        try:
            hours_float = float(hours)
            if hours_float <= 0:
                errors.append("estimated_hours must be greater than 0")
        except (TypeError, ValueError):
            errors.append("estimated_hours must be a number")
    
    # Validate importance
    if 'importance' in task_dict:
        importance = task_dict['importance']
        try:
            importance_int = int(importance)
            if importance_int < 1 or importance_int > 10:
                errors.append("importance must be between 1 and 10")
        except (TypeError, ValueError):
            errors.append("importance must be an integer")
    
    # Validate dependencies
    if 'dependencies' in task_dict:
        deps = task_dict['dependencies']
        if not isinstance(deps, list):
            errors.append("dependencies must be a list")
        else:
            for dep in deps:
                if not isinstance(dep, int):
                    errors.append(f"Invalid dependency ID: {dep} (must be integer)")
                    break
    
    return len(errors) == 0, errors


def build_dependency_graph(tasks: List[Dict]) -> Dict[int, List[int]]:
    """
    Build adjacency list representation of task dependencies.
    
    Args:
        tasks: List of task dictionaries
    
    Returns:
        Dictionary mapping task_id -> list of dependency task_ids
    """
    graph = {}
    for task in tasks:
        task_id = task.get('id')
        dependencies = task.get('dependencies', [])
        graph[task_id] = dependencies
    return graph


def generate_explanation(task: Dict, score_data: Dict) -> str:
    """
    Generate human-readable explanation for task score.
    
    Args:
        task: Task dictionary
        score_data: Score calculation results
    
    Returns:
        Formatted explanation string
    """
    return score_data.get('explanation', 'No explanation available')


def format_warnings(validation_errors: List[str]) -> List[Dict[str, str]]:
    """
    Format validation errors into structured warning objects.
    
    Args:
        validation_errors: List of error messages
    
    Returns:
        List of warning dictionaries
    """
    return [
        {
            'type': 'validation_error',
            'message': error
        }
        for error in validation_errors
    ]


def get_priority_level(score: float) -> str:
    """
    Convert numeric score to priority level.
    
    Args:
        score: Final priority score (0-10)
    
    Returns:
        Priority level string
    """
    if score >= 7:
        return 'HIGH'
    elif score >= 4:
        return 'MEDIUM'
    else:
        return 'LOW'


def add_task_ids(tasks: List[Dict]) -> List[Dict]:
    """
    Add sequential IDs to tasks if they don't have them.
    
    Args:
        tasks: List of task dictionaries
    
    Returns:
        Tasks with IDs added
    """
    for i, task in enumerate(tasks):
        if 'id' not in task:
            task['id'] = i + 1
    return tasks
