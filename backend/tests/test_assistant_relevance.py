"""FR10/NFR03: actual relevant passages, not newest records matching stop words."""
from app.providers.assistant import RetrievalProvider
from tests.helpers import post_json
from tests.test_learning import administrator, learner

def publish(admin, title, body, tags):
    response = post_json(admin, '/api/v1/admin/content', {
        'title': title, 'summary': title, 'body': body, 'tags': tags, 'status': 'published',
    })
    assert response.status_code == 201
    return response.json()

def test_specific_interview_guide_outranks_recent_unrelated_common_words(app):
    admin = administrator(app)
    relevant = publish(admin, 'Interview preparation', 'Practice an interview response using Situation, Task, Action and Result. Prepare specific project examples.', ['interview'])
    for title in ('Campus gardening', 'Library hours', 'Printing policy'):
        publish(admin, title, 'The guide explains the general information and what you should know about this topic.', ['campus'])
    app.state.assistant_provider = RetrievalProvider()
    result = post_json(learner(app), '/api/v1/assistant', {'question':'How should I prepare for an OJT interview?'})
    assert result.status_code == 200
    assert result.json()['sources'][0]['id'] == relevant['id']
    assert 'Situation' in result.json()['answer']

def test_unrelated_question_does_not_cite_guides_due_to_common_words(app):
    admin = administrator(app)
    publish(admin, 'Resume preparation', 'The resume guide explains what you should include in the document.', ['resume'])
    app.state.assistant_provider = RetrievalProvider()
    result = post_json(learner(app), '/api/v1/assistant', {'question':'What is the capital of Mars?'})
    assert result.status_code == 200
    assert result.json()['sources'] == []
    assert result.json()['uncertainty'] is True

def test_retrieval_extracts_the_matching_passage_beyond_the_opening(app):
    admin = administrator(app)
    publish(admin, 'Interview practice reference', 'General course administration. ' * 70 + '\n\nUse the STAR method: Situation, Task, Action, Result. Explain what you personally did and the outcome.', ['interview'])
    app.state.assistant_provider = RetrievalProvider()
    result = post_json(learner(app), '/api/v1/assistant', {'question':'How do I use STAR in interviews?'})
    assert result.status_code == 200
    assert 'Situation, Task, Action, Result' in result.json()['answer']


def test_follow_up_resolves_previous_question_without_exposing_account_data(app):
    guide = publish(administrator(app), 'Interview STAR practice', 'Situation, Task, Action, Result: use an actual class project and explain your contribution.', ['interview'])
    app.state.assistant_provider = RetrievalProvider()
    result = post_json(learner(app), '/api/v1/assistant', {
        'question': 'Can you give an example?',
        'previous_questions': ['How do I prepare for an interview?'],
    })
    assert result.status_code == 200
    assert result.json()['sources'][0]['id'] == guide['id']
    assert 'class project' in result.json()['answer']


def test_changing_subject_does_not_reuse_unrelated_conversation_sources(app):
    publish(administrator(app), 'Interview practice', 'Prepare an interview with STAR.', ['interview'])
    app.state.assistant_provider = RetrievalProvider()
    result = post_json(learner(app), '/api/v1/assistant', {
        'question': 'What is the capital of Mars?',
        'previous_questions': ['How do I prepare for an interview?'],
    })
    assert result.status_code == 200
    assert result.json()['sources'] == []


def test_conversation_context_is_bounded_and_rejects_private_fields(app):
    client = learner(app)
    for extra in ({'previous_questions': ['x'] * 4}, {'previous_questions': [' ']},
                  {'previous_questions': ['x' * 1001]}, {'application': {'resume': 'private'}}):
        assert post_json(client, '/api/v1/assistant', {'question': 'Interview tips?', **extra}).status_code == 422


def test_example_follow_up_extracts_an_actual_illustration(app):
    body = ('Prepare an interview with STAR.\n\n' + 'Interview preparation notes. ' * 60 +
            '\n\nIllustrative example: Our class had conflicting slide versions. I gathered agreed files, assembled the final deck, and checked it with my teammates. We submitted one consistent presentation.')
    publish(administrator(app), 'Interview practice', body, ['interview'])
    app.state.assistant_provider = RetrievalProvider()
    result = post_json(learner(app), '/api/v1/assistant', {
        'question': 'Give me a concrete example.', 'previous_questions': ['How do I prepare for an interview?'],
    })
    assert result.status_code == 200
    assert 'conflicting slide versions' in result.json()['answer']
