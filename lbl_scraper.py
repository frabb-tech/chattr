#!/usr/bin/env python3
"""
Lebanese Basketball League Live Data Scraper - ENHANCED VERSION
Fetches real-time data including upcoming games, detailed box scores, and statistics
"""

from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import threading
import time
import os

app = Flask(__name__)
CORS(app)

# Global data cache
league_data = {
    'upcoming': [],
    'results': [],
    'standings': [],
    'stats_leaders': {
        'ppg': [],
        'rpg': [],
        'apg': [],
        'spg': [],
        'bpg': []
    },
    'last_updated': None
}

BASE_URL = 'https://www.asia-basket.com'
LEAGUE_URL = f'{BASE_URL}/Lebanon/basketball-League-LBL.aspx'
SCHEDULE_URL = f'{BASE_URL}/Lebanon/Decathlon-Lebanese-Basketball-League-Schedule.aspx'

def scrape_league_data():
    """Scrapes all Lebanese Basketball League data"""
    try:
        print(f"[{datetime.now()}] Fetching data from multiple sources...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Fetch main page
        response = requests.get(LEAGUE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Fetch schedule page for upcoming games
        schedule_response = requests.get(SCHEDULE_URL, headers=headers, timeout=10)
        schedule_response.raise_for_status()
        schedule_soup = BeautifulSoup(schedule_response.content, 'html.parser')
        
        # Scrape all data
        standings = scrape_standings(soup)
        results = scrape_results(soup, schedule_soup)
        upcoming = scrape_upcoming(schedule_soup)
        stats = scrape_stats(soup)
        
        # Update global data
        league_data['standings'] = standings
        league_data['results'] = results
        league_data['upcoming'] = upcoming
        league_data['stats_leaders'] = stats
        league_data['last_updated'] = datetime.now().isoformat()
        
        print(f"[{datetime.now()}] Data updated successfully!")
        print(f"  - Standings: {len(standings)} teams")
        print(f"  - Results: {len(results)} games")
        print(f"  - Upcoming: {len(upcoming)} games")
        
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] Error scraping data: {e}")
        import traceback
        traceback.print_exc()
        return False

def scrape_standings(soup):
    """Extract standings table"""
    standings = []
    
    standings_section = soup.find('table')
    if not standings_section:
        standings_text = soup.find(text=re.compile(r'Standings'))
        if standings_text:
            parent = standings_text.find_parent()
            if parent:
                standings_section = parent.find_next('table')
    
    if standings_section:
        rows = standings_section.find_all('tr')[1:]
        
        for idx, row in enumerate(rows, 1):
            cols = row.find_all('td')
            if len(cols) >= 2:
                team_link = cols[0].find('a') or cols[1].find('a')
                team_name = team_link.text.strip() if team_link else cols[1].text.strip()
                
                record_text = cols[-1].text.strip() if len(cols) > 2 else ''
                wins, losses = 0, 0
                
                if '-' in record_text:
                    parts = record_text.split('-')
                    wins = int(parts[0])
                    losses = int(parts[1])
                
                standings.append({
                    'rank': idx,
                    'team': team_name,
                    'wins': wins,
                    'losses': losses
                })
    
    if not standings:
        standings_text = soup.get_text()
        lines = standings_text.split('\n')
        
        for line in lines:
            match = re.search(r'(\d+)\s+([A-Za-z\s]+?)\s+(\d+)-(\d+)', line)
            if match:
                standings.append({
                    'rank': int(match.group(1)),
                    'team': match.group(2).strip(),
                    'wins': int(match.group(3)),
                    'losses': int(match.group(4))
                })
    
    return standings[:12]

def parse_game_id_from_url(url):
    """Extract game ID from box score URL"""
    if not url:
        return None
    # URL format: /boxScores/Lebanon/2026/0209_2628_2682.aspx
    match = re.search(r'/(\d{4})_(\d+)_(\d+)\.aspx', url)
    if match:
        return f"{match.group(1)}_{match.group(2)}_{match.group(3)}"
    return None

def scrape_results(soup, schedule_soup):
    """Extract recent game results with game IDs and box score URLs"""
    results = []
    
    # Try to find games from schedule page (more reliable)
    games_tables = schedule_soup.find_all('table')
    
    for table in games_tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) >= 4:
                date_text = cols[0].text.strip()
                
                # Match date patterns like "Feb.9:", "zij. 7, 8581"
                if re.match(r'[A-Za-z]{3}\.?\s?\d{1,2}', date_text) or 'zij' in date_text or 'yRM' in date_text:
                    try:
                        # Get team names
                        team1_elem = cols[1].find('img')
                        team2_elem = cols[3].find('img') if len(cols) > 3 else None
                        
                        if team1_elem and team2_elem:
                            home_team = team1_elem.get('alt', '').strip()
                            away_team = team2_elem.get('alt', '').strip()
                            
                            # Get score link
                            score_link = cols[2].find('a') if len(cols) > 2 else None
                            
                            if score_link:
                                score_text = score_link.text.strip()
                                box_score_url = score_link.get('href', '')
                                
                                # Parse score
                                if '-' in score_text:
                                    scores = score_text.strip('[]').split('-')
                                    home_score = int(scores[0])
                                    away_score = int(scores[1])
                                    
                                    # Generate game ID
                                    game_id = parse_game_id_from_url(box_score_url)
                                    
                                    # Clean up date
                                    clean_date = date_text.replace(':', '').replace('.', '').strip()
                                    
                                    results.append({
                                        'date': clean_date,
                                        'homeTeam': home_team,
                                        'homeScore': home_score,
                                        'awayTeam': away_team,
                                        'awayScore': away_score,
                                        'gameId': game_id,
                                        'boxScoreUrl': f"{BASE_URL}{box_score_url}" if box_score_url else None
                                    })
                    except Exception as e:
                        continue
    
    # Fallback to main page
    if not results:
        games_tables = soup.find_all('table')
        
        for table in games_tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                
                if len(cols) >= 4:
                    date_text = cols[0].text.strip()
                    
                    if re.match(r'[A-Za-z]{3}\.?\d{1,2}', date_text):
                        try:
                            home_team = cols[1].text.strip()
                            score_link = cols[2].find('a')
                            away_team = cols[3].text.strip()
                            
                            if score_link:
                                score_text = score_link.text.strip()
                                box_score_url = score_link.get('href', '')
                                
                                if '-' in score_text:
                                    scores = score_text.strip('[]').split('-')
                                    home_score = int(scores[0])
                                    away_score = int(scores[1])
                                    
                                    game_id = parse_game_id_from_url(box_score_url)
                                    
                                    results.append({
                                        'date': date_text,
                                        'homeTeam': home_team,
                                        'homeScore': home_score,
                                        'awayTeam': away_team,
                                        'awayScore': away_score,
                                        'gameId': game_id,
                                        'boxScoreUrl': f"{BASE_URL}{box_score_url}" if box_score_url else None
                                    })
                        except:
                            continue
    
    return results[:30]

