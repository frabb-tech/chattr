#!/usr/bin/env python3
"""
Lebanese Basketball League Live Data Scraper
Fetches real-time data from asia-basket.com and serves it via a simple API
"""

from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

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

def scrape_league_data():
    """Scrapes all Lebanese Basketball League data"""
    try:
        print(f"[{datetime.now()}] Fetching data from {LEAGUE_URL}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(LEAGUE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Scrape standings
        standings = scrape_standings(soup)
        
        # Scrape recent results
        results = scrape_results(soup)
        
        # Scrape upcoming games
        upcoming = scrape_upcoming(soup)
        
        # Scrape stats leaders
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
        return False

def scrape_standings(soup):
    """Extract standings table"""
    standings = []
    
    # Look for standings section
    standings_section = soup.find('table')
    if not standings_section:
        # Try alternative selector
        standings_text = soup.find(text=re.compile(r'Standings'))
        if standings_text:
            parent = standings_text.find_parent()
            if parent:
                standings_section = parent.find_next('table')
    
    if standings_section:
        rows = standings_section.find_all('tr')[1:]  # Skip header
        
        for idx, row in enumerate(rows, 1):
            cols = row.find_all('td')
            if len(cols) >= 2:
                team_link = cols[0].find('a') or cols[1].find('a')
                team_name = team_link.text.strip() if team_link else cols[1].text.strip()
                
                # Extract record (W-L format)
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
    
    # Fallback: parse from text content
    if not standings:
        standings_text = soup.get_text()
        lines = standings_text.split('\n')
        
        for line in lines:
            # Match patterns like "1 Al Riyadi 8-0"
            match = re.search(r'(\d+)\s+([A-Za-z\s]+?)\s+(\d+)-(\d+)', line)
            if match:
                standings.append({
                    'rank': int(match.group(1)),
                    'team': match.group(2).strip(),
                    'wins': int(match.group(3)),
                    'losses': int(match.group(4))
                })
    
    return standings[:12]  # Top 12 teams

def scrape_results(soup):
    """Extract recent game results"""
    results = []
    
    # Find games table
    games_tables = soup.find_all('table')
    
    for table in games_tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) >= 4:
                # Look for date pattern
                date_text = cols[0].text.strip()
                
                if re.match(r'[A-Za-z]{3}\.?\d{1,2}', date_text):
                    # Found a game row
                    try:
                        home_team = cols[1].text.strip()
                        score_link = cols[2].find('a')
                        away_team = cols[3].text.strip()
                        
                        if score_link:
                            score_text = score_link.text.strip()
                            # Parse score like "80-74"
                            if '-' in score_text:
                                scores = score_text.strip('[]').split('-')
                                home_score = int(scores[0])
                                away_score = int(scores[1])
                                
                                results.append({
                                    'date': date_text,
                                    'homeTeam': home_team,
                                    'homeScore': home_score,
                                    'awayTeam': away_team,
                                    'awayScore': away_score
                                })
                    except:
                        continue
    
    return results[:20]  # Last 20 games

def scrape_upcoming(soup):
    """Extract upcoming games"""
    upcoming = []
    
    # Look for "Next Round Schedule" or upcoming games section
    next_round = soup.find(text=re.compile(r'Next.*Round|Upcoming'))
    
    if next_round:
        parent = next_round.find_parent('table')
        if parent:
            rows = parent.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                
                if len(cols) >= 3:
                    teams = [col.find('a') for col in cols if col.find('a')]
                    
                    if len(teams) >= 2:
                        upcoming.append({
                            'date': cols[0].text.strip() if cols else 'TBD',
                            'homeTeam': teams[0].text.strip(),
                            'awayTeam': teams[1].text.strip(),
                            'homeScore': None,
                            'awayScore': None,
                            'time': 'TBD'
                        })
    
    return upcoming[:5]  # Next 5 games

def scrape_stats(soup):
    """Extract stats leaders"""
    stats = {
        'ppg': [],
        'rpg': [],
        'apg': [],
        'spg': [],
        'bpg': []
    }
    
    # Find stats tables
    stat_categories = ['PPG', 'RPG', 'APG', 'SPG', 'BPG']
    
    for category in stat_categories:
        cat_lower = category.lower()
        
        # Find the category section
        cat_header = soup.find(text=re.compile(category, re.IGNORECASE))
        
        if cat_header:
            # Find the parent container
            parent = cat_header.find_parent()
            if parent:
                # Look for player links in the section
                player_links = parent.find_all('a', href=re.compile(r'/player/'))
                
                for link in player_links[:5]:  # Top 5 players
                    player_name = link.text.strip()
                    
                    # Try to find associated stats
                    row = link.find_parent('tr') or link.find_parent('div')
                    if row:
                        text = row.get_text()
                        # Extract numbers (stats)
                        numbers = re.findall(r'\d+\.?\d*', text)
                        
                        if numbers:
                            value = float(numbers[-1])  # Last number is usually the stat
                            
                            # Try to find team name
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
    """Get recent results"""
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

@app.route('/api/refresh', methods=['POST'])
def force_refresh():
    """Force a data refresh"""
    success = scrape_league_data()
    return jsonify({
        'success': success,
        'last_updated': league_data['last_updated']
    })

@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        'name': 'Lebanese Basketball League API',
        'version': '1.0',
        'endpoints': {
            '/api/data': 'Get all data',
            '/api/standings': 'Get standings',
            '/api/results': 'Get results',
            '/api/upcoming': 'Get upcoming games',
            '/api/stats': 'Get stats leaders',
            '/api/refresh': 'Force refresh (POST)'
        }
    })

if __name__ == '__main__':
    print("="*60)
    print("Lebanese Basketball League Live Data Scraper")
    print("="*60)
    
    # Initial data fetch
    print("\nFetching initial data...")
    scrape_league_data()
    
    # Start background refresh thread
    refresh_thread = threading.Thread(target=auto_refresh, daemon=True)
    refresh_thread.start()
    print("\nBackground refresh started (every 5 minutes)")
    
    # Start API server
    print("\nStarting API server on http://localhost:5000")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=False)
