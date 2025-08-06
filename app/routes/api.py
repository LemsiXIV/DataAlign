from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.logs import LogExecution
from app.models.user import User
from app.models import Projet
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('projets.index'))
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/logs')
@login_required
@admin_required
def all_logs():
    """Affiche tous les logs du système"""
    try:
        # Récupération des paramètres de pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Filtres optionnels
        statut_filter = request.args.get('statut', '')
        projet_filter = request.args.get('projet', '')
        date_filter = request.args.get('date', '')
        
        # Construction de la requête avec filtres
        query = LogExecution.query
        
        if statut_filter:
            query = query.filter(LogExecution.statut == statut_filter)
            
        if projet_filter:
            query = query.filter(LogExecution.projet_id == projet_filter)
            
        if date_filter:
            try:
                date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
                query = query.filter(LogExecution.timestamp >= date_obj,
                                   LogExecution.timestamp < date_obj + timedelta(days=1))
            except ValueError:
                flash('Format de date invalide. Utilisez YYYY-MM-DD', 'error')
        
        # Tri par date décroissante et pagination
        logs = query.order_by(LogExecution.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Récupérer la liste des projets pour le filtre
        projets = Projet.query.all()
        
        # Récupérer les statuts uniques pour le filtre
        statuts = db.session.query(LogExecution.statut).distinct().all()
        statuts = [s[0] for s in statuts if s[0]]
        
        return render_template('all_logs.html', 
                             logs=logs,
                             projets=projets,
                             statuts=statuts,
                             current_filters={
                                 'statut': statut_filter,
                                 'projet': projet_filter,
                                 'date': date_filter
                             })
                             
    except Exception as e:
        flash(f'Erreur lors de la récupération des logs: {str(e)}', 'error')
        return redirect(url_for('projets.index'))

@api_bp.route('/logs/cleanup', methods=['GET', 'POST'])
@login_required
@admin_required
def cleanup_logs():
    """Nettoie les anciens logs"""
    if request.method == 'POST':
        try:
            # Paramètres de nettoyage
            days_to_keep = request.form.get('days_to_keep', 30, type=int)
            max_logs = request.form.get('max_logs', 1000, type=int)
            
            # Validation
            if days_to_keep < 1 or days_to_keep > 365:
                flash('Le nombre de jours doit être entre 1 et 365', 'error')
                return redirect(url_for('api.cleanup_logs'))
                
            if max_logs < 100 or max_logs > 10000:
                flash('Le nombre maximum de logs doit être entre 100 et 10000', 'error')
                return redirect(url_for('api.cleanup_logs'))
            
            # Date de coupure
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Compter les logs à supprimer
            logs_to_delete = LogExecution.query.filter(
                LogExecution.timestamp < cutoff_date
            ).count()
            
            # Garder un nombre minimum de logs même s'ils sont anciens
            total_logs = LogExecution.query.count()
            if total_logs - logs_to_delete < max_logs:
                # Garder les logs les plus récents
                logs_to_keep = LogExecution.query.order_by(
                    LogExecution.timestamp.desc()
                ).limit(max_logs).all()
                
                # IDs des logs à garder
                keep_ids = [log.id for log in logs_to_keep]
                
                # Supprimer tous les autres
                deleted_count = LogExecution.query.filter(
                    ~LogExecution.id.in_(keep_ids)
                ).delete(synchronize_session=False)
            else:
                # Supprimer les logs anciens
                deleted_count = LogExecution.query.filter(
                    LogExecution.timestamp < cutoff_date
                ).delete()
            
            # Sauvegarder les changements
            db.session.commit()
            
            # Log de l'opération de nettoyage
            cleanup_log = LogExecution(
                projet_id=None,
                statut='succès',
                message=f'Nettoyage automatique: {deleted_count} logs supprimés par {current_user.username}'
            )
            db.session.add(cleanup_log)
            db.session.commit()
            
            flash(f'Nettoyage terminé: {deleted_count} logs supprimés', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors du nettoyage: {str(e)}', 'error')
            
        return redirect(url_for('api.cleanup_logs'))
    
    # GET request - afficher la page de nettoyage
    try:
        total_logs = LogExecution.query.count()
        oldest_log = LogExecution.query.order_by(LogExecution.timestamp.asc()).first()
        newest_log = LogExecution.query.order_by(LogExecution.timestamp.desc()).first()
        
        # Statistiques par statut
        success_count = LogExecution.query.filter(LogExecution.statut == 'succès').count()
        error_count = LogExecution.query.filter(LogExecution.statut == 'échec').count()
        warning_count = LogExecution.query.filter(LogExecution.statut == 'avertissement').count()
        
        # Logs récents (dernier mois)
        last_month = datetime.now() - timedelta(days=30)
        recent_logs = LogExecution.query.filter(LogExecution.timestamp >= last_month).count()
        
        stats = {
            'total': total_logs,
            'success': success_count,
            'error': error_count,
            'warning': warning_count,
            'recent': recent_logs,
            'oldest_date': oldest_log.timestamp if oldest_log else None,
            'newest_date': newest_log.timestamp if newest_log else None
        }
        
        return render_template('cleanup_logs.html', stats=stats)
        
    except Exception as e:
        flash(f'Erreur lors de la récupération des statistiques: {str(e)}', 'error')
        return redirect(url_for('projets.index'))

@api_bp.route('/logs/stats')
@login_required
@admin_required
def logs_stats():
    """API endpoint pour les statistiques des logs"""
    try:
        # Statistiques générales
        total_logs = LogExecution.query.count()
        
        # Logs par statut
        success_count = LogExecution.query.filter(LogExecution.statut == 'succès').count()
        error_count = LogExecution.query.filter(LogExecution.statut == 'échec').count()
        warning_count = LogExecution.query.filter(LogExecution.statut == 'avertissement').count()
        
        # Logs par période
        now = datetime.now()
        today = LogExecution.query.filter(
            LogExecution.timestamp >= now.replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        this_week = LogExecution.query.filter(
            LogExecution.timestamp >= now - timedelta(days=7)
        ).count()
        
        this_month = LogExecution.query.filter(
            LogExecution.timestamp >= now - timedelta(days=30)
        ).count()
        
        return jsonify({
            'total': total_logs,
            'by_status': {
                'success': success_count,
                'error': error_count,
                'warning': warning_count
            },
            'by_period': {
                'today': today,
                'this_week': this_week,
                'this_month': this_month
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
