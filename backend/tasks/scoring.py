"""
Advanced Priority Scoring Algorithm for Smart Task Analyzer

This module implements a sophisticated multi-factor scoring system that considers:
1. Urgency (deadline proximity with date intelligence)
2. Importance (user-defined priority)
3. Effort (quick win detection)
4. Dependencies (blocking task analysis)

Each factor is weighted and combined to produce a final priority score.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Set, Optional


# ================================
# STRATEGY WEIGHT CONFIGURATIONS
# ================================

STRATEGY_WEIGHTS = {
    'FASTEST_WINS': {
        'urgency': 0.15,
        'importance': 0.15,
        'effort': 0.55,  # Prioritize low effort tasks
        'dependency': 0.15
    },
    'HIGH_IMPACT': {
        'urgency': 0.15,
        'importance': 0.55,  # Prioritize high importance
        'effort': 0.15,
        'dependency': 0.15
    },
    'DEADLINE_DRIVEN': {
        'urgency': 0.55,  # Prioritize urgent tasks
        'importance': 0.20,
        'effort': 0.10,
        'dependency': 0.15
    },
    'SMART_BALANCE': {
        'urgency': 0.25,
        'importance': 0.25,
        'effort': 0.25,
        'dependency': 0.25
    }
}

# ================================
# CORE SCORING FUNCTIONS
# ================================

def calculate_urgency_score(due_date_str: str, today: Optional[date] = None) -> Tuple[float, str]:
    """
    Calculate urgency score based on deadline proximity.
    
    Algorithm:
    - Overdue tasks: Maximum urgency (10.0)
    - Due today: Very high urgency (9.0)
    - Due within 3 days: High urgency (7-8)
    - Due within 7 days: Medium urgency (5-6)
    - Due later: Decreasing urgency based on days remaining
    - Weekend adjustment: Slightly reduce urgency if due on weekend
    
    Args:
        due_date_str: Due date in 'YYYY-MM-DD' format or date object
        today: Current date (defaults to today)
    
    Returns:
        Tuple of (urgency_score, explanation)
    """
    if today is None:
        today = date.today()
    
    # Parse due date
    if isinstance(due_date_str, str):
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            return 5.0, "Invalid date format, using default urgency"
    else:
        due_date = due_date_str
    
    # Calculate days difference
    days_left = (due_date - today).days
    
    # Overdue tasks get maximum urgency
    if days_left < 0:
        return 10.0, f"OVERDUE by {abs(days_left)} days - Maximum urgency!"
    
    # Due today
    elif days_left == 0:
        return 9.0, "Due TODAY - Very high urgency"
    
    # Due within 3 days
    elif days_left <= 3:
        score = 8.0 - (days_left * 0.3)  # 8.0 to 7.1
        return score, f"Due in {days_left} days - High urgency"
    
    # Due within a week
    elif days_left <= 7:
        score = 7.0 - (days_left - 3) * 0.5  # 6.5 to 5.0
        return score, f"Due in {days_left} days - Medium urgency"
    
    # Due within 2 weeks
    elif days_left <= 14:
        score = 5.0 - (days_left - 7) * 0.3  # 4.7 to 2.8
        return score, f"Due in {days_left} days - Moderate urgency"
    
    # Due later
    else:
        score = max(1.0, 3.0 - (days_left - 14) * 0.1)  # Gradually decrease
        return score, f"Due in {days_left} days - Low urgency"


def calculate_importance_score(importance: int) -> Tuple[float, str]:
    """
    Calculate importance score (direct mapping from 1-10 scale).
    
    Args:
        importance: User-defined importance (1-10)
    
    Returns:
        Tuple of (importance_score, explanation)
    """
    if importance < 1 or importance > 10:
        return 5.0, "Invalid importance (must be 1-10), using default"
    
    # Direct mapping
    score = float(importance)
    
    if importance >= 8:
        level = "Critical importance"
    elif importance >= 6:
        level = "High importance"
    elif importance >= 4:
        level = "Medium importance"
    else:
        level = "Low importance"
    
    return score, f"{level} (rated {importance}/10)"


def calculate_effort_score(estimated_hours: float) -> Tuple[float, str]:
    """
    Calculate effort score with quick win bonus.
    Lower effort = higher score (encourages completing quick wins).
    
    Algorithm:
    - Tasks under 1 hour: Maximum score (10)
    - 1-2 hours: High score (8-9)
    - 2-4 hours: Medium score (6-7)
    - 4-8 hours: Lower score (4-5)
    - 8+ hours: Minimum score (1-3)
    
    Args:
        estimated_hours: Time to complete in hours
    
    Returns:
        Tuple of (effort_score, explanation)
    """
    if estimated_hours <= 0:
        return 5.0, "Invalid estimated hours, using default"
    
    # Quick wins (< 1 hour)
    if estimated_hours < 1:
        return 10.0, f"Quick win! ({estimated_hours}h) - Maximum effort score"
    
    # Very fast (1-2 hours)
    elif estimated_hours <= 2:
        score = 9.0 - (estimated_hours - 1) * 0.5
        return score, f"Fast task ({estimated_hours}h) - High effort score"
    
    # Moderate (2-4 hours)
    elif estimated_hours <= 4:
        score = 7.5 - (estimated_hours - 2) * 0.75
        return score, f"Moderate task ({estimated_hours}h) - Medium effort score"
    
    # Substantial (4-8 hours)
    elif estimated_hours <= 8:
        score = 5.5 - (estimated_hours - 4) * 0.375
        return score, f"Substantial task ({estimated_hours}h) - Lower effort score"
    
    # Large task (8+ hours)
    else:
        score = max(1.0, 4.0 - (estimated_hours - 8) * 0.2)
        return score, f"Large task ({estimated_hours}h) - Low effort score"


def calculate_dependency_score(task_id: int, all_tasks: List[Dict]) -> Tuple[float, str]:
    """
    Calculate dependency score based on how many tasks depend on this one.
    Tasks that block more other tasks get higher scores.
    
    Args:
        task_id: ID of the task to score
        all_tasks: List of all tasks with their dependencies
    
    Returns:
        Tuple of (dependency_score, explanation)
    """
    blocking_count = 0
    blocked_tasks = []
    
    # Count how many tasks have this task in their dependencies
    for task in all_tasks:
        task_deps = task.get('dependencies', [])
        if task_id in task_deps:
            blocking_count += 1
            blocked_tasks.append(task.get('title', f"Task {task.get('id')}"))
    
    # Score increases with number of blocked tasks
    if blocking_count == 0:
        return 3.0, "No tasks depend on this"
    elif blocking_count == 1:
        return 6.0, f"Blocks 1 task: {blocked_tasks[0]}"
    elif blocking_count == 2:
        return 8.0, f"Blocks {blocking_count} tasks"
    else:
        score = min(10.0, 8.0 + (blocking_count - 2) * 0.5)
        return score, f"Blocks {blocking_count} tasks - High priority!"


# ================================
# DEPENDENCY GRAPH ANALYSIS
# ================================

def detect_circular_dependencies(tasks: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Detect circular dependencies using depth-first search.
    
    Args:
        tasks: List of task dictionaries with 'id' and 'dependencies'
    
    Returns:
        Tuple of (has_cycles, cycle_descriptions)
    """
    # Build adjacency list
    graph = {}
    task_map = {}
    
    for task in tasks:
        task_id = task.get('id')
        task_map[task_id] = task.get('title', f'Task {task_id}')
        graph[task_id] = task.get('dependencies', [])
    
    def has_cycle_util(node: int, visited: Set[int], rec_stack: Set[int], path: List[int]) -> Optional[List[int]]:
        """DFS utility to detect cycles"""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = has_cycle_util(neighbor, visited, rec_stack, path[:])
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        rec_stack.remove(node)
        return None
    
    visited = set()
    cycles = []
    
    for task_id in graph:
        if task_id not in visited:
            cycle = has_cycle_util(task_id, visited, set(), [])
            if cycle:
                # Format cycle description
                cycle_names = [task_map.get(tid, f'Task {tid}') for tid in cycle]
                cycle_desc = ' → '.join(cycle_names)
                cycles.append(cycle_desc)
    
    return len(cycles) > 0, cycles


