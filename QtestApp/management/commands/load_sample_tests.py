from django.core.management.base import BaseCommand
from QtestApp.models import Test, Question, Choice

class Command(BaseCommand):
    help = 'Load sample Life in the UK tests with questions'
    
    def handle(self, *args, **options):
        # Sample questions data
        sample_questions = [
            {
                'text': 'Who were the first people to arrive in Britain in what we call the Stone Age?',
                'type': 'single',
                'choices': [
                    {'text': 'Farmers', 'correct': False},
                    {'text': 'Hunter-gatherers', 'correct': True},
                    {'text': 'Warriors', 'correct': False},
                    {'text': 'Nantes', 'correct': False},
                ],
                'explanation': 'The first people to arrive in Britain were hunter-gatherers in the Stone Age, around 10,000 years ago.'
            },
            {
                'text': 'The Commonwealth has no power over its members and it cannot suspend their membership:',
                'type': 'single',
                'choices': [
                    {'text': 'True', 'correct': False},
                    {'text': 'False', 'correct': True},
                ],
                'explanation': 'The Commonwealth has no power over its members, although it can suspend membership.'
            },
            {
                'text': 'When did Britain become permanently separated from the continent by the Channel?',
                'type': 'single',
                'choices': [
                    {'text': '10,000 years ago', 'correct': True},
                    {'text': '50,000 years ago', 'correct': False},
                    {'text': '15,000 years ago', 'correct': False},
                    {'text': '8,000 years ago', 'correct': False},
                ],
                'explanation': 'Britain only became permanently separated from the continent by the Channel about 10,000 years ago.'
            },
            {
                'text': 'Which of the following statements regarding the Black Death is NOT true?',
                'type': 'single',
                'choices': [
                    {'text': 'One third of the population of England died and a similar proportion in Scotland and Wales', 'correct': False},
                    {'text': 'It was one of the worst disasters ever to strike Britain', 'correct': False},
                    {'text': 'It affected children and old people only', 'correct': True},
                    {'text': 'Following the Black Death, there were labour shortages', 'correct': False},
                ],
                'explanation': 'In 1348, a disease, probably a form of plague, came to Britain. This was known as the Black Death. One third of the population of England died and a similar proportion in Scotland and Wales. This was one of the worst disasters ever to strike Britain. Following the Black Death, the smaller population meant there was less need to grow cereal crops. There were labour shortages and peasants began to demand higher wages.'
            },
            {
                'text': 'Who was reigning in England when Wales became formally united with England by the Act for the Government of Wales?',
                'type': 'single',
                'choices': [
                    {'text': 'Henry VII', 'correct': False},
                    {'text': 'Henry VIII', 'correct': True},
                    {'text': 'Elizabeth I', 'correct': False},
                    {'text': 'James I', 'correct': False},
                ],
                'explanation': 'During the reign of Henry VIII, Wales became formally united with England by the Act for the Government of Wales.'
            },
            {
                'text': 'The Elizabethan period is known for the richness of its poetry and drama, especially for the plays and poems of which playwright?',
                'type': 'single',
                'choices': [
                    {'text': 'Alexander Dumas', 'correct': False},
                    {'text': 'William Shakespeare', 'correct': True},
                    {'text': 'Charles Dickens', 'correct': False},
                    {'text': 'Thomas Hardy', 'correct': False},
                ],
                'explanation': 'The Elizabethan period is remembered for the richness of its poetry and drama, especially the plays and poems of William Shakespeare.'
            },
            {
                'text': 'Which of the following is NOT a fundamental principle of British life?',
                'type': 'single',
                'choices': [
                    {'text': 'Tolerance of those with different faiths and beliefs', 'correct': False},
                    {'text': 'The rule of law', 'correct': False},
                    {'text': 'Autocracy', 'correct': True},
                    {'text': 'Democracy', 'correct': False},
                ],
                'explanation': 'The fundamental principles of British life include: tolerance of those with different faiths and beliefs, the rule of law, democracy, individual liberty and participation in community life.'
            },
            {
                'text': 'Which TWO of the following are environmental charities?',
                'type': 'multiple',
                'choices': [
                    {'text': 'Crisis', 'correct': False},
                    {'text': 'The National Trust', 'correct': True},
                    {'text': 'Friends of the Earth', 'correct': True},
                    {'text': 'PDSA', 'correct': False},
                ],
                'explanation': 'The National Trust and Friends of the Earth are environmental charities.'
            },
            {
                'text': 'Which flag has a diagonal red cross on a white ground?',
                'type': 'single',
                'choices': [
                    {'text': 'The cross of St George, patron saint of England', 'correct': False},
                    {'text': 'The cross of St Patrick, patron saint of Ireland', 'correct': True},
                    {'text': 'The cross of St David, patron saint of Wales', 'correct': False},
                    {'text': 'The cross of St Andrew, patron saint of Scotland', 'correct': False},
                ],
                'explanation': 'The cross of St Patrick, patron saint of Ireland, is a diagonal red cross on a white ground.'
            },
            {
                'text': 'When did people learn to make bronze?',
                'type': 'single',
                'choices': [
                    {'text': 'Around 3,000 years ago', 'correct': False},
                    {'text': 'Around 4,000 years ago', 'correct': True},
                    {'text': 'Around 5,000 years ago', 'correct': False},
                    {'text': 'Around 2,000 years ago', 'correct': False},
                ],
                'explanation': 'People learned to make bronze around 4,000 years ago, marking the beginning of the Bronze Age.'
            },
            {
                'text': 'Which of the following are British values?',
                'type': 'multiple',
                'choices': [
                    {'text': 'Democracy', 'correct': True},
                    {'text': 'The rule of law', 'correct': True},
                    {'text': 'Individual liberty', 'correct': True},
                    {'text': 'Tolerance of those with different faiths', 'correct': True},
                ],
                'explanation': 'British values include democracy, the rule of law, individual liberty, and mutual respect and tolerance for those with different faiths and beliefs.'
            },
            {
                'text': 'What is the official name of the UK?',
                'type': 'single',
                'choices': [
                    {'text': 'United Kingdom of Great Britain and Northern Ireland', 'correct': True},
                    {'text': 'Great Britain', 'correct': False},
                    {'text': 'British Isles', 'correct': False},
                    {'text': 'England and Wales', 'correct': False},
                ],
                'explanation': 'The official name is the United Kingdom of Great Britain and Northern Ireland.'
            },
            {
                'text': 'When is Christmas Day celebrated?',
                'type': 'single',
                'choices': [
                    {'text': '24 December', 'correct': False},
                    {'text': '25 December', 'correct': True},
                    {'text': '26 December', 'correct': False},
                    {'text': '31 December', 'correct': False},
                ],
                'explanation': 'Christmas Day is celebrated on 25 December each year.'
            },
            {
                'text': 'Which of these is a famous British landmark?',
                'type': 'single',
                'choices': [
                    {'text': 'Stonehenge', 'correct': True},
                    {'text': 'Eiffel Tower', 'correct': False},
                    {'text': 'Colosseum', 'correct': False},
                    {'text': 'Statue of Liberty', 'correct': False},
                ],
                'explanation': 'Stonehenge is a famous prehistoric monument in Wiltshire, England.'
            },
            {
                'text': 'What is the capital of Scotland?',
                'type': 'single',
                'choices': [
                    {'text': 'Edinburgh', 'correct': True},
                    {'text': 'Glasgow', 'correct': False},
                    {'text': 'Aberdeen', 'correct': False},
                    {'text': 'Dundee', 'correct': False},
                ],
                'explanation': 'Edinburgh is the capital city of Scotland.'
            },
            {
                'text': 'Which languages are spoken in Wales?',
                'type': 'multiple',
                'choices': [
                    {'text': 'English', 'correct': True},
                    {'text': 'Welsh', 'correct': True},
                    {'text': 'Gaelic', 'correct': False},
                    {'text': 'Cornish', 'correct': False},
                ],
                'explanation': 'The main languages spoken in Wales are English and Welsh.'
            },
            {
                'text': 'When did the Second World War end?',
                'type': 'single',
                'choices': [
                    {'text': '1944', 'correct': False},
                    {'text': '1945', 'correct': True},
                    {'text': '1946', 'correct': False},
                    {'text': '1947', 'correct': False},
                ],
                'explanation': 'The Second World War ended in 1945.'
            },
            {
                'text': 'What is the Union Jack?',
                'type': 'single',
                'choices': [
                    {'text': 'The national flag of the UK', 'correct': True},
                    {'text': 'A type of food', 'correct': False},
                    {'text': 'A historical figure', 'correct': False},
                    {'text': 'A famous building', 'correct': False},
                ],
                'explanation': 'The Union Jack is the national flag of the United Kingdom.'
            },
        ]
        
        # First, let's check if tests already exist
        existing_tests = Test.objects.filter(slug__startswith='life-in-the-uk-test-')
        if existing_tests.exists():
            self.stdout.write(self.style.WARNING(f'Found {existing_tests.count()} existing tests. Deleting them...'))
            existing_tests.delete()
            self.stdout.write(self.style.SUCCESS('Deleted existing tests.'))
        
        # Create 12 test series (Test 1 through Test 12)
        for i in range(1, 13):
            try:
                test = Test.objects.create(
                    title=f'Life in the UK Test {i}',
                    description=f'Practice test {i} for Life in the UK citizenship test',
                    time_limit_minutes=45,
                    order=i,
                    is_active=True,
                    category='life_in_uk',
                    series_number=i,
                    chapter=None,
                    slug=f'life-in-the-uk-test-{i}',
                )
                
                self.stdout.write(self.style.SUCCESS(f'Created {test.title}'))
                
                # Add 24 questions to each test (repeating the sample questions)
                for j in range(24):
                    q_index = j % len(sample_questions)  # Cycle through sample questions
                    q_data = sample_questions[q_index]
                    
                    question = Question.objects.create(
                        test=test,
                        text=q_data['text'],
                        question_type=q_data['type'],
                        explanation=q_data['explanation'],
                        order=j + 1
                    )
                    
                    # Add choices
                    for k, choice_data in enumerate(q_data['choices']):
                        Choice.objects.create(
                            question=question,
                            text=choice_data['text'],
                            is_correct=choice_data['correct'],
                            order=k + 1
                        )
                
                self.stdout.write(f'  - Added {test.questions.count()} questions to {test.title}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating test {i}: {str(e)}'))
                continue
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created 12 test series with 24 questions each!')
        )