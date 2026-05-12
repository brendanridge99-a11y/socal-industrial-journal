#!/usr/bin/env python3
"""
SoCal Industrial Journal - Automated News Aggregator
Searches Bloomberg, WSJ, Green Street, Connect CRE, BisNow, CoStar, GlobeSt for IE industrial news
"""

import os
import json
import anthropic
from datetime import datetime, timedelta

# Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', 'YOUR_API_KEY_HERE')
ARTICLES_FILE = 'articles_database.json'
HTML_OUTPUT = 'docs/index.html'
RETENTION_HOURS = 48
YOUR_EMAIL = "Brendan.ridge@jll.com"

print("\n🏭 SoCal Industrial Journal - Auto-Update")
print("=" * 60)

def load_articles():
    """Load existing articles from JSON file"""
    print("📂 Loading existing articles...")
    try:
        with open(ARTICLES_FILE, 'r') as f:
            data = json.load(f)
            print(f"   Found {len(data['articles'])} existing articles")
            return data
    except FileNotFoundError:
        print("   No existing database found, creating new one")
        return {
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "articles": [],
            "settings": {
                "retention_hours": RETENTION_HOURS,
                "sources": ["Bloomberg", "Wall Street Journal", "Green Street", "Connect CRE", "BisNow", "CoStar", "GlobeSt"],
                "update_frequency_hours": 2
            }
        }

def remove_old_articles(data):
    """Remove articles older than retention period"""
    from datetime import timezone
    print("🧹 Removing articles older than 48 hours...")
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=RETENTION_HOURS)
    
    original_count = len(data['articles'])
    data['articles'] = [
        article for article in data['articles']
        if datetime.fromisoformat(article['added_at'].replace('Z', '+00:00')) > cutoff
    ]
    removed_count = original_count - len(data['articles'])
    
    if removed_count > 0:
        print(f"🗑️  Removed {removed_count} articles older than {RETENTION_HOURS} hours")
    
    print(f"   {len(data['articles'])} articles remaining")
    return data

def search_new_articles(existing_articles):
    """Search for new articles using Claude API"""
    
    # SEARCH PAST 24 HOURS - This ensures we get articles!
    time_window = "PAST 24 HOURS"
    hours_back = 24
    
    print(f"🔍 Searching for new articles from {time_window.lower()}...")
    
    # Build prompt
    prompt = f"""Search for the latest news articles published in the {time_window} from these specific sources:
- Bloomberg
- Wall Street Journal  
- Green Street
- Connect CRE
- BisNow
- CoStar
- GlobeSt

Focus on these topics relevant to Southern California industrial real estate (Inland Empire, Los Angeles, Orange County, San Diego):
- Macro economics: Federal Reserve policy, interest rates, inflation, GDP, unemployment, oil prices
- Industrial real estate trends: Cap rates, NOI, rents, absorption, vacancy rates, investment activity
- Supply chain and logistics: Ports activity, shipping, freight, warehouse demand, e-commerce fulfillment
- Business/company news: Major deals, expansions, bankruptcies affecting industrial sector
- Local Southern California developments: Specific IE/LA/OC/SD industrial deals, projects, leases

Categorize each article into ONE of these:
- economics: Fed policy, interest rates, inflation, macro trends, oil/energy prices, financial markets
- industries: Industrial RE trends, cap rates, construction, leasing, investment sales, REIT news
- business: Corporate deals, M&A, earnings reports, business strategy, retail trends, company news
- tech: Technology trends (AI, automation, robotics), supply chain tech, e-commerce platforms, logistics innovation
- politics: Government policy, regulations, infrastructure, trade policy, tariffs, labor law
- supply-chain: Ports, shipping, freight, transportation, trade flows, nearshoring, supply chain disruptions
- local-deals: IE/LA/OC/SD specific real estate deals, leases, developments, local business news

For each article found, return in this exact JSON format:
{{
  "articles": [
    {{
      "headline": "Exact article headline",
      "source": "Source name",
      "source_type": "paywalled or free",
      "date": "May 12, 2026",
      "url": "Direct URL to article",
      "summary": "3-4 sentence detailed summary focusing on implications for IE industrial brokers",
      "category": "economics, industries, business, tech, politics, supply-chain, or local-deals"
    }}
  ]
}}

IMPORTANT: Return ONLY valid JSON with no other text. If no new articles found, return: {{"articles": []}}
"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}]
        )
        
        # Extract text response - handle both text and tool_use blocks
        response_text = ""
        for block in message.content:
            if hasattr(block, 'type') and block.type == "text":
                response_text += block.text
        
        # Debug: print what we got
        print(f"   API response length: {len(response_text)} characters")
        
        if not response_text.strip():
            print("   ⚠️  Empty response from API")
            return []
        
        # Clean up response - remove markdown code blocks
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Extract JSON from response - look for the actual JSON object
        # Claude sometimes adds explanatory text before the JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
        else:
            print("   ⚠️  No JSON object found in response")
            return []
        
        # Parse JSON
        try:
            result = json.loads(json_text)
            articles = result.get('articles', [])
            print(f"   ✅ Found {len(articles)} new articles")
            return articles
        except json.JSONDecodeError as je:
            print(f"   ⚠️  JSON parsing error: {je}")
            print(f"   JSON preview: {json_text[:200]}...")
            return []
        
    except Exception as e:
        print(f"❌ Error searching for articles: {e}")
        import traceback
        traceback.print_exc()
        return []

def generate_article_id(headline, source):
    """Generate unique ID for article"""
    import hashlib
    return hashlib.md5(f"{headline}{source}".encode()).hexdigest()[:12]

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
            print(f"✅ Added: {article['headline'][:60]}...")
    
    if added_count == 0:
        print("   No new articles to add")
    
    return data, added_count

def save_articles(data):
    """Save articles to JSON file"""
    print("💾 Saving articles database...")
    data['last_updated'] = datetime.utcnow().isoformat() + "Z"
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

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
    
    # Convert UTC to Pacific Time for display
    from datetime import timezone, timedelta as td
    utc_now = datetime.now(timezone.utc)
    pacific_offset = td(hours=-8)  # PST is UTC-8
    pacific_now = utc_now + pacific_offset
    
    current_date = pacific_now.strftime('%A, %B %d, %Y')
    current_time = pacific_now.strftime('%I:%M %p PST')
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
            color: #000;
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

# Main execution
def main():
    # Load existing data
    data = load_articles()
    
    # Remove old articles
    data = remove_old_articles(data)
    
    # Search for new articles
    new_articles = search_new_articles(data['articles'])
    
    # Add new articles
    data, added_count = add_new_articles(data, new_articles)
    
    # Save updated database
    save_articles(data)
    
    # Generate HTML
    print("🎨 Generating HTML...")
    html = generate_html(data)
    
    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)
    
    with open(HTML_OUTPUT, 'w') as f:
        f.write(html)
    print(f"   HTML saved to {HTML_OUTPUT}")
    
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print(f"   Total articles: {len(data['articles'])}")
    print(f"   New this run: {added_count}")
    print(f"   Next update: In 2 hours")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
