#!/usr/bin/env python3
"""
SoCal Industrial Journal - Auto-Update Script
Maintains a rolling 48-hour news feed with state tracking
"""

import json
import os
from datetime import datetime, timedelta
from anthropic import Anthropic
import hashlib

# Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', 'YOUR_API_KEY_HERE')
ARTICLES_FILE = 'articles_database.json'
HTML_OUTPUT = 'docs/index.html'
RETENTION_HOURS = 48
YOUR_EMAIL = "Brendan.ridge@jll.com"

# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)

def load_articles():
    """Load existing articles from JSON file"""
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "articles": [],
            "settings": {
                "retention_hours": RETENTION_HOURS,
                "sources": ["Bloomberg", "Wall Street Journal", "Green Street", "Connect CRE", "BisNow", "CoStar", "GlobeSt"],
                "update_frequency_hours": 2
            }
        }

def save_articles(data):
    """Save articles to JSON file"""
    data['last_updated'] = datetime.utcnow().isoformat() + "Z"
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_article_id(headline, source):
    """Generate unique ID for an article"""
    content = f"{headline}-{source}".lower()
    return hashlib.md5(content.encode()).hexdigest()[:16]

def remove_old_articles(data):
    """Remove articles older than retention period"""
    from datetime import timezone
    cutoff = datetime.now(timezone.utc) - timedelta(hours=RETENTION_HOURS)
    
    original_count = len(data['articles'])
    data['articles'] = [
        article for article in data['articles']
        if datetime.fromisoformat(article['added_at'].replace('Z', '+00:00')) > cutoff
    ]
    removed_count = original_count - len(data['articles'])
    
    if removed_count > 0:
        print(f"🗑️  Removed {removed_count} articles older than {RETENTION_HOURS} hours")
    
    return data

