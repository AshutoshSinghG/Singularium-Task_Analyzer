"""
Task Model for Smart Task Analyzer
Stores task information with fields for priority calculation.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Task(models.Model):
    """
    Task model with fields required for advanced priority scoring.
    
    Fields:
        title: Task name/description
        due_date: When the task should be completed
        estimated_hours: Time needed to complete (for quick win analysis)
        importance: User-defined importance scale 1-10
        dependencies: JSON array of task IDs this task depends on
    """
    
    title = models.CharField(
        max_length=255,
        help_text="Task name or description"
    )
    
    due_date = models.DateField(
        help_text="Due date for task completion"
    )
    
    estimated_hours = models.FloatField(
        validators=[MinValueValidator(0.1)],
        help_text="Estimated hours to complete (must be > 0)"
    )
    
    importance = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        help_text="Importance scale from 1 (low) to 10 (high)"
    )
    
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of task IDs this task depends on"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-importance', 'due_date']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return f"{self.title} (Due: {self.due_date})"
    
    def clean(self):
        """
        Custom validation for task data.
        """
        errors = {}
        
        # Validate estimated hours
        if self.estimated_hours is not None and self.estimated_hours <= 0:
            errors['estimated_hours'] = 'Estimated hours must be greater than 0'
        
        # Validate importance range
        if self.importance is not None:
            if self.importance < 1 or self.importance > 10:
                errors['importance'] = 'Importance must be between 1 and 10'
        
        # Validate dependencies is a list
        if self.dependencies is not None:
            if not isinstance(self.dependencies, list):
                errors['dependencies'] = 'Dependencies must be a list of task IDs'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        """
        self.clean()
        super().save(*args, **kwargs)
