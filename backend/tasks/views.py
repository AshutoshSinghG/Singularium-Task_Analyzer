"""
API Views for Smart Task Analyzer.
Implements task analysis and suggestion endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TaskAnalysisSerializer, TaskAnalysisResponseSerializer
from .scoring import (
    calculate_final_score,
    detect_circular_dependencies,
    STRATEGY_WEIGHTS
)
from .utils import (
    validate_task_data,
    format_warnings,
    get_priority_level,
    add_task_ids
)


class AnalyzeTasksView(APIView):
    def post(self, request):
        # Validate request data
        serializer = TaskAnalysisSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = serializer.validated_data['tasks']
        strategy = serializer.validated_data.get('strategy', 'SMART_BALANCE')
        
        # Add IDs to tasks if they don't have them
        tasks = add_task_ids(tasks)
        
        # Validate each task
        all_warnings = []
        validated_tasks = []
        
        for i, task in enumerate(tasks):
            is_valid, errors = validate_task_data(task)
            if not is_valid:
                all_warnings.extend([
                    {
                        'task_index': i,
                        'task_title': task.get('title', f'Task {i + 1}'),
                        'type': 'validation_error',
                        'message': error
                    }
                    for error in errors
                ])
            else:
                validated_tasks.append(task)
        
        # If no valid tasks, return error
        if not validated_tasks:
            return Response(
                {
                    'error': 'No valid tasks to analyze',
                    'warnings': all_warnings
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for circular dependencies
        has_cycles, cycle_details = detect_circular_dependencies(validated_tasks)
        
        if has_cycles:
            all_warnings.append({
                'type': 'circular_dependency',
                'message': 'Circular dependencies detected!',
                'details': cycle_details
            })
        
        # Calculate scores for each task
        scored_tasks = []
        for task in validated_tasks:
            score_data = calculate_final_score(task, validated_tasks, strategy)
            
            # Add score data to task
            task_with_score = {
                **task,
                'priority_score': score_data['final_score'],
                'score_breakdown': score_data['breakdown'],
                'score_explanation': score_data['explanation'],
                'priority_level': get_priority_level(score_data['final_score'])
            }
            scored_tasks.append(task_with_score)
        
        # Sort tasks by priority score (highest first)
        scored_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Prepare response
        response_data = {
            'tasks': scored_tasks,
            'warnings': all_warnings,
            'strategy': strategy,
            'has_circular_dependencies': has_cycles,
            'circular_dependency_details': cycle_details if has_cycles else []
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class SuggestTasksView(APIView):
    
    def post(self, request):
        # Use analyze endpoint logic
        analyze_view = AnalyzeTasksView()
        analyze_response = analyze_view.post(request)
        
        if analyze_response.status_code != 200:
            return analyze_response
        
        # Get analyzed tasks
        analyzed_data = analyze_response.data
        all_tasks = analyzed_data['tasks']
        
        # Get top 3 tasks
        top_tasks = all_tasks[:3]
        
        # Add recommendations
        for i, task in enumerate(top_tasks):
            rank = i + 1
            score = task['priority_score']
            
            if rank == 1:
                recommendation = f"🎯 TOP PRIORITY! This task has the highest score ({score:.2f}/10). Start with this task today."
            elif rank == 2:
                recommendation = f"⭐ Second priority task (score: {score:.2f}/10). Complete this after the top task."
            else:
                recommendation = f"✓ Third priority task (score: {score:.2f}/10). Important to complete soon."
            
            # Add blocking information
            if task.get('score_breakdown', {}).get('dependency', 0) >= 6:
                recommendation += " ⚠️ This task is blocking other tasks!"
            
            task['recommendation'] = recommendation
        
        # Prepare response
        response_data = {
            'top_tasks': top_tasks,
            'strategy': analyzed_data['strategy'],
            'total_tasks_analyzed': len(all_tasks),
            'warnings': analyzed_data.get('warnings', []),
            'has_circular_dependencies': analyzed_data.get('has_circular_dependencies', False),
            'circular_dependency_details': analyzed_data.get('circular_dependency_details', [])
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def get(self, request):
        """
        GET endpoint for suggestions.
        Returns helpful message if no tasks provided.
        """
        return Response(
            {
                'message': 'Use POST method with task data to get suggestions',
                'example': {
                    'tasks': [
                        {
                            'title': 'Example task',
                            'due_date': '2025-12-01',
                            'estimated_hours': 2,
                            'importance': 8,
                            'dependencies': []
                        }
                    ],
                    'strategy': 'SMART_BALANCE'
                }
            },
            status=status.HTTP_200_OK
        )