def scrape_upcoming(schedule_soup):
    """Extract upcoming games from schedule"""
    upcoming = []
    
    # Look for games without scores (upcoming)
    games_tables = schedule_soup.find_all('table')
    
    for table in games_tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) >= 4:
                date_text = cols[0].text.strip()
                
                # Match date patterns
                if re.match(r'[A-Za-z]{3}\.?\s?\d{1,2}', date_text) or 'yRM' in date_text or 'biQ' in date_text:
                    try:
                        # Get team names from images
                        team1_elem = cols[1].find('img')
                        team2_elem = cols[3].find('img') if len(cols) > 3 else None
                        
                        if team1_elem and team2_elem:
                            home_team = team1_elem.get('alt', '').strip()
                            away_team = team2_elem.get('alt', '').strip()
                            
                            # Check if there's a score link (means game is completed)
                            score_link = cols[2].find('a') if len(cols) > 2 else None
                            
                            # If no score link or text says "Last 10 Games", it's upcoming
                            if not score_link or 'Last 10 Games' in cols[2].text:
                                # Clean up date
                                clean_date = date_text.replace(':', '').replace('.', '').strip()
                                
                                # Try to extract round info
                                round_text = ''
                                round_header = row.find_previous(text=re.compile(r'Round \d+'))
                                if round_header:
                                    round_text = round_header.strip()
                                
                                upcoming.append({
                                    'date': clean_date,
                                    'homeTeam': home_team,
                                    'awayTeam': away_team,
                                    'homeScore': None,
                                    'awayScore': None,
                                    'time': 'TBD',
                                    'round': round_text,
                                    'venue': 'TBD'
                                })
                    except Exception as e:
                        continue
    
    # Remove duplicates
    seen = set()
    unique_upcoming = []
    for game in upcoming:
        key = f"{game['homeTeam']}-{game['awayTeam']}-{game['date']}"
        if key not in seen:
            seen.add(key)
            unique_upcoming.append(game)
    
    return unique_upcoming[:15]

