import os
import json
import sqlite3
import subprocess
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Twilio SMS functionality removed - manual texting preferred

def get_season_label(date_obj):
    """
    Calculate season based on November 1 - October 31 year.
    Examples:
    - Nov 1, 2024 - Oct 31, 2025 = "2025 Season"
    - Nov 1, 2023 - Oct 31, 2024 = "2024 Season"
    """
    if date_obj.month >= 11:  # November or December
        return f"{date_obj.year + 1} Season"
    else:  # January through October
        return f"{date_obj.year} Season"

# Optional: Refresh the course list every time the app starts
# subprocess.run(["python", "scrape_courses.py"])  # Commented out to avoid startup issues

app = Flask(__name__)

# Secret key for sessions (change this to a random secret key)
app.secret_key = 'pgg-tour-secret-key-2025-golf-scoring-system'

# Clubhouse password
CLUBHOUSE_PASSWORD = 'restorativehealing'

# Admin password for administrative functions
ADMIN_PASSWORD = 'pgg2024'

# Authentication decorator
def require_auth(f):
    """Decorator to require authentication for routes"""
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('clubhouse_entry'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# SMS functionality removed - manual texting preferred

# Force HTTPS in production
@app.before_request
def force_https():
    if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
        if 'localhost' not in request.host and '127.0.0.1' not in request.host:
            return redirect(request.url.replace('http://', 'https://'), code=301)

@app.route("/")
def index():
    """Main entry point - redirect to clubhouse entry if not authenticated"""
    if session.get('authenticated'):
        return redirect(url_for('home'))
    return redirect(url_for('clubhouse_entry'))

@app.route("/clubhouse-entry", methods=["GET", "POST"])
def clubhouse_entry():
    """Clubhouse entry screen with password protection"""

    if request.method == "POST":
        password = request.form.get("password", "").strip()

        if password == CLUBHOUSE_PASSWORD:
            session['authenticated'] = True
            session.permanent = True  # Keep session across browser restarts
            return redirect(url_for('home'))
        else:
            return render_template("entry.html", error="Invalid access code. Please try again.")

    # If already authenticated, go to home
    if session.get('authenticated'):
        return redirect(url_for('home'))

    return render_template("entry.html")

@app.route("/logout")
def logout():
    """Logout and return to clubhouse entry"""
    session.clear()
    return redirect(url_for('clubhouse_entry'))

@app.route("/home")
@require_auth
def home():
    """Dashboard home page with latest updates, leaderboard widget, and upcoming events"""

    # Get current season
    today = datetime.today()
    current_season = get_season_label(today)

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    # Get leaderboard data (top 5) - highest scores first for PGG Tour
    c.execute('''
        SELECT player_name, COUNT(*) as rounds, AVG(total) as avg_score
        FROM scores
        WHERE season = ?
        GROUP BY player_name
        HAVING rounds >= 1
        ORDER BY avg_score DESC
        LIMIT 5
    ''', (current_season,))
    leaderboard_widget = c.fetchall()

    # Get upcoming events (next 3)
    c.execute("""
        SELECT e.event_date, e.event_time, e.course, e.description,
               COUNT(ep.player_id) as participant_count
        FROM events e
        LEFT JOIN event_participants ep ON e.id = ep.event_id
        WHERE e.event_date >= date('now')
        GROUP BY e.id
        ORDER BY e.event_date, e.event_time
        LIMIT 3
    """)
    upcoming_events_widget = c.fetchall()

    # Get recent matches (last 2 complete matches)
    recent_matches = get_recent_matches(c, limit=2)

    # Get hole in one pot data
    c.execute("SELECT SUM(amount_owed) FROM hole_in_one_pot")
    hole_in_one_pot = c.fetchone()[0] or 0

    # Get total rounds played (for pot calculation)
    c.execute("SELECT COUNT(*) FROM scores")
    total_rounds_played = c.fetchone()[0] or 0

    # Get unique players count
    c.execute("SELECT COUNT(DISTINCT player_name) FROM scores")
    unique_players = c.fetchone()[0] or 0

    conn.close()

    return render_template("home.html",
                         season=current_season,
                         leaderboard_widget=leaderboard_widget,
                         upcoming_events_widget=upcoming_events_widget,
                         recent_matches=recent_matches,
                         hole_in_one_pot=hole_in_one_pot,
                         total_rounds_played=total_rounds_played,
                         unique_players=unique_players)

@app.route("/api/live-match-status")
@require_auth
def live_match_status():
    """API endpoint to check if there's a live match in progress"""

    print(f"🔍 Checking live match status...")
    print(f"   - Active scorecard: {session.get('active_scorecard')}")

    # First check if there's an active scorecard session
    if session.get('active_scorecard'):
        scorecard_data = session.get('scorecard_data', {})
        print(f"   - Scorecard data: {len(scorecard_data.get('players', []))} players")

        if scorecard_data.get('players'):
            # Build live data from session
            players_data = []
            max_holes = 0

            for player_data in scorecard_data['players']:
                if player_data.get('name'):
                    total = sum([score for score in player_data.get('holes', []) if score > 0])
                    holes_played = len([score for score in player_data.get('holes', []) if score > 0])
                    max_holes = max(max_holes, holes_played)

                    if total > 0:  # Only include players with scores
                        players_data.append({
                            'name': player_data['name'],
                            'total': total,
                            'holesPlayed': holes_played
                        })

            if players_data:
                # Sort by total score (highest first for PGG Tour)
                players_data.sort(key=lambda x: x['total'], reverse=True)

                # Determine progress text
                if max_holes == 0:
                    progress_text = "Starting Soon"
                elif max_holes == 9:
                    progress_text = "Round Complete"
                else:
                    progress_text = f"Through {max_holes} Hole{'s' if max_holes != 1 else ''}"

                return jsonify({
                    'hasLiveMatch': True,
                    'progressText': progress_text,
                    'players': players_data[:4],  # Top 4 players
                    'holesPlayed': max_holes,
                    'isLive': True  # Flag to indicate this is live data
                })

    # If no active session, check for submitted scores from today
    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    today = datetime.today().strftime('%Y-%m-%d')
    c.execute("""
        SELECT player_name, total,
               hole_1, hole_2, hole_3, hole_4, hole_5, hole_6, hole_7, hole_8, hole_9
        FROM scores
        WHERE date = ?
        ORDER BY total DESC
    """, (today,))

    today_scores = c.fetchall()
    conn.close()

    if not today_scores:
        return jsonify({
            'hasLiveMatch': False,
            'message': 'No match being played'
        })

    # Check if there are any incomplete rounds (holes with 0 scores)
    players_data = []
    max_holes_played = 0

    for row in today_scores:
        player_name, total = row[0], row[1]
        holes = row[2:11]  # holes 1-9

        # Count how many holes have been played
        holes_played = sum(1 for hole in holes if hole > 0)
        max_holes_played = max(max_holes_played, holes_played)

        players_data.append({
            'name': player_name,
            'total': total,
            'holes_played': holes_played
        })

    # Sort by total score (highest first for PGG Tour)
    players_data.sort(key=lambda x: x['total'], reverse=True)

    # Determine progress text
    if max_holes_played == 0:
        progress_text = "Starting Soon"
    elif max_holes_played == 9:
        progress_text = "Round Complete"
    else:
        progress_text = f"Through {max_holes_played} Hole{'s' if max_holes_played != 1 else ''}"

    return jsonify({
        'hasLiveMatch': True,
        'progressText': progress_text,
        'players': players_data[:4],  # Top 4 players
        'holesPlayed': max_holes_played
    })

@app.route("/api/update-live-scorecard", methods=["POST"])
@require_auth
def update_live_scorecard():
    """Update live scorecard data in session"""

    try:
        data = request.get_json()

        # Debug logging
        print(f"📱 Live scorecard update received: {len(data.get('players', []))} players")
        for player in data.get('players', []):
            print(f"   - {player.get('name', 'Unknown')}: {player.get('total', 0)} points")

        # Mark that there's an active scorecard session
        session['active_scorecard'] = True
        session['scorecard_data'] = {
            'players': data.get('players', []),
            'course': data.get('course', ''),
            'nine': data.get('nine', ''),
            'last_updated': datetime.now().isoformat()
        }

        print(f"✅ Session updated - active_scorecard: {session.get('active_scorecard')}")

        return jsonify({'success': True, 'debug': f"Updated {len(data.get('players', []))} players"})

    except Exception as e:
        print(f"❌ Error updating live scorecard: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route("/api/debug-session")
@require_auth
def debug_session():
    """Debug endpoint to check session data"""
    return jsonify({
        'active_scorecard': session.get('active_scorecard', False),
        'has_scorecard_data': bool(session.get('scorecard_data')),
        'player_count': len(session.get('scorecard_data', {}).get('players', [])),
        'session_keys': list(session.keys())
    })

@app.route("/scorecard", methods=["GET", "POST"])
@require_auth
def scorecard():
    if request.method == "POST":
        # Check admin password first
        admin_password = request.form.get("admin_password", "").strip()
        if admin_password != ADMIN_PASSWORD:
            # Redirect back with error message
            return redirect(url_for("scorecard") + "?error=invalid_password")

        date = request.form.get("date")
        if date:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            season = get_season_label(date_obj)
        else:
            season = None
        course = request.form.get("course")
        nine = request.form.get("nine")

        conn = sqlite3.connect("golf_scores.db")
        c = conn.cursor()

        # First pass: Collect all player data
        players_data = []
        for i in range(1, 5):  # Loop through each player
            name = request.form.get(f"player_{i}_name")
            mulligan = request.form.get(f"player_{i}_mulligan")

            if name:  # Only process if player name is provided
                # Gather scores for each hole
                holes = []
                total = 0
                for j in range(1, 10):
                    val = request.form.get(f"player_{i}_hole_{j}")
                    score = int(val) if val else 0
                    holes.append(score)
                    total += score

                players_data.append({
                    'name': name,
                    'mulligan': mulligan,
                    'holes': holes,
                    'total': total
                })

        # Determine winner(s) - highest score wins in PGG Tour
        max_score = max([p['total'] for p in players_data]) if players_data else 0

        # Second pass: Insert data with correct winner status
        for player_data in players_data:
            winner = "Yes" if player_data['total'] == max_score and max_score > 0 else "No"

            # Insert into database
            c.execute('''
                INSERT INTO scores (
                    date, course, nine, player_name, mulligan,
                    hole_1, hole_2, hole_3, hole_4, hole_5,
                    hole_6, hole_7, hole_8, hole_9,
                    total, winner, season
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, course, nine, player_data['name'], player_data['mulligan'],
                *player_data['holes'], player_data['total'], winner, season
            ))

            # Update hole-in-one pot for this player (+$1 per round)
            update_hole_in_one_pot(player_data['name'])

        conn.commit()
        conn.close()

        return redirect(url_for("scorecard"))

    # Load player names from database
    conn_players = sqlite3.connect("golf_scores.db")
    c_players = conn_players.cursor()
    c_players.execute("SELECT name FROM players WHERE active = 1 ORDER BY name")
    players = [row[0] for row in c_players.fetchall()]
    conn_players.close()

    # GET request: Load course list for the dropdown
    with open("static/course_list.json") as f:
        courses = json.load(f)

    # Check for error messages
    error_type = request.args.get('error')
    error_message = None

    if error_type == 'invalid_password':
        error_message = "Invalid admin password. Please try again."

    return render_template("scorecard.html", courses=courses, players=players, error_message=error_message)

@app.route("/leaderboard")
@require_auth
def leaderboard():
    # Step 1: Get the current season based on today's date
    today = datetime.today()
    current_season = get_season_label(today)

    # Step 2: Fetch only rows from that season
    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    c.execute('''
        SELECT player_name, COUNT(*) as rounds, AVG(total) as avg_score
        FROM scores
        WHERE season = ?
        GROUP BY player_name
        HAVING rounds >= 1
        ORDER BY avg_score DESC
    ''', (current_season,))

    leaderboard_data = c.fetchall()
    conn.close()

    # Step 3: Pass season into the template
    return render_template("leaderboard.html", leaderboard=leaderboard_data, season=current_season)

@app.route("/stats")
@require_auth
def stats():
    """Stats page with filtering and comprehensive statistics"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    # Get filter parameters
    season_filter = request.args.get('season', '')
    course_filter = request.args.get('course', '')
    player_filter = request.args.get('player', '')

    # Get all unique values for dropdowns
    c.execute("SELECT DISTINCT season FROM scores WHERE season IS NOT NULL ORDER BY season DESC")
    seasons = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT course FROM scores WHERE course IS NOT NULL AND course != '' ORDER BY course")
    courses = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT player_name FROM scores WHERE player_name IS NOT NULL AND player_name != '' ORDER BY player_name")
    players = [row[0] for row in c.fetchall()]

    # Build WHERE clause based on filters
    where_conditions = []
    params = []

    if season_filter:
        where_conditions.append("season = ?")
        params.append(season_filter)

    if course_filter:
        where_conditions.append("course = ?")
        params.append(course_filter)

    if player_filter:
        where_conditions.append("player_name = ?")
        params.append(player_filter)

    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

    # Get player statistics (without awards to avoid duplication)
    player_stats_query = f"""
        SELECT
            s.player_name,
            COUNT(s.id) as rounds_played,
            AVG(s.total) as avg_score,
            MAX(s.total) as best_score,
            MIN(s.total) as worst_score,
            SUM(CASE WHEN s.winner = 'Yes' THEN 1 ELSE 0 END) as wins,
            COUNT(DISTINCT s.course) as courses_played,
            COUNT(DISTINCT s.season) as seasons_played
        FROM scores s
        {where_clause}
        GROUP BY s.player_name
        ORDER BY s.player_name
    """

    c.execute(player_stats_query, params)
    player_stats = c.fetchall()

    # Get awards count for each player separately
    awards_count_query = f"""
        SELECT a.player_name, COUNT(a.id) as award_count
        FROM awards a
        WHERE a.player_name IN (
            SELECT DISTINCT s.player_name FROM scores s {where_clause}
        )
        GROUP BY a.player_name
    """

    c.execute(awards_count_query, params)
    awards_counts = dict(c.fetchall())

    # Get detailed awards for each player (for the filtered data)
    awards_query = f"""
        SELECT a.player_name, a.season, a.award_category, a.description
        FROM awards a
        WHERE a.player_name IN (
            SELECT DISTINCT s.player_name FROM scores s {where_clause}
        )
        ORDER BY a.player_name, a.season DESC, a.award_category
    """

    c.execute(awards_query, params)
    awards_data = c.fetchall()

    # Group awards by player
    player_awards = {}
    for player_name, season, category, description in awards_data:
        if player_name not in player_awards:
            player_awards[player_name] = []
        player_awards[player_name].append({
            'season': season,
            'category': category,
            'description': description
        })

    # Get recent rounds (last 20)
    recent_rounds_query = f"""
        SELECT date, course, nine, player_name, total, winner, season
        FROM scores
        {where_clause}
        ORDER BY date DESC, id DESC
        LIMIT 20
    """

    c.execute(recent_rounds_query, params)
    recent_rounds = c.fetchall()

    conn.close()

    return render_template("stats.html",
                         player_stats=player_stats,
                         recent_rounds=recent_rounds,
                         seasons=seasons,
                         courses=courses,
                         players=players,
                         player_awards=player_awards,
                         awards_counts=awards_counts,
                         current_filters={
                             'season': season_filter,
                             'course': course_filter,
                             'player': player_filter
                         })

@app.route("/stats/import", methods=["POST"])
def import_scores():
    """Import historical scores data from CSV (password protected)"""

    # Simple password protection
    password = request.form.get("import_password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("stats"))

    # Check if user wants to clear existing data first
    clear_data = request.form.get("clear_existing", "") == "yes"

    scores_data = request.form.get("scores_data", "").strip()

    if not scores_data:
        return redirect(url_for("stats"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    imported_count = 0
    error_count = 0

    try:
        # Clear existing scores if requested
        if clear_data:
            c.execute("DELETE FROM scores")
            print("🗑️ Cleared all existing scores")

        # Parse CSV data: Date,Player,Score,Nine (one line per player per nine)
        lines = scores_data.split('\n')

        # First pass: collect all data by date and nine to determine winners
        rounds_data = {}  # {(date, nine): [(player, score), ...]}

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('Date'):  # Skip empty lines, comments, and header
                continue

            try:
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 3:  # Minimum: date, player, score
                    date = parts[0]
                    player_name = parts[1]
                    try:
                        score = int(parts[2])
                    except ValueError:
                        print(f"⚠️ Invalid score on line {line_num}: {parts[2]}")
                        error_count += 1
                        continue

                    nine = parts[3] if len(parts) > 3 and parts[3] in ['Front', 'Back'] else 'Front'

                    # Calculate season from date
                    try:
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                        season = get_season_label(date_obj)
                    except:
                        # Try different date formats
                        try:
                            date_obj = datetime.strptime(date, '%m/%d/%Y')
                            season = get_season_label(date_obj)
                            date = date_obj.strftime('%Y-%m-%d')  # Convert to standard format
                        except:
                            try:
                                date_obj = datetime.strptime(date, '%m/%d/%y')
                                season = get_season_label(date_obj)
                                date = date_obj.strftime('%Y-%m-%d')  # Convert to standard format
                            except:
                                print(f"⚠️ Invalid date format on line {line_num}: {date}")
                                error_count += 1
                                continue

                    # Group by round (date + nine)
                    round_key = (date, nine)
                    if round_key not in rounds_data:
                        rounds_data[round_key] = []
                    rounds_data[round_key].append((player_name, score, season))

            except Exception as e:
                print(f"⚠️ Error parsing line {line_num} '{line}': {e}")
                error_count += 1

        # Second pass: insert data with correct winner determination
        for (date, nine), players_in_round in rounds_data.items():
            if not players_in_round:
                continue

            # Find winner (highest score in PGG Tour)
            max_score = max(score for _, score, _ in players_in_round)

            # Insert each player's data
            for player_name, score, season in players_in_round:
                winner = "Yes" if score == max_score else "No"

                c.execute('''
                    INSERT INTO scores (
                        date, course, nine, player_name, mulligan,
                        hole_1, hole_2, hole_3, hole_4, hole_5,
                        hole_6, hole_7, hole_8, hole_9,
                        total, winner, season
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date, "Historical Course", nine, player_name, "No",
                    0, 0, 0, 0, 0, 0, 0, 0, 0,  # Individual hole scores not available
                    score, winner, season
                ))

                imported_count += 1

        conn.commit()
        print(f"✅ Import completed: {imported_count} records imported, {error_count} errors")

    except Exception as e:
        print(f"❌ Import failed: {e}")
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for("stats"))

@app.route("/schedule")
@require_auth
def schedule():
    """Schedule page showing upcoming events and admin interface"""

    # Check for error messages
    error_type = request.args.get('error')
    error_message = None

    if error_type == 'invalid_password':
        error_message = "Invalid admin password. Please try again."
    elif error_type == 'missing_fields':
        error_message = "Please fill in all required fields."

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    # Get upcoming events with participant counts
    c.execute("""
        SELECT
            e.id, e.event_date, e.event_time, e.course, e.description,
            e.max_players, e.status,
            COUNT(ep.player_id) as participant_count
        FROM events e
        LEFT JOIN event_participants ep ON e.id = ep.event_id
        WHERE e.event_date >= date('now')
        GROUP BY e.id
        ORDER BY e.event_date, e.event_time
    """)

    upcoming_events = c.fetchall()

    # Get all players for admin interface
    c.execute("SELECT id, name, email FROM players WHERE active = 1 ORDER BY name")
    players = c.fetchall()

    # Load course list for dropdown
    with open("static/course_list.json") as f:
        courses = json.load(f)

    conn.close()

    return render_template("schedule.html",
                         upcoming_events=upcoming_events,
                         players=players,
                         courses=courses,
                         datetime=datetime,
                         error_message=error_message)

@app.route("/schedule/create", methods=["POST"])
@require_auth
def create_event():
    """Create a new scheduled event and send invitations (admin password protected)"""

    # Check admin password
    admin_password = request.form.get("admin_password", "").strip()
    if admin_password != ADMIN_PASSWORD:
        # Redirect back to schedule with error (we'll add error handling)
        return redirect(url_for("schedule") + "?error=invalid_password")

    event_date = request.form.get("event_date")
    event_time = request.form.get("event_time")
    course = request.form.get("course")
    description = request.form.get("description", "")
    selected_players = request.form.getlist("players")

    if not event_date or not selected_players:
        return redirect(url_for("schedule") + "?error=missing_fields")

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        # Create the event
        c.execute("""
            INSERT INTO events (event_date, event_time, course, description, max_players, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_date, event_time, course, description, len(selected_players), "Admin"))

        event_id = c.lastrowid

        # Add participants
        for player_id in selected_players:
            c.execute("""
                INSERT INTO event_participants (event_id, player_id, status)
                VALUES (?, ?, 'invited')
            """, (event_id, player_id))

        conn.commit()

        # Event created successfully - admin can manually text players
        print(f"✅ Event created successfully for {len(selected_players)} players")
        print(f"📅 Event: {event_date} at {event_time}")
        print(f"🏌️ Course: {course}")

        # Get player names for logging
        player_names = []
        for player_id in selected_players:
            c.execute("SELECT name FROM players WHERE id = ?", (player_id,))
            result = c.fetchone()
            if result:
                player_names.append(result[0])

        print(f"👥 Players: {', '.join(player_names)}")
        print("📱 Admin should manually text players about the event")

    except Exception as e:
        print(f"Error creating event: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("schedule"))

# SMS invitation functionality removed - manual texting preferred

@app.route("/players/manage")
def manage_players():
    """Player management page for editing emails and contact info"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    c.execute("SELECT id, name, email, phone, active FROM players ORDER BY name")
    players = c.fetchall()

    conn.close()

    return render_template("manage_players.html", players=players)

@app.route("/players/update", methods=["POST"])
def update_player():
    """Update player information"""

    player_id = request.form.get("player_id")
    email = request.form.get("email")
    phone = request.form.get("phone")

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        c.execute("""
            UPDATE players
            SET email = ?, phone = ?
            WHERE id = ?
        """, (email, phone, player_id))

        conn.commit()

    except Exception as e:
        print(f"Error updating player: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("manage_players"))

@app.route("/roster")
def roster():
    """Roster management page"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    # Get all players with their stats (without awards to avoid duplication)
    c.execute("""
        SELECT
            p.id, p.name, p.email, p.phone, p.active, p.created_date,
            COUNT(s.id) as total_rounds,
            AVG(s.total) as avg_score,
            SUM(CASE WHEN s.winner = 'Yes' THEN 1 ELSE 0 END) as total_wins
        FROM players p
        LEFT JOIN scores s ON p.name = s.player_name
        GROUP BY p.id, p.name, p.email, p.phone, p.active, p.created_date
        ORDER BY p.active DESC, p.name
    """)

    players = c.fetchall()

    # Get awards count for each player separately
    c.execute("""
        SELECT a.player_name, COUNT(a.id) as award_count
        FROM awards a
        GROUP BY a.player_name
    """)
    awards_counts = dict(c.fetchall())

    # Get detailed awards for each player
    c.execute("""
        SELECT a.player_name, a.season, a.award_category, a.description
        FROM awards a
        ORDER BY a.player_name, a.season DESC, a.award_category
    """)

    awards_data = c.fetchall()

    # Group awards by player
    player_awards = {}
    for player_name, season, category, description in awards_data:
        if player_name not in player_awards:
            player_awards[player_name] = []
        player_awards[player_name].append({
            'season': season,
            'category': category,
            'description': description
        })

    conn.close()

    return render_template("roster.html", players=players, player_awards=player_awards, awards_counts=awards_counts)

@app.route("/roster/add", methods=["POST"])
def add_player():
    """Add a new player (admin password protected)"""

    # Check admin password first
    admin_password = request.form.get("admin_password", "").strip()
    if admin_password != ADMIN_PASSWORD:
        # Redirect back with error message
        return redirect(url_for("roster") + "?error=invalid_password")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name:
        return redirect(url_for("roster"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO players (name, email, phone, active)
            VALUES (?, ?, ?, 1)
        """, (name, email or None, phone or None))

        conn.commit()

    except sqlite3.IntegrityError:
        # Player name already exists
        print(f"Player {name} already exists")
    except Exception as e:
        print(f"Error adding player: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("roster"))

@app.route("/roster/update", methods=["POST"])
def update_roster_player():
    """Update player information from roster page"""

    player_id = request.form.get("player_id")
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    active = request.form.get("active") == "1"

    if not player_id or not name:
        return redirect(url_for("roster"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        c.execute("""
            UPDATE players
            SET name = ?, email = ?, phone = ?, active = ?
            WHERE id = ?
        """, (name, email or None, phone or None, active, player_id))

        conn.commit()

    except Exception as e:
        print(f"Error updating player: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("roster"))

@app.route("/roster/delete/<int:player_id>", methods=["POST"])
def delete_player(player_id):
    """Deactivate a player (soft delete)"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        # Soft delete - just mark as inactive
        c.execute("UPDATE players SET active = 0 WHERE id = ?", (player_id,))
        conn.commit()

    except Exception as e:
        print(f"Error deactivating player: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("roster"))

@app.route("/awards")
def awards():
    """Awards page showing winners by season"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    # Get all awards grouped by season (include ID for editing)
    c.execute("""
        SELECT id, season, award_category, player_name, description, award_date
        FROM awards
        ORDER BY season DESC, award_category, player_name
    """)

    all_awards = c.fetchall()

    # Group awards by season
    awards_by_season = {}
    for award_id, season, category, player, description, award_date in all_awards:
        if season not in awards_by_season:
            awards_by_season[season] = []
        awards_by_season[season].append({
            'id': award_id,
            'category': category,
            'player': player,
            'description': description,
            'award_date': award_date
        })

    # Get all players for admin dropdown
    c.execute("SELECT name FROM players WHERE active = 1 ORDER BY name")
    players = [row[0] for row in c.fetchall()]

    # Get distinct award categories for dropdown
    c.execute("SELECT DISTINCT award_category FROM awards ORDER BY award_category")
    categories = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template("awards.html",
                         awards_by_season=awards_by_season,
                         players=players,
                         categories=categories)

@app.route("/awards/add", methods=["POST"])
def add_award():
    """Add a new award (password protected)"""

    # Simple password protection
    password = request.form.get("password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("awards"))

    season = request.form.get("season", "").strip()
    category = request.form.get("category", "").strip()
    custom_category = request.form.get("custom_category", "").strip()
    player_name = request.form.get("player_name", "").strip()
    description = request.form.get("description", "").strip()
    award_date = request.form.get("award_date", "").strip()

    # Use custom category if provided, otherwise use selected category
    final_category = custom_category if custom_category else category

    if not season or not final_category or not player_name:
        return redirect(url_for("awards"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO awards (season, award_category, player_name, description, award_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (season, final_category, player_name, description, award_date, "Admin"))

        conn.commit()
        print(f"✅ Added award: {final_category} to {player_name} for {season}")

    except Exception as e:
        print(f"❌ Error adding award: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("awards"))

@app.route("/awards/import", methods=["POST"])
def import_awards():
    """Import historical awards data (password protected)"""

    # Simple password protection
    password = request.form.get("import_password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("awards"))

    awards_data = request.form.get("awards_data", "").strip()

    if not awards_data:
        return redirect(url_for("awards"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    imported_count = 0
    error_count = 0

    try:
        # Parse CSV-like data: Season,Category,Player,Description,Date
        lines = awards_data.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                continue

            try:
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 3:  # Minimum: season, category, player
                    season = parts[0]
                    category = parts[1]
                    player = parts[2]
                    description = parts[3] if len(parts) > 3 else ""
                    award_date = parts[4] if len(parts) > 4 else ""

                    c.execute("""
                        INSERT INTO awards (season, award_category, player_name, description, award_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (season, category, player, description, award_date, "Import"))

                    imported_count += 1

            except Exception as e:
                print(f"⚠️ Error importing line '{line}': {e}")
                error_count += 1

        conn.commit()
        print(f"✅ Imported {imported_count} awards, {error_count} errors")

    except Exception as e:
        print(f"❌ Error during import: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("awards"))

@app.route("/awards/edit/<int:award_id>", methods=["POST"])
def edit_award(award_id):
    """Edit an existing award (password protected)"""

    # Simple password protection
    password = request.form.get("password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("awards"))

    season = request.form.get("season", "").strip()
    category = request.form.get("category", "").strip()
    custom_category = request.form.get("custom_category", "").strip()
    player_name = request.form.get("player_name", "").strip()
    description = request.form.get("description", "").strip()
    award_date = request.form.get("award_date", "").strip()

    # Use custom category if provided, otherwise use selected category
    final_category = custom_category if custom_category else category

    if not season or not final_category or not player_name:
        return redirect(url_for("awards"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        c.execute("""
            UPDATE awards
            SET season = ?, award_category = ?, player_name = ?, description = ?, award_date = ?
            WHERE id = ?
        """, (season, final_category, player_name, description, award_date, award_id))

        conn.commit()
        print(f"✅ Updated award ID {award_id}: {final_category} to {player_name} for {season}")

    except Exception as e:
        print(f"❌ Error updating award: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("awards"))

@app.route("/awards/delete/<int:award_id>", methods=["POST"])
def delete_award(award_id):
    """Delete an award (password protected)"""

    # Simple password protection
    password = request.form.get("password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("awards"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        # Get award details before deleting for logging
        c.execute("SELECT award_category, player_name, season FROM awards WHERE id = ?", (award_id,))
        award_info = c.fetchone()

        if award_info:
            c.execute("DELETE FROM awards WHERE id = ?", (award_id,))
            conn.commit()
            print(f"✅ Deleted award: {award_info[0]} - {award_info[1]} ({award_info[2]})")

    except Exception as e:
        print(f"❌ Error deleting award: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("awards"))

@app.route("/hole-in-one")
def hole_in_one():
    """Hole-in-one pot tracking and history page"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    # Get current pot status
    c.execute("SELECT SUM(amount_owed) FROM hole_in_one_pot")
    total_pot = c.fetchone()[0] or 0.0

    # Get player balances with paid status
    c.execute("""
        SELECT player_name, amount_owed, total_contributed, paid
        FROM hole_in_one_pot
        ORDER BY amount_owed DESC
    """)
    player_balances = c.fetchall()

    # Get hole-in-one history
    c.execute("""
        SELECT player_name, course, hole_number, event_date, pot_amount, description
        FROM hole_in_one_history
        ORDER BY event_date DESC
    """)
    hole_in_one_history = c.fetchall()

    # Get all players for admin dropdown
    c.execute("SELECT name FROM players WHERE active = 1 ORDER BY name")
    players = [row[0] for row in c.fetchall()]

    # Load course list for dropdown
    with open("static/course_list.json") as f:
        courses = json.load(f)

    conn.close()

    return render_template("hole_in_one.html",
                         total_pot=total_pot,
                         player_balances=player_balances,
                         hole_in_one_history=hole_in_one_history,
                         players=players,
                         courses=courses)

@app.route("/hole-in-one/record", methods=["POST"])
def record_hole_in_one():
    """Record a hole-in-one and reset the pot (password protected)"""

    # Simple password protection
    password = request.form.get("password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("hole_in_one"))

    player_name = request.form.get("player_name", "").strip()
    course = request.form.get("course", "").strip()
    hole_number = request.form.get("hole_number", "").strip()
    event_date = request.form.get("event_date", "").strip()
    description = request.form.get("description", "").strip()

    if not player_name or not course or not hole_number or not event_date:
        return redirect(url_for("hole_in_one"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        # Get current pot total
        c.execute("SELECT SUM(amount_owed) FROM hole_in_one_pot")
        pot_amount = c.fetchone()[0] or 0.0

        # Record the hole-in-one
        c.execute("""
            INSERT INTO hole_in_one_history
            (player_name, course, hole_number, event_date, pot_amount, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (player_name, course, int(hole_number), event_date, pot_amount, description))

        # Reset all player balances and paid status (they've all paid up!)
        c.execute("""
            UPDATE hole_in_one_pot
            SET amount_owed = 0.0,
                original_balance = 0.0,
                paid = 1
        """)

        conn.commit()
        print(f"✅ Recorded hole-in-one: {player_name} won ${pot_amount:.2f} pot!")

    except Exception as e:
        print(f"❌ Error recording hole-in-one: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("hole_in_one"))

@app.route("/hole-in-one/upload-balances", methods=["POST"])
def upload_hole_in_one_balances():
    """Upload current player balances (password protected)"""

    # Simple password protection
    password = request.form.get("password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("hole_in_one"))

    balances_data = request.form.get("balances_data", "").strip()

    if not balances_data:
        return redirect(url_for("hole_in_one"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    updated_count = 0
    error_count = 0

    try:
        # Parse CSV-like data: Player,Amount
        lines = balances_data.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                continue

            try:
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 2:
                    player_name = parts[0]
                    amount = float(parts[1])

                    # Cap at $50
                    amount = min(amount, 50.0)

                    # Update or insert player balance
                    c.execute("""
                        INSERT OR REPLACE INTO hole_in_one_pot
                        (player_name, amount_owed, total_contributed, last_updated)
                        VALUES (?, ?, 0.0, ?)
                    """, (player_name, amount, datetime.now().isoformat()))

                    updated_count += 1
                    print(f"✅ Updated {player_name}: ${amount:.2f}")

            except Exception as e:
                print(f"⚠️ Error importing line '{line}': {e}")
                error_count += 1

        conn.commit()
        print(f"✅ Updated {updated_count} player balances, {error_count} errors")

    except Exception as e:
        print(f"❌ Error during balance upload: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("hole_in_one"))

@app.route("/hole-in-one/toggle-paid/<player_name>", methods=["POST"])
def toggle_paid_status(player_name):
    """Toggle paid status for a player (password protected)"""

    # Simple password protection
    password = request.form.get("password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("hole_in_one"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        # Get current status and original balance
        c.execute("SELECT paid, amount_owed, original_balance FROM hole_in_one_pot WHERE player_name = ?", (player_name,))
        result = c.fetchone()

        if result:
            current_paid, amount_owed, original_balance = result
            new_paid = 1 if current_paid == 0 else 0  # Toggle status

            if new_paid == 1:  # Marking as paid
                # Store original balance and set amount_owed to 0
                c.execute("""
                    UPDATE hole_in_one_pot
                    SET paid = 1,
                        original_balance = ?,
                        amount_owed = 0,
                        last_updated = ?
                    WHERE player_name = ?
                """, (amount_owed, datetime.now().isoformat(), player_name))
                print(f"✅ Marked {player_name} as PAID - ${amount_owed:.2f} balance cleared")
            else:  # Marking as unpaid (restore their original balance)
                c.execute("""
                    UPDATE hole_in_one_pot
                    SET paid = 0,
                        amount_owed = original_balance,
                        last_updated = ?
                    WHERE player_name = ?
                """, (datetime.now().isoformat(), player_name))
                print(f"✅ Marked {player_name} as UNPAID - ${original_balance:.2f} balance restored")

            conn.commit()

    except Exception as e:
        print(f"❌ Error toggling paid status: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("hole_in_one"))

@app.route("/hole-in-one/record-payment", methods=["POST"])
def record_hole_in_one_payment():
    """Record a payment from a player (password protected)"""

    # Simple password protection
    password = request.form.get("password", "")
    if password != ADMIN_PASSWORD:
        return redirect(url_for("hole_in_one"))

    player_name = request.form.get("player_name", "").strip()
    payment_amount = request.form.get("payment_amount", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    if not player_name or not payment_amount:
        return redirect(url_for("hole_in_one"))

    try:
        payment_amount = float(payment_amount)
    except ValueError:
        return redirect(url_for("hole_in_one"))

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        # Get current player balance
        c.execute("SELECT amount_owed, total_contributed FROM hole_in_one_pot WHERE player_name = ?", (player_name,))
        result = c.fetchone()

        if result:
            current_owed, current_contributed = result

            # Calculate new balances
            payment_applied = min(payment_amount, current_owed)  # Can't pay more than owed
            new_owed = current_owed - payment_applied
            new_contributed = current_contributed + payment_applied

            # Update the database
            c.execute("""
                UPDATE hole_in_one_pot
                SET amount_owed = ?, total_contributed = ?, last_updated = ?
                WHERE player_name = ?
            """, (new_owed, new_contributed, datetime.now().isoformat(), player_name))

            conn.commit()
            print(f"✅ Recorded payment: {player_name} paid ${payment_applied:.2f} via {payment_method}")
            print(f"   New balance: Owes ${new_owed:.2f}, Total contributed: ${new_contributed:.2f}")

        else:
            print(f"❌ Player {player_name} not found in hole-in-one pot")

    except Exception as e:
        print(f"❌ Error recording payment: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for("hole_in_one"))

def update_hole_in_one_pot(player_name):
    """Update pot when a player plays a round (called from score entry)"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    try:
        # Check current balance first
        c.execute("SELECT amount_owed FROM hole_in_one_pot WHERE player_name = ?", (player_name,))
        result = c.fetchone()

        if result:
            current_owed = result[0]
            # Only add $1 if they haven't reached the $50 cap
            if current_owed < 50.0:
                new_amount = min(current_owed + 1.0, 50.0)  # Cap at $50
                c.execute("""
                    UPDATE hole_in_one_pot
                    SET amount_owed = ?,
                        original_balance = ?,
                        last_updated = ?
                    WHERE player_name = ?
                """, (new_amount, new_amount, datetime.now().isoformat(), player_name))

                if current_owed + 1.0 >= 50.0:
                    print(f"🎯 {player_name} has reached the $50 cap!")
        else:
            # If player doesn't exist in pot table, create them with $1
            c.execute("""
                INSERT INTO hole_in_one_pot (player_name, amount_owed, total_contributed, original_balance)
                VALUES (?, 1.0, 0.0, 1.0)
            """, (player_name,))

        conn.commit()

    except Exception as e:
        print(f"❌ Error updating hole-in-one pot for {player_name}: {e}")
        conn.rollback()

    finally:
        conn.close()

def get_recent_matches(cursor, limit=2):
    """Get recent complete matches grouped by date, course, and nine"""

    # Get distinct matches (date + course + nine combinations) with scores
    cursor.execute("""
        SELECT DISTINCT date, course, nine
        FROM scores
        WHERE date IS NOT NULL AND course IS NOT NULL AND nine IS NOT NULL
        ORDER BY date DESC, course, nine DESC
        LIMIT ?
    """, (limit * 2,))  # Get more to ensure we have enough complete matches

    match_combinations = cursor.fetchall()

    recent_matches = []

    for date, course, nine in match_combinations:
        if len(recent_matches) >= limit:
            break

        # Get all players for this specific match
        cursor.execute("""
            SELECT player_name, total, winner
            FROM scores
            WHERE date = ? AND course = ? AND nine = ?
            ORDER BY total DESC
        """, (date, course, nine))

        players = cursor.fetchall()

        # Only include matches with at least 2 players
        if len(players) >= 2:
            recent_matches.append({
                'date': date,
                'course': course,
                'nine': nine,
                'players': players
            })

    return recent_matches

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    print("🚀 Starting PGG Tour Flask App...")
    if debug:
        print("📍 Server will be available at: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        print(f"📍 Production server starting on port {port}")
        app.run(debug=False, host='0.0.0.0', port=port)