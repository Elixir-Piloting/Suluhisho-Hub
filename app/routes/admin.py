from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, Response
from flask_login import login_required, current_user
from functools import wraps
from bson import ObjectId
from datetime import datetime, timedelta
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.suggestion import Suggestion
from app.models.report import Report
from app.models.settings import Settings
from flask_mail import Message

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Define allowed categories (same as in posts.py)
ALLOWED_CATEGORIES = [
    'Infrastructure',
    'Security',
    'Environment',
    'Public Services',
    'Transportation',
    'Education',
    'Healthcare',
    'Other'
]

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def mod_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_admin and not current_user.is_moderator):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    # Get system statistics
    stats = {
        'total_users': current_app.db.users.count_documents({}),
        'total_posts': current_app.db.posts.count_documents({'is_deleted': False}),
        'total_comments': current_app.db.comments.count_documents({'is_deleted': False}),
        'total_suggestions': current_app.db.suggestions.count_documents({'is_deleted': False})
    }
    
    # Get posts by category for pie chart
    category_data = []
    for category in ALLOWED_CATEGORIES:
        count = current_app.db.posts.count_documents({'category': category, 'is_deleted': False})
        if count > 0:  # Only include categories with posts
            category_data.append({
                'category': category,
                'count': count
            })
    
    # Get activity over time (last 7 days) for line chart
    now = datetime.utcnow()
    activity_data = []
    for i in range(7):
        day_start = datetime(now.year, now.month, now.day) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        posts = current_app.db.posts.count_documents({
            'created_at': {'$gte': day_start, '$lt': day_end},
            'is_deleted': False
        })
        
        comments = current_app.db.comments.count_documents({
            'created_at': {'$gte': day_start, '$lt': day_end},
            'is_deleted': False
        })
        
        reports = current_app.db.reports.count_documents({
            'created_at': {'$gte': day_start, '$lt': day_end}
        })
        
        activity_data.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'posts': posts,
            'comments': comments,
            'reports': reports
        })
    
    # Reverse to show oldest to newest
    activity_data.reverse()
    
    # Get reports count
    reports_count = Report.get_pending_count(current_app.db)
    
    return render_template('admin/index.html',
                          stats=stats,
                          category_data=category_data,
                          activity_data=activity_data,
                          reports_count=reports_count)

    # Get recent activity
    recent_activity = []
    
    # Recent user registrations
    recent_users = list(current_app.db.users.find().sort('created_at', -1).limit(5))
    for user in recent_users:
        recent_activity.append({
            'icon': 'user',
            'text': f'New user registration: {user["username"]}',
            'timestamp': user['created_at']
        })

    # Recent posts
    recent_posts = list(current_app.db.posts.find({'is_deleted': False}).sort('created_at', -1).limit(5))
    for post in recent_posts:
        recent_activity.append({
            'icon': 'file-alt',
            'text': f'New post created: {post["title"]}',
            'timestamp': post['created_at']
        })

    # Sort all activity by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:10]  # Keep only the 10 most recent items

    # Get email configuration status
    email_configured = bool(current_app.config.get('MAIL_USERNAME'))

    return render_template('admin/index.html', 
                         stats=stats,
                         reports_count=reports_count,
                         recent_activity=recent_activity,
                         maintenance_mode=Settings.get_maintenance_mode(current_app.db),
                         email_configured=email_configured)

@bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    users = list(current_app.db.users.find().skip(skip).limit(per_page))
    total = current_app.db.users.count_documents({})
    
    return render_template('admin/users.html', users=users, total=total, page=page, per_page=per_page)

@bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))
    
    new_status = 'active' if user.get('status') == 'suspended' else 'suspended'
    current_app.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'status': new_status}}
    )
    
    flash(f'User status updated to {new_status}.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<user_id>/edit-role', methods=['POST'])
@login_required
@admin_required
def edit_user_role(user_id):
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))
    
    # Prevent self-demotion
    if str(user['_id']) == str(current_user._id):
        flash('You cannot modify your own role.', 'error')
        return redirect(url_for('admin.users'))
    
    new_role = request.form.get('role')
    if new_role not in ['user', 'moderator', 'admin']:
        flash('Invalid role specified.', 'error')
        return redirect(url_for('admin.users'))
    
    # Update user role flags
    role_update = {
        'is_admin': new_role == 'admin',
        'is_moderator': new_role == 'moderator'
    }
    
    current_app.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': role_update}
    )
    
    flash(f'User role updated to {new_role}.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/reports')