# ================================
# FINAL SCORE CALCULATION
# ================================

def calculate_final_score(
    task: Dict,
    all_tasks: List[Dict],
    strategy: str = 'SMART_BALANCE'
) -> Dict:
    """
    Calculate final priority score using weighted multi-factor algorithm.
    
    Args:
        task: Task dictionary with all required fields
        all_tasks: All tasks (needed for dependency calculation)
        strategy: Scoring strategy name
    
    Returns:
        Dictionary with score, breakdown, and explanation
    """
    # Get weights for strategy
    weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS['SMART_BALANCE'])
    
    # Calculate individual scores
    urgency_score, urgency_exp = calculate_urgency_score(task.get('due_date'))
    importance_score, importance_exp = calculate_importance_score(task.get('importance'))
    effort_score, effort_exp = calculate_effort_score(task.get('estimated_hours'))
    dependency_score, dependency_exp = calculate_dependency_score(
        task.get('id'),
        all_tasks
    )
    
    # Calculate weighted final score
    final_score = (
        urgency_score * weights['urgency'] +
        importance_score * weights['importance'] +
        effort_score * weights['effort'] +
        dependency_score * weights['dependency']
    )
    
    # Round to 2 decimal places
    final_score = round(final_score, 2)
    
    # Generate comprehensive explanation
    explanation = f"""
Priority Score: {final_score}/10 (Strategy: {strategy})
├─ Urgency: {urgency_score:.1f}/10 × {weights['urgency']:.0%} = {urgency_score * weights['urgency']:.2f} ({urgency_exp})
├─ Importance: {importance_score:.1f}/10 × {weights['importance']:.0%} = {importance_score * weights['importance']:.2f} ({importance_exp})
├─ Effort: {effort_score:.1f}/10 × {weights['effort']:.0%} = {effort_score * weights['effort']:.2f} ({effort_exp})
└─ Dependencies: {dependency_score:.1f}/10 × {weights['dependency']:.0%} = {dependency_score * weights['dependency']:.2f} ({dependency_exp})
    """.strip()
    
    return {
        'final_score': final_score,
        'breakdown': {
            'urgency': urgency_score,
            'importance': importance_score,
            'effort': effort_score,
            'dependency': dependency_score
        },
        'weights': weights,
        'explanation': explanation
    }