def search_new_articles(existing_articles):
    """Search for new articles using Claude API"""
    
    # Determine time window based on current hour
    current_hour = datetime.now().hour
    
    # First scan of day (4am) looks back 10 hours, others look back 2 hours
    if current_hour == 4:
        time_window = "PAST 10 HOURS (since 6pm yesterday)"
        hours_back = 10
    else:
        time_window = "PAST 2 HOURS"
        hours_back = 2
    
    # Build list of existing article headlines to avoid duplicates
    existing_headlines = [article['headline'] for article in existing_articles]
    
    prompt = f"""Search for the latest news articles published in the {time_window} from these specific sources:
- Bloomberg
- Wall Street Journal  
- Green Street
- Connect CRE
- BisNow
- CoStar
- GlobeSt

Focus on topics relevant to Inland Empire industrial real estate professionals, including both direct and indirect/macro topics:

**Direct IE Industrial Topics:**
1. IE/LA/OC/SD industrial real estate deals, leases, developments
2. Warehouse, logistics, and distribution center news
3. Port of Long Beach/LA activity, shipping, freight

**Broader Economic & Business Context:**
4. Macro economic indicators (Fed policy, interest rates, inflation, GDP, employment)
5. Oil prices, fuel costs, energy markets
6. Trade policy, tariffs, international commerce
7. Corporate earnings, M&A activity, business strategy (especially retail, e-commerce, logistics companies)
8. General Southern California business news

**Industry & Technology:**
9. Supply chain trends and disruptions
10. E-commerce and retail trends
11. Technology affecting logistics, automation, AI, robotics
12. Manufacturing and nearshoring trends

**Policy & Politics:**
13. Regulations affecting real estate, logistics, or business
14. Infrastructure spending and development
15. Labor markets and workforce trends
16. Environmental policy, sustainability initiatives

CRITICAL: Only return articles from the {time_window}. Do not include older articles.

AVOID DUPLICATES: Do not include any articles with these headlines (already in database):
{chr(10).join('- ' + h for h in existing_headlines[:50])}

For each NEW article found, categorize into one of these sections:
- economics: Fed policy, interest rates, inflation, GDP, employment, macro economic trends, oil/energy prices
- industries: Industrial RE trends, warehousing, logistics industry, manufacturing, e-commerce sector news
- business: Corporate deals, M&A, earnings reports, business strategy, retail trends, company news
- tech: Technology trends (AI, automation, robotics), supply chain tech, e-commerce platforms, logistics innovation
- politics: Government policy, regulations, infrastructure, trade policy, tariffs, labor law
- supply-chain: Ports, shipping, freight, transportation, trade flows, nearshoring, supply chain disruptions
- local-deals: IE/LA/OC/SD specific real estate deals, leases, developments, local business news

For each NEW article found, return in this exact JSON format:
{{
  "articles": [
    {{
      "headline": "Exact article headline",
      "source": "Source name (Bloomberg, WSJ, Green Street, Connect CRE, or BisNow)",
      "source_type": "paywalled or free",
      "date": "YYYY-MM-DD",
      "url": "Direct URL to article",
      "summary": "3-4 sentence detailed summary focusing on implications for IE industrial brokers",
      "category": "economics, industries, business, tech, politics, supply-chain, or local-deals"
    }}
  ]
}}

Return ONLY valid JSON. If no new articles found, return: {{"articles": []}}
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}]
        )
        
        # Extract text response
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text
        
        # Parse JSON from response
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result.get('articles', [])
        
    except Exception as e:
        print(f"❌ Error searching for articles: {e}")
        return []

def add_new_articles(data, new_articles):
    """Add new articles to database with deduplication"""
    added_count = 0
    current_time = datetime.utcnow().isoformat() + "Z"
    
    existing_ids = {article['id'] for article in data['articles']}
    
    for article in new_articles:
        article_id = generate_article_id(article['headline'], article['source'])
        
        if article_id not in existing_ids:
            article['id'] = article_id
            article['added_at'] = current_time
            article['timestamp'] = article.get('timestamp', current_time)
            data['articles'].append(article)
            added_count += 1
            print(f"✅ Added: {article['headline'][:60]}... ({article['source']})")
    
    return data, added_count

def generate_html(data):
    """Generate HTML from articles database"""
    
    # Group articles by category
    categories = {
        'economics': [],
        'industries': [],
        'business': [],
        'tech': [],
        'politics': [],
        'supply-chain': [],
        'local-deals': []
    }
    
    for article in data['articles']:
        category = article.get('category', 'industries')
        if category in categories:
            categories[category].append(article)
    
    # Sort each category by date (newest first)
    for category in categories:
        categories[category].sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Generate article HTML for different layouts
    def generate_hero_article(article):
        """Generate featured/hero article"""
        is_paywalled = article.get('source_type', 'free') == 'paywalled'
        paywall_badge = ''
        request_access = ''
        
        if is_paywalled:
            paywall_badge = '<span style="background: #fff5f5; color: #c8102e; padding: 0.2rem 0.5rem; font-family: var(--font-sans); font-size: 0.65rem; font-weight: 500; border-radius: 2px; text-transform: uppercase; letter-spacing: 0.05em; border: 1px solid #ffe0e0;">Subscriber only</span>'
            request_access = f'<a href="mailto:{YOUR_EMAIL}" style="font-family: var(--font-sans); color: #c8102e; text-decoration: none; font-weight: 500; font-size: 0.85rem;">Request access</a>'
        
        read_link = f'<a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #000; text-decoration: none; font-weight: 500; font-size: 0.85rem; border-bottom: 1px solid #000; padding-bottom: 2px;">Read full story</a>'
        
        return f'''
        <div style="background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid #c8102e; margin-bottom: 2.5rem; padding: 2.5rem;">
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;">
            <span style="font-family: var(--font-sans); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #c8102e;">{article['source']}</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #999;">•</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #666;">{article['date']}</span>
            {paywall_badge}
          </div>
          
          <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.25rem; font-weight: 400; line-height: 1.2; margin: 0 0 1.25rem; color: #000;">{article['headline']}</h2>
          
          <p style="font-family: Georgia, serif; font-size: 1.1rem; line-height: 1.7; color: #333; margin: 0 0 1rem;">
            {article['summary']}
          </p>
          
          <div style="display: flex; align-items: center; gap: 1.5rem; margin-top: 1.5rem;">
            {read_link}
            {request_access}
          </div>
        </div>'''
    
    def generate_secondary_article(article):
        """Generate secondary article (2-column layout)"""
        is_paywalled = article.get('source_type', 'free') == 'paywalled'
        paywall_badge = ''
        request_access = ''
        
        if is_paywalled:
            paywall_badge = '<span style="background: #fff5f5; color: #c8102e; padding: 0.15rem 0.4rem; font-family: var(--font-sans); font-size: 0.6rem; border-radius: 2px; border: 1px solid #ffe0e0;">🔒</span>'
            request_access = f'<a href="mailto:{YOUR_EMAIL}" style="font-family: var(--font-sans); color: #c8102e; text-decoration: none; font-size: 0.75rem;">Request access →</a>'
        
        read_link = f'<a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #000; text-decoration: none; font-weight: 500; font-size: 0.8rem; border-bottom: 1px solid #000; padding-bottom: 1px;">Continue reading</a>'
        
        links_html = f'<div style="display: flex; align-items: center; gap: 1rem;">{read_link}{request_access}</div>' if request_access else read_link
        
        return f'''
        <div style="border-bottom: 1px solid #e0e0e0; padding-bottom: 1.5rem;">
          <div style="margin-bottom: 0.875rem; display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-family: var(--font-sans); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #c8102e;">{article['source']}</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #999;">• {article['date']}</span>
            {paywall_badge}
          </div>
          
          <h4 style="font-family: Georgia, serif; font-size: 1.35rem; font-weight: 600; line-height: 1.3; margin: 0 0 0.875rem; color: #000;">{article['headline']}</h4>
          
          <p style="font-family: Georgia, serif; font-size: 0.95rem; line-height: 1.65; color: #555; margin: 0 0 1rem;">
            {article['summary']}
          </p>
          
          {links_html}
        </div>'''
    
    def generate_tertiary_article(article):
        """Generate tertiary article (3-column layout)"""
        is_paywalled = article.get('source_type', 'free') == 'paywalled'
        paywall_badge = ''
        request_access_html = ''
        
        if is_paywalled:
            paywall_badge = '<span style="background: #fff5f5; color: #c8102e; padding: 0.15rem 0.4rem; font-family: var(--font-sans); font-size: 0.6rem; border-radius: 2px; border: 1px solid #ffe0e0;">🔒</span>'
            request_access_html = f'''
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
              <a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #000; text-decoration: none; font-weight: 500; font-size: 0.8rem; border-bottom: 1px solid #000; padding-bottom: 1px; display: inline-block; width: fit-content;">Continue reading</a>
              <a href="mailto:{YOUR_EMAIL}" style="font-family: var(--font-sans); color: #c8102e; text-decoration: none; font-size: 0.75rem; display: inline-block; width: fit-content;">Request access →</a>
            </div>'''
        else:
            request_access_html = f'<a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #000; text-decoration: none; font-weight: 500; font-size: 0.8rem; border-bottom: 1px solid #000; padding-bottom: 1px;">Continue reading</a>'
        
        return f'''
        <div>
          <div style="margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-family: var(--font-sans); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #c8102e;">{article['source']}</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #999;">• {article['date']}</span>
            {paywall_badge}
          </div>
          
          <h4 style="font-family: Georgia, serif; font-size: 1.1rem; font-weight: 600; line-height: 1.3; margin: 0 0 0.75rem; color: #000;">{article['headline']}</h4>
          
          <p style="font-family: Georgia, serif; font-size: 0.9rem; line-height: 1.6; color: #555; margin: 0 0 0.75rem;">
            {article['summary']}
          </p>
          
          {request_access_html}
        </div>'''
        """Generate featured/hero article"""
        is_paywalled = article.get('source_type', 'free') == 'paywalled'
        paywall_badge = ''
        request_access = ''
        
        if is_paywalled:
            paywall_badge = '<span style="background: #fffbeb; color: #d4a574; padding: 0.2rem 0.5rem; font-family: var(--font-sans); font-size: 0.65rem; font-weight: 500; border-radius: 2px; text-transform: uppercase; letter-spacing: 0.05em;">Subscriber only</span>'
            request_access = f'<a href="mailto:{YOUR_EMAIL}" style="font-family: var(--font-sans); color: #d4a574; text-decoration: none; font-weight: 500; font-size: 0.85rem;">Request access</a>'
        
        read_link = f'<a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #0a0a0a; text-decoration: none; font-weight: 500; font-size: 0.85rem; border-bottom: 1px solid #0a0a0a; padding-bottom: 2px;">Read full story</a>'
        
        return f'''
        <div style="background: #fff; border: 1px solid #e0e0e0; margin-bottom: 2.5rem; padding: 2.5rem;">
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;">
            <span style="font-family: var(--font-sans); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #d4a574;">{article['source']}</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #999;">•</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #666;">{article['date']}</span>
            {paywall_badge}
          </div>
          
          <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.25rem; font-weight: 400; line-height: 1.2; margin: 0 0 1.25rem; color: #0a0a0a;">{article['headline']}</h2>
          
          <p style="font-family: Georgia, serif; font-size: 1.1rem; line-height: 1.7; color: #333; margin: 0 0 1rem;">
            {article['summary']}
          </p>
          
          <div style="display: flex; align-items: center; gap: 1.5rem; margin-top: 1.5rem;">
            {read_link}
            {request_access}
          </div>
        </div>'''
    
    def generate_secondary_article(article):
        """Generate secondary article (2-column layout)"""
        is_paywalled = article.get('source_type', 'free') == 'paywalled'
        paywall_badge = ''
        request_access = ''
        
        if is_paywalled:
            paywall_badge = '<span style="background: #fffbeb; color: #d4a574; padding: 0.15rem 0.4rem; font-family: var(--font-sans); font-size: 0.6rem; border-radius: 2px;">🔒</span>'
            request_access = f'<a href="mailto:{YOUR_EMAIL}" style="font-family: var(--font-sans); color: #d4a574; text-decoration: none; font-size: 0.75rem;">Request access →</a>'
        
        read_link = f'<a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #0a0a0a; text-decoration: none; font-weight: 500; font-size: 0.8rem; border-bottom: 1px solid #0a0a0a; padding-bottom: 1px;">Continue reading</a>'
        
        links_html = f'<div style="display: flex; align-items: center; gap: 1rem;">{read_link}{request_access}</div>' if request_access else read_link
        
        return f'''
        <div style="border-bottom: 1px solid #e0e0e0; padding-bottom: 1.5rem;">
          <div style="margin-bottom: 0.875rem; display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-family: var(--font-sans); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #d4a574;">{article['source']}</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #999;">• {article['date']}</span>
            {paywall_badge}
          </div>
          
          <h4 style="font-family: Georgia, serif; font-size: 1.35rem; font-weight: 600; line-height: 1.3; margin: 0 0 0.875rem; color: #0a0a0a;">{article['headline']}</h4>
          
          <p style="font-family: Georgia, serif; font-size: 0.95rem; line-height: 1.65; color: #555; margin: 0 0 1rem;">
            {article['summary']}
          </p>
          
          {links_html}
        </div>'''
    
    def generate_tertiary_article(article):
        """Generate tertiary article (3-column layout)"""
        is_paywalled = article.get('source_type', 'free') == 'paywalled'
        paywall_badge = ''
        request_access_html = ''
        
        if is_paywalled:
            paywall_badge = '<span style="background: #fffbeb; color: #d4a574; padding: 0.15rem 0.4rem; font-family: var(--font-sans); font-size: 0.6rem; border-radius: 2px;">🔒</span>'
            request_access_html = f'''
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
              <a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #0a0a0a; text-decoration: none; font-weight: 500; font-size: 0.8rem; border-bottom: 1px solid #0a0a0a; padding-bottom: 1px; display: inline-block; width: fit-content;">Continue reading</a>
              <a href="mailto:{YOUR_EMAIL}" style="font-family: var(--font-sans); color: #d4a574; text-decoration: none; font-size: 0.75rem; display: inline-block; width: fit-content;">Request access →</a>
            </div>'''
        else:
            request_access_html = f'<a href="{article["url"]}" target="_blank" style="font-family: var(--font-sans); color: #0a0a0a; text-decoration: none; font-weight: 500; font-size: 0.8rem; border-bottom: 1px solid #0a0a0a; padding-bottom: 1px;">Continue reading</a>'
        
        return f'''
        <div>
          <div style="margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-family: var(--font-sans); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #d4a574;">{article['source']}</span>
            <span style="font-family: var(--font-sans); font-size: 0.7rem; color: #999;">• {article['date']}</span>
            {paywall_badge}
          </div>
          
          <h4 style="font-family: Georgia, serif; font-size: 1.1rem; font-weight: 600; line-height: 1.3; margin: 0 0 0.75rem; color: #0a0a0a;">{article['headline']}</h4>
          
          <p style="font-family: Georgia, serif; font-size: 0.9rem; line-height: 1.6; color: #555; margin: 0 0 0.75rem;">
            {article['summary']}
          </p>
          
          {request_access_html}
        </div>'''
    
    # Build sections HTML
    section_titles = {
        'economics': 'Economics',
        'industries': 'Industries',
        'business': 'Business',
        'tech': 'Tech',
        'politics': 'Politics',
        'supply-chain': 'Supply Chain & Logistics',
        'local-deals': 'Local Deals & Developments'
    }
    
    sections_html = ''
    for category_key, title in section_titles.items():
        articles = categories[category_key]
        if not articles:
            continue
        
        # Featured article (first one)
        hero_html = generate_hero_article(articles[0]) if len(articles) > 0 else ''
        
        # Secondary articles (next 2, in 2-column layout)
        secondary_articles = articles[1:3]
        secondary_html = ''
        if secondary_articles:
            secondary_cards = '\n'.join(generate_secondary_article(article) for article in secondary_articles)
            secondary_html = f'''
    <div style="border-bottom: 2px solid #c8102e; margin-bottom: 2rem; padding-bottom: 0.5rem;">
      <h3 style="font-family: var(--font-sans); font-size: 0.8rem; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; margin: 0; color: #000;">More in {title}</h3>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2.5rem; margin-bottom: 3rem;">
      {secondary_cards}
    </div>'''
        
        # Tertiary articles (rest, in 3-column layout)
        tertiary_articles = articles[3:]
        tertiary_html = ''
        if tertiary_articles:
            tertiary_cards = '\n'.join(generate_tertiary_article(article) for article in tertiary_articles)
            tertiary_html = f'''
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-bottom: 3rem;">
      {tertiary_cards}
    </div>'''
        
        sections_html += f'''
    <!-- {title} Section -->
    {hero_html}
    {secondary_html}
    {tertiary_html}
'''
    
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p PST')
    total_articles = len(data['articles'])
    
    # Generate navigation with all sections
    nav_items = []
    for category_key, title in section_titles.items():
        if categories[category_key]:
            is_first = category_key == 'economics'
            style = 'color: #c8102e; text-decoration: none; border-bottom: 2px solid #c8102e; padding-bottom: 0.5rem;' if is_first else 'color: #666; text-decoration: none; padding-bottom: 0.5rem;'
            nav_items.append(f'<a href="#{category_key}" style="{style}">{title.split(" & ")[0] if " & " in title else title.split()[0]}</a>')
    
    nav_html = '\n        '.join(nav_items)
    
    # Full HTML template
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoCal Industrial Journal | Daily Brief</title>
    <meta http-equiv="refresh" content="7200">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Georgia, serif;
            background: #fafafa;
            color: #0a0a0a;
            line-height: 1.6;
        }}

        @media (max-width: 768px) {{
            .hero-title {{ font-size: 1.75rem !important; }}
            .secondary-grid {{ grid-template-columns: 1fr !important; }}
            .tertiary-grid {{ grid-template-columns: 1fr !important; }}
            .nav-links {{ flex-wrap: wrap; gap: 1rem !important; }}
        }}
    </style>
</head>
<body>
    <!-- Premium Header -->
    <div style="background: #000; color: #fff; padding: 1.5rem 2rem; border-bottom: 3px solid #c8102e;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h1 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.5rem; font-weight: 400; letter-spacing: -0.02em; margin: 0;">SoCal Industrial Journal</h1>
          <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 0.75rem; color: #999; margin: 0.5rem 0 0; letter-spacing: 0.15em; text-transform: uppercase;">{current_date} • Rolling 48-Hour Brief</p>
        </div>
        <div style="text-align: right; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 0.75rem; color: #999;">
          <div>Last update {current_time}</div>
          <div style="margin-top: 0.25rem;">{total_articles} stories</div>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div style="background: #fff; border-bottom: 1px solid #e0e0e0; padding: 0.875rem 2rem;">
      <div class="nav-links" style="display: flex; gap: 2rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 0.75rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase;">
        {nav_html}
      </div>
    </div>

    <!-- Content Area -->
    <div style="background: #fafafa; padding: 2.5rem 2rem;">
      {sections_html}
    </div>

    <!-- Premium Footer -->
    <div style="background: #000; color: #666; padding: 2rem; text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 0.75rem; border-top: 3px solid #c8102e;">
      <div style="margin-bottom: 0.5rem; color: #999;">SoCal Industrial Journal</div>
      <div style="margin-bottom: 0.75rem;">Bloomberg • WSJ • Green Street • Connect CRE • BisNow • CoStar • GlobeSt</div>
      <div style="font-size: 0.7rem; color: #555;">Rolling 48-hour window • Updates every 2 hours</div>
    </div>

</body>
</html>'''
    
    return html
    """Generate HTML from articles database"""
    
    # Group articles by category
    categories = {
        'economics': [],
        'industries': [],
        'business': [],
        'tech': [],
        'politics': [],
        'supply-chain': [],
        'local-deals': []
    }
    
    for article in data['articles']:
        category = article.get('category', 'industries')
        categories[category].append(article)
    
    # Sort each category by date (newest first)
    for category in categories:
        categories[category].sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Generate article cards HTML
    def generate_article_card(article):
        is_paywalled = article.get('source_type', 'free') == 'paywalled'
        paywall_class = ' paywalled' if is_paywalled else ''
        source_class = ' paywalled' if is_paywalled else ''
        paywall_icon = ' 🔒' if is_paywalled else ''
        
        paywall_notice = ''
        if is_paywalled:
            paywall_notice = f'''
                        <div class="paywall-notice">
                            <div class="paywall-notice-header">📰 Subscription Required</div>
                            <div class="paywall-contact"><a href="mailto:{YOUR_EMAIL}">Contact me for more info</a></div>
                        </div>'''
        
        return f'''
                    <article class="article-card{paywall_class}">
                        <div class="article-meta">
                            <span class="article-source{source_class}">{article['source']}{paywall_icon}</span>
                            <span class="article-date">{article['date']}</span>
                        </div>
                        <h3 class="article-headline">
                            <a href="{article['url']}" target="_blank">{article['headline']}</a>
                        </h3>
                        <p class="article-summary">
                            {article['summary']}
                        </p>
                        <a href="{article['url']}" target="_blank" class="article-link">Read full article</a>{paywall_notice}
                    </article>'''
    
    # Build sections HTML
    section_titles = {
        'economics': 'Economics',
        'industries': 'Industries',
        'business': 'Business',
        'tech': 'Tech',
        'politics': 'Politics',
        'supply-chain': 'Supply Chain & Logistics',
        'local-deals': 'Local Deals & Developments'
    }
    
    sections_html = ''
    for category_key, title in section_titles.items():
        articles = categories[category_key]
        if not articles:
            continue
        
        articles_html = '\n'.join(generate_article_card(article) for article in articles)
        
        sections_html += f'''
            <section id="{category_key}" class="section">
                <div class="section-header">
                    <h2 class="section-title">{title}</h2>
                    <span class="section-count">{len(articles)}</span>
                </div>
                <div class="articles-grid">
{articles_html}
                </div>
            </section>
'''
    
    current_date = datetime.now().strftime('%B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p PST')
    total_articles = len(data['articles'])
    
    # Full HTML template
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoCal Industrial Journal | Daily Brief</title>
    <meta http-equiv="refresh" content="7200">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Work+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --color-primary: #1a1a1a;
            --color-secondary: #4a4a4a;
            --color-accent: #d97706;
            --color-border: #e5e5e5;
            --color-bg: #fafaf9;
            --color-card: #ffffff;
            --font-display: 'Crimson Pro', serif;
            --font-body: 'Work Sans', sans-serif;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--font-body);
            background: var(--color-bg);
            color: var(--color-primary);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }}

        .header {{
            background: var(--color-primary);
            color: white;
            padding: 3rem 0 2rem;
            border-bottom: 4px solid var(--color-accent);
        }}

        .masthead {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 1rem;
        }}

        .site-title {{
            font-family: var(--font-display);
            font-size: 3rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1;
        }}

        .tagline {{
            font-size: 0.95rem;
            color: rgba(255,255,255,0.7);
            margin-top: 0.5rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .date-info {{
            text-align: right;
            font-size: 0.9rem;
            color: rgba(255,255,255,0.8);
        }}

        .date-info .date {{
            font-weight: 600;
            font-size: 1.1rem;
        }}

        .auto-refresh-notice {{
            background: rgba(217, 119, 6, 0.1);
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }}

        .nav {{
            background: white;
            border-bottom: 1px solid var(--color-border);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}

        .nav-links {{
            display: flex;
            gap: 2rem;
            padding: 1rem 0;
            list-style: none;
        }}

        .nav-links a {{
            color: var(--color-secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: color 0.2s;
        }}

        .nav-links a:hover {{
            color: var(--color-accent);
        }}

        .main {{
            padding: 3rem 0;
        }}

        .section {{
            margin-bottom: 4rem;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--color-primary);
        }}

        .section-title {{
            font-family: var(--font-display);
            font-size: 2rem;
            font-weight: 700;
            color: var(--color-primary);
        }}

        .section-count {{
            background: var(--color-accent);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
        }}

        .articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 2rem;
        }}

        .article-card {{
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-radius: 8px;
            padding: 1.75rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .article-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--color-accent);
            transform: scaleY(0);
            transition: transform 0.3s ease;
        }}

        .article-card:hover {{
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            transform: translateY(-2px);
        }}

        .article-card:hover::before {{
            transform: scaleY(1);
        }}

        .article-card.paywalled {{
            border-left: 3px solid #f59e0b;
        }}

        .article-meta {{
            display: flex;
            gap: 1rem;
            align-items: center;
            margin-bottom: 1rem;
            font-size: 0.85rem;
            color: var(--color-secondary);
        }}

        .article-source {{
            font-weight: 600;
            color: var(--color-accent);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .article-source.paywalled {{
            color: #f59e0b;
        }}

        .article-date {{
            color: var(--color-secondary);
        }}

        .article-headline {{
            font-family: var(--font-display);
            font-size: 1.5rem;
            font-weight: 600;
            line-height: 1.3;
            margin-bottom: 1rem;
            color: var(--color-primary);
        }}

        .article-headline a {{
            color: inherit;
            text-decoration: none;
            transition: color 0.2s;
        }}

        .article-headline a:hover {{
            color: var(--color-accent);
        }}

        .article-summary {{
            color: var(--color-secondary);
            line-height: 1.6;
            margin-bottom: 1rem;
            font-size: 0.95rem;
        }}

        .article-link {{
            color: var(--color-accent);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .article-link:hover {{
            text-decoration: underline;
        }}

        .article-link::after {{
            content: '→';
            transition: transform 0.2s;
        }}

        .article-link:hover::after {{
            transform: translateX(4px);
        }}

        .paywall-notice {{
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 4px;
        }}

        .paywall-notice-header {{
            font-weight: 600;
            color: #f59e0b;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .paywall-contact {{
            font-size: 0.9rem;
            color: var(--color-secondary);
            margin-top: 0.5rem;
        }}

        .paywall-contact a {{
            color: var(--color-accent);
            text-decoration: none;
            font-weight: 500;
        }}

        .paywall-contact a:hover {{
            text-decoration: underline;
        }}

        .footer {{
            background: var(--color-primary);
            color: rgba(255,255,255,0.7);
            padding: 2rem 0;
            margin-top: 4rem;
            text-align: center;
            font-size: 0.9rem;
        }}

        .footer-update-info {{
            margin-top: 1rem;
            font-size: 0.85rem;
            color: rgba(255,255,255,0.5);
        }}

        @media (max-width: 768px) {{
            .articles-grid {{
                grid-template-columns: 1fr;
            }}

            .site-title {{
                font-size: 2rem;
            }}

            .masthead {{
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }}

            .nav-links {{
                flex-wrap: wrap;
                gap: 1rem;
            }}
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .article-card {{
            animation: fadeIn 0.6s ease-out;
        }}

        .article-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .article-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .article-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .article-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .article-card:nth-child(5) {{ animation-delay: 0.5s; }}
        .article-card:nth-child(6) {{ animation-delay: 0.6s; }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="masthead">
                <div>
                    <h1 class="site-title">SoCal Industrial Journal</h1>
                    <p class="tagline">Daily Intelligence for Southern California Industrial Real Estate</p>
                </div>
                <div class="date-info">
                    <div class="date">{current_date}</div>
                    <div>Last Updated: {current_time}</div>
                    <div class="auto-refresh-notice">⟳ Updates every 2 hours | {total_articles} articles</div>
                </div>
            </div>
        </div>
    </header>

    <nav class="nav">
        <div class="container">
            <ul class="nav-links">
                <li><a href="#economics">Economics</a></li>
                <li><a href="#industries">Industries</a></li>
                <li><a href="#business">Business</a></li>
                <li><a href="#tech">Tech</a></li>
                <li><a href="#politics">Politics</a></li>
                <li><a href="#supply-chain">Supply Chain</a></li>
                <li><a href="#local-deals">Local Deals</a></li>
            </ul>
        </div>
    </nav>

    <main class="main">
        <div class="container">
{sections_html}
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <p>SoCal Industrial Journal</p>
            <p>Sources: Bloomberg, Wall Street Journal, Green Street, Connect CRE, BisNow</p>
            <div class="footer-update-info">
                Rolling 48-hour window | Articles automatically expire after 2 days | Next update in 2 hours
            </div>
        </div>
    </footer>

</body>
</html>'''
    
    return html

def main():
    """Main execution function"""
    print("\n🏭 SoCal Industrial Journal - Auto-Update")
    print("=" * 60)
    
    # Load existing articles
    print("📂 Loading existing articles...")
    data = load_articles()
    print(f"   Found {len(data['articles'])} existing articles")
    
    # Remove old articles
    print(f"🧹 Removing articles older than {RETENTION_HOURS} hours...")
    data = remove_old_articles(data)
    print(f"   {len(data['articles'])} articles remaining")
    
    # Search for new articles
    print("🔍 Searching for new articles from past 2 hours...")
    new_articles = search_new_articles(data['articles'])
    print(f"   Found {len(new_articles)} new articles")
    
    # Add new articles
    if new_articles:
        print("➕ Adding new articles...")
        data, added_count = add_new_articles(data, new_articles)
        print(f"   Added {added_count} new articles (duplicates filtered)")
    else:
        print("   No new articles to add")
    
    # Save updated articles database
    print("💾 Saving articles database...")
    save_articles(data)
    
    # Generate HTML
    print("🎨 Generating HTML...")
    html = generate_html(data)
    with open(HTML_OUTPUT, 'w') as f:
        f.write(html)
    print(f"   HTML saved to {HTML_OUTPUT}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Update complete!")
    print(f"   Total articles: {len(data['articles'])}")
    print(f"   New this run: {len(new_articles) if new_articles else 0}")
    print(f"   Next update: In 2 hours")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