@login_required
@admin_required
def reports():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    # Get total count of reports
    total = current_app.db.reports.count_documents({})
    
    # Get paginated reports
    reports = list(current_app.db.reports.find()
                  .sort('created_at', -1)
                  .skip(skip)
                  .limit(per_page))
    
    # Get reporter information for each report
    for report in reports:
        # Ensure created_at exists
        if 'created_at' not in report:
            report['created_at'] = report.get('generated_at', datetime.utcnow())
        
        # Handle user-reported content
        if 'reporter_id' in report:
            reporter = current_app.db.users.find_one({'_id': report['reporter_id']})
            if reporter:
                report['reporter'] = {
                    'username': reporter['username'],
                    'profile_picture': reporter.get('profile_picture')
                }
            else:
                report['reporter'] = {
                    'username': '[deleted]',
                    'profile_picture': None
                }
        # Handle generated reports
        elif 'generated_by' in report:
            generator = current_app.db.users.find_one({'_id': report['generated_by']})
            if generator:
                report['reporter'] = {
                    'username': generator['username'],
                    'profile_picture': generator.get('profile_picture')
                }
            else:
                report['reporter'] = {
                    'username': '[deleted]',
                    'profile_picture': None
                }
        else:
            report['reporter'] = {
                'username': 'System',
                'profile_picture': None
            }
    
    return render_template('admin/reports.html',
                         reports=reports,
                         total=total,
                         page=page,
                         per_page=per_page)

@bp.route('/reports/<report_id>/dismiss', methods=['POST'])
@login_required
@mod_required
def dismiss_report(report_id):
    report = current_app.db.reports.find_one({'_id': ObjectId(report_id)})
    if not report:
        abort(404)
    
    # Update report status
    current_app.db.reports.update_one(
        {'_id': ObjectId(report_id)},
        {'$set': {'status': 'dismissed'}}
    )
    
    # Create notification for reporter
    notification_data = {
        'user_id': report['reporter_id'],
        'type': 'report_dismissed',
        'title': 'Report Dismissed',
        'message': f'Your report has been reviewed and dismissed by a moderator.',
        'content_type': report['content_type'],
        'content_id': report['content_id'],
        'created_at': datetime.utcnow(),
        'is_read': False
    }
    current_app.db.notifications.insert_one(notification_data)
    
    flash('Report has been dismissed.', 'success')
    return redirect(url_for('admin.reports'))

@bp.route('/reports/<content_type>/<content_id>/remove', methods=['POST'])
@login_required
@mod_required
def remove_content(content_type, content_id):
    if content_type not in ['posts', 'comments', 'suggestions']:
        abort(404)
    
    # Get the content
    content = current_app.db[content_type].find_one({'_id': ObjectId(content_id)})
    if not content:
        abort(404)
    
    # Mark content as deleted
    current_app.db[content_type].update_one(
        {'_id': ObjectId(content_id)},
        {'$set': {'is_deleted': True}}
    )
    
    # Create notification for content owner
    notification_data = {
        'user_id': ObjectId(content['author_id']),
        'type': 'content_removed',
        'title': 'Content Removed',
        'message': f'Your {content_type} has been removed by a moderator.',
        'content_type': content_type,
        'content_id': ObjectId(content_id),
        'created_at': datetime.utcnow(),
        'is_read': False
    }
    current_app.db.notifications.insert_one(notification_data)
    
    # Update report status
    current_app.db.reports.update_many(
        {
            'content_type': content_type,
            'content_id': ObjectId(content_id)
        },
        {'$set': {'status': 'resolved'}}
    )
    
    flash('Content has been removed.', 'success')
    return redirect(url_for('admin.reports'))

@bp.route('/reports/<content_type>/<content_id>')
@login_required
@mod_required
def view_content(content_type, content_id):
    if content_type not in ['posts', 'comments', 'suggestions']:
        abort(404)
    
    # Get the content
    content = current_app.db[content_type].find_one({'_id': ObjectId(content_id), 'is_deleted': False})
    if not content:
        abort(404)
    
    # Get author information
    author = current_app.db.users.find_one({'_id': ObjectId(content['author_id'])})
    if author:
        content['author'] = {
            'username': author['username'],
            'profile_picture': author.get('profile_picture')
        }
    else:
        content['author'] = {
            'username': '[deleted]',
            'profile_picture': None
        }
    
    # Get related reports
    reports = list(current_app.db.reports.find({
        'content_type': content_type,
        'content_id': ObjectId(content_id)
    }).sort('created_at', -1))
    
    # Get reporter information for each report
    for report in reports:
        reporter = current_app.db.users.find_one({'_id': report['reporter_id']})
        if reporter:
            report['reporter'] = {
                'username': reporter['username'],
                'profile_picture': reporter.get('profile_picture')
            }
        else:
            report['reporter'] = {
                'username': '[deleted]',
                'profile_picture': None
            }
    
    return render_template('admin/view_content.html',
                         content=content,
                         content_type=content_type,
                         reports=reports)

@bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        settings = {
            'site_name': request.form.get('site_name'),
            'site_description': request.form.get('site_description'),
            'contact_email': request.form.get('contact_email'),
            'allow_registration': request.form.get('allow_registration') == 'on',
            'require_email_verification': request.form.get('require_email_verification') == 'on',
            'enable_email_notifications': request.form.get('enable_email_notifications') == 'on',
            'notify_moderators': request.form.get('notify_moderators') == 'on',
            'notify_admins': request.form.get('notify_admins') == 'on',
            'maintenance_mode': request.form.get('maintenance_mode') == 'on'
        }
        
        current_app.db.settings.update_one(
            {'_id': 'global'},
            {'$set': settings},
            upsert=True
        )
        
        flash('Settings have been updated.', 'success')
        return redirect(url_for('admin.settings'))
    
    settings = current_app.db.settings.find_one({'_id': 'global'}) or {}
    return render_template('admin/settings.html', settings=settings)

@bp.route('/reports/generate', methods=['GET', 'POST'])
@login_required
@admin_required
def generate_report():
    # Get contacts for email sending
    contacts = list(current_app.db.contacts.find())
    
    if request.method == 'POST':
        print('Form data:', request.form)
        print('Start date:', request.form.get('start_date'))
        print('End date:', request.form.get('end_date'))
        print('Category:', request.form.get('category'))
        print('Status:', request.form.get('status'))
        try:
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            # Set time to start and end of day
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
            return redirect(url_for('admin.generate_report'))
        category = request.form.get('category')
        status = request.form.get('status')
        
        # Validate dates
        if start_date > datetime.now():
            flash('Start date cannot be in the future.', 'error')
            return redirect(url_for('admin.generate_report'))
        
        if end_date > datetime.now():
            end_date = datetime.now()
        
        if start_date > end_date:
            flash('Start date must be before end date.', 'error')
            return redirect(url_for('admin.generate_report'))
        
        # Build query
        query = {
            'created_at': {
                '$gte': start_date,
                '$lte': end_date
            },
            'is_deleted': False  # Only include non-deleted posts
        }
        
        # Debug query before filters
        print('Query before filters:', query)
        
        if category and category != 'All Categories' and category != '':
            query['category'] = category
            print('Added category filter:', category)
        
        if status and status != 'All Statuses' and status != '':
            query['status'] = status
            print('Added status filter:', status)
        
        # Debug final query
        print('Final query:', query)
        
        # Debug: Print query and count
        print(f"Query: {query}")
        total_posts = current_app.db.posts.count_documents(query)
        print(f"Total posts matching query: {total_posts}")
        
        # Get posts
        posts = list(current_app.db.posts.find(query).sort('created_at', -1))
        
        # Debug: Print first few posts
        print(f"Found {len(posts)} posts")
        for post in posts[:3]:  # Print first 3 posts for debugging
            print(f"Post: {post['title']}, Category: {post['category']}, Status: {post.get('status')}")
        
        # Get top suggestions for each post
        for post in posts:
            suggestions = list(current_app.db.suggestions.find({
                'post_id': post['_id'],
                'is_deleted': False
            }).sort('upvotes', -1).limit(3))
            
            # Get author information for each suggestion
            for suggestion in suggestions:
                author = current_app.db.users.find_one({'_id': suggestion['author_id']})
                if author:
                    suggestion['author'] = {
                        'username': author['username'],
                        'profile_picture': author.get('profile_picture')
                    }
                else:
                    suggestion['author'] = {
                        'username': '[deleted]',
                        'profile_picture': None
                    }
            
            post['top_suggestions'] = suggestions
        
        # Generate report data
        now = datetime.utcnow()
        report_data = {
            'start_date': start_date,
            'end_date': end_date,
            'category': category,
            'status': status,
            'posts': posts,
            'generated_at': now,
            'created_at': now,  # Add created_at field
            'generated_by': current_user._id
        }
        
        # Save report
        report_id = current_app.db.reports.insert_one(report_data).inserted_id
        
        # If email is requested, send it
        if request.form.get('send_email'):
            contact_id = request.form.get('contact_id')
            if contact_id:
                contact = current_app.db.contacts.find_one({'_id': ObjectId(contact_id)})
                if contact:
                    send_report_email(contact['email'], report_data)
        
        return redirect(url_for('admin.view_report', report_id=report_id))
    
    # Get contacts for the form
    contacts = list(current_app.db.contacts.find())
    
    return render_template('admin/generate_report.html',
                         categories=ALLOWED_CATEGORIES,
                         contacts=contacts)