def scrape_stats(soup):
    """Extract stats leaders"""
    stats = {
        'ppg': [],
        'rpg': [],
        'apg': [],
        'spg': [],
        'bpg': []
    }
    
    stat_categories = ['PPG', 'RPG', 'APG', 'SPG', 'BPG']
    
    for category in stat_categories:
        cat_lower = category.lower()
        
        cat_header = soup.find(text=re.compile(category, re.IGNORECASE))
        
        if cat_header:
            parent = cat_header.find_parent()
            if parent:
                player_links = parent.find_all('a', href=re.compile(r'/player/'))
                
                for link in player_links[:5]:
                    player_name = link.text.strip()
                    
                    row = link.find_parent('tr') or link.find_parent('div')
                    if row:
                        text = row.get_text()
                        numbers = re.findall(r'\d+\.?\d*', text)
                        
                        if numbers:
                            value = float(numbers[-1])
                            
                            team = 'Unknown'
                            team_elem = row.find(text=re.compile(r'[A-Z][a-z]+'))
                            if team_elem:
                                team = team_elem.strip()
                            
                            stats[cat_lower].append({
                                'player': player_name,
                                'team': team,
                                'value': value
                            })
    
    return stats

def auto_refresh():
    """Background thread to refresh data periodically"""
    while True:
        scrape_league_data()
        time.sleep(300)  # Refresh every 5 minutes

# API Endpoints

@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        'name': 'Lebanese Basketball League API - Enhanced',
        'version': '2.0',
        'status': 'running',
        'features': [
            'Real upcoming games from schedule',
            'Detailed game results with box score URLs',
            'Game IDs for tracking',
            'Live standings',
            'Statistical leaders'
        ],
        'endpoints': {
            '/api/data': 'Get all data',
            '/api/standings': 'Get standings',
            '/api/results': 'Get results with box scores',
            '/api/upcoming': 'Get upcoming games',
            '/api/stats': 'Get stats leaders',
            '/api/game/<game_id>': 'Get specific game details',
            '/api/refresh': 'Force refresh (POST)',
            '/health': 'Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'last_updated': league_data.get('last_updated', 'never')
    })

@app.route('/api/data', methods=['GET'])
def get_all_data():
    """Get all league data"""
    return jsonify(league_data)

@app.route('/api/standings', methods=['GET'])
def get_standings():
    """Get current standings"""
    return jsonify({
        'standings': league_data['standings'],
        'last_updated': league_data['last_updated']
    })

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get recent results with box score links"""
    return jsonify({
        'results': league_data['results'],
        'last_updated': league_data['last_updated']
    })

@app.route('/api/upcoming', methods=['GET'])
def get_upcoming():
    """Get upcoming games"""
    return jsonify({
        'upcoming': league_data['upcoming'],
        'last_updated': league_data['last_updated']
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get stats leaders"""
    return jsonify({
        'stats_leaders': league_data['stats_leaders'],
        'last_updated': league_data['last_updated']
    })

@app.route('/api/game/<game_id>', methods=['GET'])
def get_game(game_id):
    """Get specific game details by ID"""
    # Search in results
    for game in league_data['results']:
        if game.get('gameId') == game_id:
            return jsonify({
                'game': game,
                'source': 'results'
            })
    
    # Search in upcoming
    for game in league_data['upcoming']:
        game_key = f"{game['homeTeam']}-{game['awayTeam']}"
        if game_key == game_id:
            return jsonify({
                'game': game,
                'source': 'upcoming'
            })
    
    return jsonify({'error': 'Game not found'}), 404

@app.route('/api/refresh', methods=['POST'])
def force_refresh():
    """Force a data refresh"""
    success = scrape_league_data()
    return jsonify({
        'success': success,
        'last_updated': league_data['last_updated']
    })

if __name__ == '__main__':
    print("="*60)
    print("Lebanese Basketball League Live Data Scraper")
    print("ENHANCED VERSION with Detailed Stats")
    print("="*60)
    
    # Initial data fetch
    print("\nFetching initial data...")
    scrape_league_data()
    
    # Start background refresh thread
    refresh_thread = threading.Thread(target=auto_refresh, daemon=True)
    refresh_thread.start()
    print("\nBackground refresh started (every 5 minutes)")
    
    # Get port from environment
    PORT = int(os.environ.get('PORT', 5000))
    
    # Start API server
    print(f"\nStarting API server on port {PORT}")
    print("="*60)
    app.run(host='0.0.0.0', port=PORT, debug=False)
