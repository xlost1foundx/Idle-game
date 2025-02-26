from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, login_manager
from models import User, Resources, Buildings
from game_logic import GameLogic
import stripe
from datetime import datetime, timedelta

stripe.api_key = app.config['STRIPE_KEY']

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'],
                   email=request.form['email'])
        user.set_password(request.form['password'])
        
        resources = Resources()
        buildings = Buildings()
        
        user.resources = resources
        user.buildings = buildings
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('game'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('game'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/game')
@login_required
def game():
    GameLogic.update_resources(current_user)
    db.session.commit()
    return render_template('game.html')

@app.route('/subscribe')
@login_required
def subscribe():
    return render_template('subscribe.html')

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Game Subscription',
                    },
                    'unit_amount': 299,
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('game', _external=True),
            cancel_url=url_for('subscribe', _external=True),
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, app.config['STRIPE_WEBHOOK_SECRET']
        )
    except ValueError as e:
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        return '', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_details']['email']
        user = User.query.filter_by(email=customer_email).first()
        if user:
            user.is_subscribed = True
            user.subscription_end = datetime.utcnow() + timedelta(days=30)
            db.session.commit()

    return ''

@app.route('/api/gather/<resource_type>', methods=['POST'])
@login_required
def gather_resource(resource_type):
    if resource_type in ['wood', 'stone', 'food']:
        GameLogic.add_manual_resource(current_user.resources, resource_type)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid resource type'})

@app.route('/api/build/<building_type>', methods=['POST'])
@login_required
def build(building_type):
    if GameLogic.can_afford_building(current_user.resources, building_type):
        costs = GameLogic.get_building_costs(building_type)
        current_user.resources.wood -= costs.get('wood', 0)
        current_user.resources.stone -= costs.get('stone', 0)
        
        if building_type == 'woodcutter':
            current_user.buildings.woodcutter += 1
        elif building_type == 'quarry':
            current_user.buildings.quarry += 1
        elif building_type == 'farm':
            current_user.buildings.farm += 1
            
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Not enough resources'})

@app.route('/api/upgrade/<building_type>', methods=['POST'])
@login_required
def upgrade_building(building_type):
    current_level = 1
    if building_type == 'woodcutter':
        current_level = current_user.buildings.woodcutter_level
    elif building_type == 'quarry':
        current_level = current_user.buildings.quarry_level
    elif building_type == 'farm':
        current_level = current_user.buildings.farm_level
    else:
        return jsonify({'success': False, 'message': 'Invalid building type'})

    if GameLogic.can_afford_upgrade(current_user.resources, building_type, current_level):
        costs = GameLogic.get_upgrade_costs(building_type, current_level)
        current_user.resources.wood -= costs.get('wood', 0)
        current_user.resources.stone -= costs.get('stone', 0)

        if building_type == 'woodcutter':
            current_user.buildings.woodcutter_level += 1
        elif building_type == 'quarry':
            current_user.buildings.quarry_level += 1
        elif building_type == 'farm':
            current_user.buildings.farm_level += 1

        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Not enough resources'})

@app.route('/api/hunt', methods=['POST'])
@login_required
def hunt():
    if GameLogic.can_hunt(current_user.resources):
        if GameLogic.perform_hunt(current_user.resources):
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Hunt successful! Got 2 food and 1 leather.'
            })
    return jsonify({
        'success': False,
        'message': 'Hunting is on cooldown'
    })