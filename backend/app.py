from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime
from services.ai_service import AIService
from models.interaction import Interaction, SummarizeRequest, SummarizeResponse

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize AI service
ai_service = AIService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Salesforce AI Interactions'
    })

@app.route('/summarize', methods=['POST'])
def summarize_interactions():
    """Summarize interactions endpoint"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'account_id' not in data or 'interactions' not in data:
            return jsonify({'error': 'Missing required fields: account_id, interactions'}), 400
        
        if not data['interactions']:
            return jsonify({'error': 'No interactions provided'}), 400
        
        # Parse interactions
        interactions = []
        for interaction_data in data['interactions']:
            try:
                interaction = Interaction(
                    id=interaction_data.get('id', ''),
                    account_id=interaction_data.get('account_id', ''),
                    subject=interaction_data.get('subject', ''),
                    description=interaction_data.get('description', ''),
                    interaction_type=interaction_data.get('interaction_type', ''),
                    created_date=datetime.fromisoformat(interaction_data.get('created_date', datetime.now().isoformat())),
                    created_by=interaction_data.get('created_by', ''),
                    status=interaction_data.get('status'),
                    priority=interaction_data.get('priority')
                )
                interactions.append(interaction)
            except Exception as e:
                return jsonify({'error': f'Invalid interaction data: {str(e)}'}), 400
        
        # Generate summary
        summary = ai_service.summarize_interactions(interactions)
        
        # Return response
        return jsonify({
            'success': True,
            'summary': {
                'account_id': summary.account_id,
                'summary': summary.summary,
                'key_topics': summary.key_topics,
                'sentiment_score': summary.sentiment_score,
                'next_steps': summary.next_steps,
                'total_interactions': summary.total_interactions,
                'date_range': summary.date_range,
                'urgency_level': summary.urgency_level
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error_message': str(e)
        }), 500

@app.route('/test-summarize', methods=['GET'])
def test_summarize():
    """Test endpoint with sample data"""
    try:
        # Sample test data
        sample_interactions = [
            Interaction(
                id="001",
                account_id="acc001",
                subject="Initial Discovery Call",
                description="Discussed their current CRM challenges and requirements for a new solution. Customer mentioned they need better reporting capabilities and integration with their existing systems.",
                interaction_type="Phone Call",
                created_date=datetime(2024, 1, 15, 10, 0),
                created_by="John Sales",
                status="Completed"
            ),
            Interaction(
                id="002",
                account_id="acc001",
                subject="Demo Presentation",
                description="Presented our CRM solution focusing on reporting features. Customer was impressed with the dashboard capabilities but had concerns about data migration timeline.",
                interaction_type="Meeting",
                created_date=datetime(2024, 1, 18, 14, 30),
                created_by="Sarah Demo",
                status="Completed"
            ),
            Interaction(
                id="003",
                account_id="acc001",
                subject="Follow-up on Pricing",
                description="Discussed pricing options and provided detailed proposal. Customer requested additional time to review with their team and mentioned budget constraints.",
                interaction_type="Email",
                created_date=datetime(2024, 1, 22, 9, 15),
                created_by="Mike Finance",
                status="Pending"
            )
        ]
        
        # Generate summary
        summary = ai_service.summarize_interactions(sample_interactions)
        
        return jsonify({
            'success': True,
            'summary': {
                'account_id': summary.account_id,
                'summary': summary.summary,
                'key_topics': summary.key_topics,
                'sentiment_score': summary.sentiment_score,
                'next_steps': summary.next_steps,
                'total_interactions': summary.total_interactions,
                'date_range': summary.date_range,
                'urgency_level': summary.urgency_level
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error_message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
