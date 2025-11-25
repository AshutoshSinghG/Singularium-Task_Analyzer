"""
Serializers for Task API endpoints.
Handles JSON serialization and validation.
"""
from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model with custom validation.
    """
    
    # Read-only fields for analysis results
    priority_score = serializers.FloatField(read_only=True, required=False)
    score_explanation = serializers.CharField(read_only=True, required=False)
    priority_level = serializers.CharField(read_only=True, required=False)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'due_date',
            'estimated_hours',
            'importance',
            'dependencies',
            'priority_score',
            'score_explanation',
            'priority_level',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_importance(self, value):
        """Validate importance is within 1-10 range"""
        if value < 1 or value > 10:
            raise serializers.ValidationError(
                "Importance must be between 1 and 10"
            )
        return value
    
    def validate_estimated_hours(self, value):
        """Validate estimated hours is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "Estimated hours must be greater than 0"
            )
        return value
    
    def validate_dependencies(self, value):
        """Validate dependencies is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Dependencies must be a list of task IDs"
            )
        return value


class TaskAnalysisSerializer(serializers.Serializer):
    """
    Serializer for task analysis request.
    """
    tasks = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        help_text="List of tasks to analyze"
    )
    
    strategy = serializers.ChoiceField(
        choices=['FASTEST_WINS', 'HIGH_IMPACT', 'DEADLINE_DRIVEN', 'SMART_BALANCE'],
        default='SMART_BALANCE',
        help_text="Priority scoring strategy"
    )
    
    def validate_tasks(self, value):
        """Validate each task has required fields"""
        if not value:
            raise serializers.ValidationError("Tasks list cannot be empty")
        
        required_fields = ['title', 'due_date', 'estimated_hours', 'importance']
        
        for i, task in enumerate(value):
            for field in required_fields:
                if field not in task:
                    raise serializers.ValidationError(
                        f"Task {i + 1} is missing required field: {field}"
                    )
        
        return value


class TaskAnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer for task analysis response.
    """
    tasks = serializers.ListField(
        child=serializers.DictField()
    )
    
    warnings = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    
    strategy = serializers.CharField()
    
    has_circular_dependencies = serializers.BooleanField()
    
    circular_dependency_details = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