@bp.route('/reports/<report_id>')
@login_required
@admin_required
def view_report(report_id):
    report = current_app.db.reports.find_one({'_id': ObjectId(report_id)})
    if not report:
        abort(404)
    
    # Get contacts for the send modal
    contacts = list(current_app.db.contacts.find())
    
    return render_template('admin/view_report.html', 
                         report=report,
                         contacts=contacts)

@bp.route('/reports/<report_id>/send', methods=['POST'])
@login_required
@admin_required
def send_report(report_id):
    report = current_app.db.reports.find_one({'_id': ObjectId(report_id)})
    if not report:
        abort(404)
    
    contact_ids = request.form.getlist('contact_ids')
    if not contact_ids:
        flash('Please select at least one contact.', 'error')
        return redirect(url_for('admin.view_report', report_id=report_id))
    
    for contact_id in contact_ids:
        contact = current_app.db.contacts.find_one({'_id': ObjectId(contact_id)})
        if contact:
            send_report_email(contact['email'], report)
    
    flash('Report sent successfully.', 'success')
    return redirect(url_for('admin.view_report', report_id=report_id))

@bp.route('/reports/<report_id>/download')
@login_required
@admin_required
def download_report(report_id):
    report = current_app.db.reports.find_one({'_id': ObjectId(report_id)})
    if not report:
        abort(404)
    
    # Generate CSV content
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Report Details'])
    writer.writerow(['Period', f"{report['start_date'].strftime('%Y-%m-%d')} to {report['end_date'].strftime('%Y-%m-%d')}"])
    writer.writerow(['Category', report.get('category', 'All Categories')])
    writer.writerow(['Status', report.get('status', 'All Statuses')])
    writer.writerow(['Generated', report['generated_at'].strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])  # Empty row for spacing
    
    # Write posts
    writer.writerow(['Posts'])
    writer.writerow(['Title', 'Category', 'Status', 'Created', 'Description'])
    
    for post in report['posts']:
        writer.writerow([
            post['title'],
            post['category'],
            post.get('status', 'N/A'),
            post['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
            post['description']
        ])
        
        # Write top suggestions
        if post.get('top_suggestions'):
            writer.writerow([])  # Empty row for spacing
            writer.writerow(['Top Suggestions'])
            writer.writerow(['Content', 'Upvotes', 'Author'])
            for suggestion in post['top_suggestions']:
                writer.writerow([
                    suggestion['content'],
                    len(suggestion.get('upvotes', [])),
                    suggestion['author']['username']
                ])
        writer.writerow([])  # Empty row between posts
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=report_{report_id}.csv'
        }
    )

@bp.route('/contacts')
@login_required
@admin_required
def contacts():
    contacts = list(current_app.db.contacts.find())
    return render_template('admin/contacts.html', contacts=contacts, categories=ALLOWED_CATEGORIES)

@bp.route('/contacts/add', methods=['POST'])
@login_required
@admin_required
def add_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    category = request.form.get('category')
    
    if not all([name, email, category]):
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('admin.contacts'))
    
    contact_data = {
        'name': name,
        'email': email,
        'category': category,
        'created_at': datetime.utcnow()
    }
    
    current_app.db.contacts.insert_one(contact_data)
    flash('Contact added successfully.', 'success')
    return redirect(url_for('admin.contacts'))

@bp.route('/contacts/<contact_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_contact(contact_id):
    current_app.db.contacts.delete_one({'_id': ObjectId(contact_id)})
    flash('Contact deleted successfully.', 'success')
    return redirect(url_for('admin.contacts'))

def send_report_email(email, report_data):
    """Send report via email"""
    subject = f"Report: {report_data['category'] or 'All Categories'} Posts"
    body = render_template('email/report.html', report=report_data)
    
    msg = Message(
        subject=subject,
        recipients=[email],
        body=body,
        html=body
    )
    
    current_app.mail.send(msg) 