from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name

class Question(models.Model):
    QUESTION_TYPES = (
        ('yes_no', 'Yes/No'),
        ('scale', 'Scale (1-5)'),
        ('multiple', 'Multiple Choice'),
    )
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    weight = models.FloatField(default=1.0)
    order = models.IntegerField(default=0)
    options = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    # New fields for conditional logic
    depends_on = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    show_conditions = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        help_text="""
        JSON format for conditions. Example:
        {
            "operator": "equals", # or "greater_than", "less_than", "in"
            "value": "yes" # or number/array depending on question_type
        }
        """
    )
    skip_logic = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        help_text="""
        JSON format for skip logic. Example:
        {
            "if_answer": "yes", 
            "skip_to_question_id": 5
        }
        """
    )
    branch_logic = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        help_text="""
        JSON format for branch logic. Example:
        {
            "conditions": [
                {
                    "answer": "yes", 
                    "next_question_id": 3
                },
                {
                    "answer": "no",
                    "next_question_id": 7
                }
            ]
        }
        """
    )
    
    class Meta:
        ordering = ['category', 'order']
    
    def __str__(self):
        return f"{self.category.name} - {self.text[:50]}"
    
    def should_show(self, previous_answers):
        if not self.depends_on_id or not self.show_conditions:
            return True
        
        dependent_answer = previous_answers.get(str(self.depends_on_id))
        if dependent_answer is None:
            return False
        
        condition = self.show_conditions
        operator = condition.get('operator')
        value = condition.get('value')
        
        if operator == 'equals':
            return str(dependent_answer) == str(value)
        elif operator == 'greater_than':
            return float(dependent_answer) > float(value)
        elif operator == 'less_than':
            return float(dependent_answer) < float(value)
        elif operator == 'in':
            return dependent_answer in value
        
        return True
    
    def get_next_question_id(self, answer):
        if self.branch_logic:
            for condition in self.branch_logic['conditions']:
                if str(condition['answer']) == str(answer):
                    return condition['next_question_id']
        
        if self.skip_logic and str(self.skip_logic['if_answer']) == str(answer):
            return self.skip_logic['skip_to_question_id']
        
        return None

class Assessment(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200, blank=True, null=True)  # Added field
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Response(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.JSONField(encoder=DjangoJSONEncoder)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['question__category', 'question__order']
        unique_together = ['assessment', 'question']
    
    def __str__(self):
        return f"{self.assessment.title} - {self.question.text[:50]}"