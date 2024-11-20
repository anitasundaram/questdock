from django.db import models
from wagtail.models import Page 
from wagtail.fields import RichTextField 
from wagtail.admin.panels import FieldPanel 
from assessment.models import Category
import uuid
from django.utils import timezone

class RecommendationTemplate(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    score_range_min = models.IntegerField()
    score_range_max = models.IntegerField()
    title = models.CharField(max_length=200)
    description = RichTextField()
    action_items = models.JSONField()
    resources = models.JSONField()

    panels = [
        FieldPanel('category'),
        FieldPanel('score_range_min'),
        FieldPanel('score_range_max'),
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('action_items'),
        FieldPanel('resources'),
    ]

    def __str__(self):
        return f"{self.category.name} - {self.title}"

class Roadmap(models.Model):
    assessment = models.OneToOneField('assessment.Assessment', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    recommendations = models.JSONField()

    def __str__(self):
        return f"Roadmap for {self.assessment.user.email}"

class RoadmapShare(models.Model):
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='shares')
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='roadmap_shares')
    shared_with_email = models.EmailField(null=True, blank=True)
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Share for {self.roadmap} - {self.share_token}"

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at