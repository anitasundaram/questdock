from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from assessment.models import Assessment, Response, Question
from roadmap.models import Roadmap, RecommendationTemplate
import json

class BusinessAnalyzer:
    """Service for analyzing business assessments and generating recommendations"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )
    
    def _prepare_features(self, assessment):
        """Convert assessment responses to feature vector"""
        responses = Response.objects.filter(assessment=assessment)
        features = {}
        
        for response in responses:
            question = response.question
            answer = response.answer
            
            # Convert different question types to numerical values
            if question.question_type == 'yes_no':
                value = 1.0 if str(answer).lower() == 'yes' else 0.0
            elif question.question_type == 'scale':
                value = float(answer)
            elif question.question_type == 'multiple':
                # Convert multiple choice to one-hot encoding
                options = question.options
                value = [1.0 if opt == answer else 0.0 for opt in options]
            
            features[f"q_{question.id}"] = value
            
        return features
    
    def analyze_assessment(self, assessment):
        """Generate scores and recommendations for an assessment"""
        features = self._prepare_features(assessment)
        
        # Group questions by category
        categories = {}
        for question in Question.objects.filter(
            id__in=Response.objects.filter(assessment=assessment).values_list('question_id', flat=True)
        ):
            if question.category_id not in categories:
                categories[question.category_id] = []
            categories[question.category_id].append(question.id)
        
        # Calculate category scores
        scores = {}
        for category_id, question_ids in categories.items():
            category_features = [v for k, v in features.items() 
                               if int(k.split('_')[1]) in question_ids]
            if isinstance(category_features[0], list):
                # Handle multiple choice questions
                category_features = [item for sublist in category_features 
                                   for item in (sublist if isinstance(sublist, list) else [sublist])]
            
            # Calculate weighted average score for category
            score = np.mean(category_features) * 100
            scores[category_id] = min(100, max(0, score))  # Clamp between 0-100
        
        # Generate recommendations
        recommendations = []
        for category_id, score in scores.items():
            template = RecommendationTemplate.objects.filter(
                category_id=category_id,
                score_range_min__lte=score,
                score_range_max__gte=score
            ).first()
            
            if template:
                recommendations.append({
                    'category_id': category_id,
                    'score': score,
                    'title': template.title,
                    'description': template.description,
                    'action_items': template.action_items,
                    'resources': template.resources
                })
        
        return {
            'scores': scores,
            'recommendations': recommendations
        }