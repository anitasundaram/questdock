from django.core.management.base import BaseCommand
from assessment.models import Category, Question, Choice, Recommendation

class Command(BaseCommand):
    help = 'Loads initial assessment questions, choices, and recommendations'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading initial assessment data...')

        # Create categories
        categories = {
            'strategy': Category.objects.create(
                name='Business Strategy',
                description='Evaluation of your business planning and strategic direction'
            ),
            'operations': Category.objects.create(
                name='Operations',
                description='Assessment of your business processes and efficiency'
            ),
            'finance': Category.objects.create(
                name='Financial Management',
                description='Review of your financial planning and management'
            ),
            'marketing': Category.objects.create(
                name='Marketing & Sales',
                description='Analysis of your market presence and sales processes'
            )
        }

        # Sample questions and choices for Strategy category
        strategy_questions = [
            {
                'text': 'Do you have a documented business plan?',
                'description': 'A business plan outlines your business goals and strategies for achieving them.',
                'choices': [
                    {
                        'text': 'Yes, detailed and regularly updated',
                        'score': 100,
                        'recommendation': 'Continue maintaining and updating your business plan regularly.'
                    },
                    {
                        'text': 'Yes, but needs updating',
                        'score': 70,
                        'recommendation': 'Schedule quarterly reviews of your business plan to keep it current.'
                    },
                    {
                        'text': 'No, but planning to create one',
                        'score': 30,
                        'recommendation': 'Prioritize creating a business plan within the next 3 months.'
                    },
                    {
                        'text': 'No business plan',
                        'score': 0,
                        'recommendation': 'Start with a basic business plan template and outline your key objectives.'
                    }
                ]
            },
            # Add more questions as needed
        ]

        # Create questions and choices
        for category_key, questions_data in {
            'strategy': strategy_questions,
            # Add more categories and their questions
        }.items():
            for q_data in questions_data:
                question = Question.objects.create(
                    category=categories[category_key],
                    text=q_data['text'],
                    description=q_data.get('description', '')
                )
                
                for c_data in q_data['choices']:
                    Choice.objects.create(
                        question=question,
                        text=c_data['text'],
                        score=c_data['score']
                    )
                    
                    # Create associated recommendation if score is below threshold
                    if c_data['score'] < 70:
                        Recommendation.objects.create(
                            category=categories[category_key],
                            title=f'Improve {question.text.lower()}',
                            description=c_data['recommendation'],
                            priority=1 if c_data['score'] < 30 else 2
                        )

        self.stdout.write(self.style.SUCCESS('Successfully loaded initial assessment data'))