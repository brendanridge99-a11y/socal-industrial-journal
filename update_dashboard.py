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
RETENTION_HOURS = 72
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
    print(f"🧹 Removing articles older than {RETENTION_HOURS} hours...")
    
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

Your goal: Find articles that industrial real estate brokers and their clients need to know. Industrial RE clients include manufacturers, distributors, retailers, e-commerce companies, 3PLs, and logistics operators. They need to understand the ENTIRE business environment affecting their operations and real estate decisions.

**ECONOMICS (macro to micro - everything affecting business conditions):**
- Monetary policy: Fed decisions, interest rates, inflation, money supply, quantitative tightening/easing
- Credit markets: Corporate borrowing costs, bond yields, bank lending, credit availability, debt markets
- Economic indicators: GDP, employment, consumer spending, business investment, PMI, leading indicators
- Currency & commodities: Dollar strength, oil/gas prices, metals, agricultural commodities
- Stock markets: Equity trends, sector rotations, IPOs, market volatility, investor sentiment
- Banking & finance: Bank health, commercial lending, CMBS, financial regulation, fintech
- Consumer trends: Retail sales, consumer confidence, household debt, savings rates
- Global economics: Trade balances, foreign investment, emerging markets, currency crises

**BUSINESS & CORPORATE (all industries - potential tenants/clients):**
- Retail: Store openings/closings, bankruptcies, expansions, same-store sales, omnichannel strategy, department stores, specialty retail, grocery
- E-commerce: Online sales growth, fulfillment strategies, last-mile delivery, marketplace trends, direct-to-consumer brands
- Manufacturing: Production levels, factory orders, capacity utilization, reshoring, automation investments, industry-specific trends
- Food & beverage: Restaurant chains, food production, cold storage needs, grocery distribution, beverage manufacturing
- Consumer goods: CPG companies, brand performance, distribution strategies, inventory management
- Technology: Tech company real estate needs, data center demand, cloud computing, tech layoffs/hiring
- Automotive: Auto sales, EV production, parts distribution, dealer networks, auto logistics
- Healthcare: Medical device manufacturing, pharmaceutical distribution, healthcare supply chain, hospital systems
- Energy: Renewable energy projects, oil/gas operations, energy storage, utilities infrastructure
- Aerospace & defense: Defense contractors, aircraft manufacturing, supply chain, government contracts
- Building materials: Lumber, steel, concrete, construction supplies distribution
- Every M&A deal, expansion, contraction, bankruptcy, restructuring across ALL industries

**SUPPLY CHAIN & LOGISTICS (global to local):**
- Ports & shipping: LA/Long Beach port activity, container volumes, vessel congestion, drayage, rail-to-port connections, port automation, international shipping routes
- Freight & trucking: Truckload rates, driver shortage, fuel costs, trucking company performance, freight volumes, brokerage trends
- Rail: Intermodal volumes, Class I railroad performance, rail infrastructure, inland ports
- Air cargo: Air freight rates, express delivery, airport cargo capacity
- Ocean freight: Container rates, vessel supply, shipping alliances, blank sailings
- Parcel delivery: UPS/FedEx/USPS performance, package volumes, delivery speed wars
- 3PL sector: Third-party logistics companies, warehouse operators, contract logistics trends
- Trade: Import/export volumes, trade agreements, tariff changes, customs, trade tensions, nearshoring/reshoring/friendshoring
- Inventory: Inventory-to-sales ratios, safety stock strategies, just-in-time vs. just-in-case
- Warehouse automation: Robotics, WMS, conveyor systems, AS/RS, picking technology, labor vs. automation economics
- Last-mile: Delivery innovations, urban logistics, micro-fulfillment, dark stores

**TECHNOLOGY (affecting operations & real estate needs):**
- Warehouse tech: Robotics, AGVs, sortation, picking systems, WMS, automation ROI
- AI & machine learning: Demand forecasting, route optimization, inventory management
- E-commerce platforms: Shopify, Amazon, marketplace growth, social commerce
- Transportation tech: Fleet management, route optimization, autonomous vehicles, electric trucks
- Supply chain visibility: Tracking, transparency, IoT, blockchain
- Energy tech: Solar installations on warehouses, EV charging infrastructure, energy efficiency
- Any technology changing how companies produce, store, or distribute products

**POLITICS & POLICY (regulations affecting business & real estate):**
- California: AB5, warehouse regulations, environmental rules, CARB, labor laws, zoning, CEQA, climate mandates
- Federal: Infrastructure bills, tax policy, trade policy, tariffs, business regulations, OSHA, EPA
- Labor: Minimum wage, overtime rules, union activity, gig worker classification, worker safety, WARN Act
- Transportation: Truck emissions, autonomous vehicle regulations, highway funding, rail policy
- Environment: Carbon regulations, clean air standards, water usage, stormwater, solar mandates, EV requirements
- Real estate: Zoning changes, land use, development fees, permitting, affordable housing mandates
- Trade: Tariffs, trade agreements, customs, import/export restrictions, sanctions
- Tax: Property tax, corporate tax, sales tax, tax incentives, opportunity zones
- Local government: City/county decisions on industrial development, tax revenues, municipal bonds

**REAL ESTATE (all CRE sectors - context & comparisons):**
- Industrial: Cap rates, rents, absorption, vacancy, construction starts, land sales, spec development, build-to-suit, sale-leasebacks, 1031 exchanges
- REIT performance: Industrial REITs (Prologis, Duke, etc.) and all CRE REITs for comparison
- Investment sales: Pricing trends, buyer/seller activity, foreign investment, institutional capital
- Construction: Material costs, labor availability, building costs, development timelines, permits
- Office market: Especially conversions to industrial, sublease space, work-from-home impacts on office users potentially needing warehouse space
- Retail real estate: Store closures creating re-tenanting opportunities, retail-to-industrial conversions
- Lending: CMBS, bank lending, life companies, debt funds, loan terms, LTV ratios, interest rate spreads
- Appraisal & valuation: Methodology changes, comparable sales, market data

**LOCAL SOUTHERN CALIFORNIA (IE/LA/OC/SD specific):**
- Industrial deals: Leases, sales, development, land acquisitions in Inland Empire, LA, Orange County, San Diego
- Major employers: Expansions, relocations, closures, hiring/layoffs of significant companies
- Infrastructure: I-10, I-15, SR-60, Ontario Airport, ports, rail, highways, public transit
- Development projects: Specific projects, master plans, business parks, logistics parks
- Economic data: Regional employment, population growth, business climate, economic forecasts
- Local government: City/county decisions affecting industrial development, economic development initiatives
- Demographics: Population shifts, labor force, migration patterns

**SELECTION PHILOSOPHY:**
Cast a WIDE net. Include any article that helps brokers:
- Understand client industries and business conditions
- Anticipate tenant demand or contraction
- Advise clients on market timing
- Contextualize local market within broader trends
- Identify emerging opportunities or risks

If an article affects business operations, consumer behavior, supply chains, regulations, or economic conditions, it's relevant. Brokers need the full picture to serve clients.

EXCLUDE only:
- Pure residential real estate (unless affects industrial market)
- Celebrity/entertainment gossip
- Sports (unless stadium/arena real estate or logistics)
- Arts/culture (unless economic impact)
- Pure political horse-race coverage without policy substance

Categorize each article into ONE of these:
- economics: Fed policy, interest rates, inflation, macro trends, oil/energy, financial markets, banking, economic indicators, consumer trends
- industries: Any real estate news, cap rates, construction, leasing, investment sales, REITs, development, all CRE sectors
- business: Corporate news, M&A, earnings, retail, e-commerce, manufacturing, any industry, expansions, contractions, bankruptcies
- tech: Automation, robotics, AI, e-commerce platforms, supply chain tech, warehouse tech, transportation tech, energy tech
- politics: Government policy, regulations, infrastructure, trade policy, tariffs, labor law, zoning, environmental rules, tax policy
- supply-chain: Ports, shipping, freight, trucking, rail, air cargo, 3PL, trade flows, inventory trends, logistics operations, warehousing
- local-deals: IE/LA/OC/SD specific real estate, business, or economic news, local infrastructure, regional employers, SoCal developments

For each article found, return in this exact JSON format:
{{
  "articles": [
    {{
      "headline": "Exact article headline",
      "source": "Source name",
      "source_type": "paywalled or free",
      "date": "May 12, 2026",
      "url": "Direct URL to article",
      "summary": "3-4 sentence factual summary in neutral journalistic style. Report what happened, who said what, specific numbers/data, and concrete next steps. DO NOT include speculation, implications, analysis, or phrases like 'could impact', 'may affect', 'suggests', 'indicates'. Just report the facts as a news wire would.",
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
    """Generate unique ID for article based on headline and source"""
    import hashlib
    # Normalize headline: lowercase, remove special chars, trim whitespace
    normalized = headline.lower().strip()
    return hashlib.md5(f"{normalized}{source}".encode()).hexdigest()[:12]

def add_new_articles(data, new_articles):
    """Add new articles to database with robust deduplication and date validation"""
    added_count = 0
    skipped_count = 0
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # Calculate cutoff time for article age (72 hours)
    cutoff_time = datetime.utcnow() - timedelta(hours=RETENTION_HOURS)
    
    # Build deduplication sets
    existing_ids = {article['id'] for article in data['articles']}
    existing_urls = {article['url'] for article in data['articles']}
    existing_headlines = {article['headline'].lower().strip() for article in data['articles']}
    
    for article in new_articles:
        article_id = generate_article_id(article['headline'], article['source'])
        article_url = article['url']
        article_headline = article['headline'].lower().strip()
        
        # Check for duplicates by ID, URL, or exact headline
        if article_id in existing_ids:
            skipped_count += 1
            print(f"⏭️  Skipped (duplicate ID): {article['headline'][:50]}...")
            continue
        
        if article_url in existing_urls:
            skipped_count += 1
            print(f"⏭️  Skipped (duplicate URL): {article['headline'][:50]}...")
            continue
            
        if article_headline in existing_headlines:
            skipped_count += 1
            print(f"⏭️  Skipped (duplicate headline): {article['headline'][:50]}...")
            continue
        
        # DATE VALIDATION - Parse article date and check if within retention window
        article_date_str = article.get('date', '')
        try:
            # Try to parse the date (format: "May 12, 2026")
            article_date = datetime.strptime(article_date_str, "%B %d, %Y")
            
            # Check if article is too old
            if article_date < cutoff_time.replace(hour=0, minute=0, second=0, microsecond=0):
                skipped_count += 1
                days_old = (datetime.utcnow() - article_date).days
                print(f"⏭️  Skipped (too old - {days_old} days): {article['headline'][:50]}...")
                continue
        except (ValueError, AttributeError) as e:
            # If date parsing fails, log but still add the article (don't want to lose good articles due to date format issues)
            print(f"⚠️  Warning: Could not parse date '{article_date_str}' for article: {article['headline'][:50]}...")
        
        # Add article if it's genuinely new and recent
        article['id'] = article_id
        article['added_at'] = current_time
        article['timestamp'] = article.get('timestamp', current_time)
        
        data['articles'].append(article)
        existing_ids.add(article_id)
        existing_urls.add(article_url)
        existing_headlines.add(article_headline)
        added_count += 1
        print(f"✅ Added: {article['headline'][:60]}...")
    
    if added_count == 0 and skipped_count == 0:
        print("   No new articles to add")
    elif skipped_count > 0:
        print(f"   Skipped {skipped_count} duplicates/old articles")
    
    return data, added_count

def save_articles(data):
    """Save articles to JSON file"""
    print("💾 Saving articles database...")
    data['last_updated'] = datetime.utcnow().isoformat() + "Z"
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_html(data):
    """Generate magazine-style homepage and category pages"""
    
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
    
    # Helper function to parse article dates for sorting
    def parse_article_date(article):
        date_str = article.get('date', '')
        try:
            return datetime.strptime(date_str, "%B %d, %Y")
        except:
            # If parsing fails, return very old date so article goes to bottom
            return datetime(2000, 1, 1)
    
    # Helper function to calculate article importance score for homepage
    def calculate_importance_score(article):
        """Score articles by importance - higher score = more important"""
        score = 0
        headline = article.get('headline', '').lower()
        source = article.get('source', '').lower()
        
        # Source priority (tier 1 sources get boost)
        if source in ['wall street journal', 'bloomberg', 'wsj']:
            score += 50
        elif source in ['green street', 'costar']:
            score += 30
        else:
            score += 10
        
        # Breaking/major news keywords
        breaking_keywords = ['breaking', 'exclusive', 'major', 'unprecedented', 'historic', 'largest', 'biggest', 'first-ever']
        for keyword in breaking_keywords:
            if keyword in headline:
                score += 30
                break
        
        # High-impact business events
        impact_keywords = ['bankruptcy', 'bankrupt', 'collapse', 'acquisition', 'acquires', 'merger', 'acquires', 'layoff', 'lays off', 'closes', 'shuts down', 'billion', 'million sf', 'record']
        for keyword in impact_keywords:
            if keyword in headline:
                score += 20
                break
        
        # Economic/policy significance
        policy_keywords = ['fed ', 'federal reserve', 'interest rate', 'recession', 'inflation', 'gdp', 'tariff', 'regulation']
        for keyword in policy_keywords:
            if keyword in headline:
                score += 15
                break
        
        # Local SoCal gets boost (very relevant)
        local_keywords = ['inland empire', 'riverside', 'san bernardino', 'ontario', 'fontana', 'moreno valley', 'los angeles', 'orange county', 'san diego']
        for keyword in local_keywords:
            if keyword in headline:
                score += 25
                break
        
        # Recency bonus - newer articles get slight boost
        try:
            article_date = parse_article_date(article)
            days_old = (datetime.now() - article_date).days
            if days_old == 0:  # Today
                score += 15
            elif days_old == 1:  # Yesterday
                score += 10
            elif days_old == 2:  # 2 days ago
                score += 5
        except:
            pass
        
        return score
    
    # Sort each category by date (newest first) for category pages
    for category in categories:
        categories[category].sort(key=parse_article_date, reverse=True)
    
    section_titles = {
        'economics': 'Economics',
        'industries': 'Industries',
        'business': 'Business',
        'tech': 'Tech',
        'politics': 'Politics',
        'supply-chain': 'Supply Chain & Logistics',
        'local-deals': 'Local Deals & Developments'
    }
    
    # Category colors and icons
    category_styles = {
        'economics': {'color': '#c8102e', 'icon': '📊'},
        'industries': {'color': '#1976d2', 'icon': '🏭'},
        'business': {'color': '#388e3c', 'icon': '💼'},
        'tech': {'color': '#7b1fa2', 'icon': '🔬'},
        'politics': {'color': '#f57c00', 'icon': '⚖️'},
        'supply-chain': {'color': '#795548', 'icon': '📦'},
        'local-deals': {'color': '#f9a825', 'icon': '🏢'}
    }
    
    # Calculate Pacific time
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    
    # DST check for Pacific time
    year = utc_now.year
    month = utc_now.month
    
    if 3 < month < 11:
        is_dst = True
    elif month == 3:
        is_dst = utc_now.day > 14
    elif month == 11:
        is_dst = utc_now.day <= 7
    else:
        is_dst = False
    
    pacific_offset = timedelta(hours=-7 if is_dst else -8)
    pacific_now = utc_now + pacific_offset
    time_zone_abbr = 'PDT' if is_dst else 'PST'
    
    current_date = pacific_now.strftime('%A, %B %d, %Y')
    total_articles = len(data['articles'])
    
    # Generate fixed header HTML (used on all pages)
    def generate_header(active_page='home'):
        nav_items = []
        for cat_key, cat_title in section_titles.items():
            short_title = cat_title.split(' & ')[0] if ' & ' in cat_title else cat_title.split()[0]
            nav_items.append(f'<a href="{cat_key}.html" style="font-family: -apple-system, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: #666; text-decoration: none;">{short_title}</a>')
        
        nav_html = '\n        '.join(nav_items)
        
        return f'''
  <div style="position: fixed; top: 0; left: 0; right: 0; background: #000; color: #fff; z-index: 1000; border-bottom: 3px solid #c8102e; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="text-align: center; padding: 1.5rem 2rem 1rem;">
      <a href="index.html" style="text-decoration: none; color: inherit;">
        <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 2rem; font-weight: 400; letter-spacing: -0.02em; margin-bottom: 0.5rem;">SoCal Industrial Journal</div>
      </a>
      <div style="font-size: 0.7rem; color: #999; letter-spacing: 0.15em; text-transform: uppercase;">{current_date} • Rolling 72-Hour Brief</div>
    </div>
    
    <div style="background: #fff; border-top: 1px solid #333; padding: 0.75rem 2rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
      <a href="index.html" style="font-family: -apple-system, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: {'#c8102e' if active_page == 'home' else '#666'}; text-decoration: none;">Home</a>
      {nav_html}
    </div>
  </div>'''
    
    # Generate homepage with category cards
    def generate_homepage():
        cards_html = ''
        empty_categories = []
        
        for cat_key, cat_title in section_titles.items():
            articles = categories[cat_key]
            article_count = len(articles)
            style = category_styles[cat_key]
            cat_color = style['color']
            cat_icon = style['icon']
            
            if article_count == 0:
                # Track empty categories but don't show them on homepage
                empty_categories.append(cat_title)
                continue
            else:
                # Select most important article for homepage (not just first/newest)
                # Score each article and pick the highest
                articles_with_scores = [(article, calculate_importance_score(article)) for article in articles]
                articles_with_scores.sort(key=lambda x: x[1], reverse=True)
                top_article = articles_with_scores[0][0]  # Get article with highest score
                
                # Truncate summary to 2 lines worth of text (~150 chars)
                summary = top_article['summary']
                if len(summary) > 150:
                    summary = summary[:150] + '...'
                
                # Calculate hover shadow color (lighter version of category color)
                hover_shadow = f'0 4px 12px rgba{tuple(int(cat_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.15,)}'.replace('(', '(').replace(')', ')')
                
                cards_html += f'''
    <a href="{cat_key}.html" style="background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid {cat_color}; padding: 2rem; cursor: pointer; text-decoration: none; color: inherit; display: block; transition: all 0.2s;" onmouseover="this.style.borderLeftWidth='6px'; this.style.boxShadow='{hover_shadow}'; this.style.transform='translateY(-2px)';" onmouseout="this.style.borderLeftWidth='4px'; this.style.boxShadow='none'; this.style.transform='translateY(0)';">
      <div style="font-family: -apple-system, sans-serif; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: {cat_color}; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
        {cat_icon} {cat_title}
        <span style="background: {cat_color}; color: #fff; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.65rem; font-weight: 600;">{article_count} {'story' if article_count == 1 else 'stories'}</span>
      </div>
      <h2 style="font-family: Georgia, serif; font-size: 1.5rem; font-weight: 700; line-height: 1.25; color: #000; margin-bottom: 0.75rem;">{top_article['headline']}</h2>
      <div style="font-family: -apple-system, sans-serif; font-size: 0.75rem; color: #999; margin-bottom: 1rem;">{top_article['source']} • {top_article['date']}</div>
      <p style="font-family: Georgia, serif; font-size: 0.9rem; line-height: 1.6; color: #555; margin-bottom: 1rem;">{summary}</p>
      <div style="font-family: -apple-system, sans-serif; font-size: 0.8rem; font-weight: 500; color: {cat_color};">View all {cat_title} stories →</div>
    </a>
'''
        
        # Add empty categories notice if any
        empty_notice = ''
        if empty_categories:
            empty_list = ', '.join(empty_categories)
            empty_notice = f'''
  <div style="text-align: center; margin: 3rem 0; padding: 1.5rem; background: #f5f5f5; border-radius: 8px;">
    <p style="font-size: 0.9rem; color: #666;">
      {empty_list} {'category has' if len(empty_categories) == 1 else 'categories have'} no stories yet. Check back soon for updates.
    </p>
  </div>'''
        
        # Calculate "updated X ago" timestamp
        last_update_time = data.get('last_updated', datetime.utcnow().isoformat() + "Z")
        last_update_dt = datetime.fromisoformat(last_update_time.replace('Z', '+00:00'))
        now_utc = datetime.now(timezone.utc)
        time_diff = now_utc - last_update_dt
        
        minutes_ago = int(time_diff.total_seconds() / 60)
        if minutes_ago < 60:
            time_ago = f"{minutes_ago} minute{'s' if minutes_ago != 1 else ''} ago"
        else:
            hours_ago = int(minutes_ago / 60)
            time_ago = f"{hours_ago} hour{'s' if hours_ago != 1 else ''} ago"
        
        active_categories = len([cat for cat in categories.values() if len(cat) > 0])
        
        homepage_html = f'''<!DOCTYPE html>
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

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: Georgia, serif;
            background: #fafafa;
            color: #000;
            line-height: 1.6;
            padding-top: 160px;
        }}

        @media (max-width: 768px) {{
            body {{ padding-top: 180px; }}
            .category-grid {{ grid-template-columns: 1fr !important; }}
        }}
    </style>
</head>
<body>
{generate_header('home')}

<div style="max-width: 1200px; margin: 0 auto; padding: 2rem;">
  
  <div style="text-align: center; margin-bottom: 3rem;">
    <h1 style="font-family: Georgia, serif; font-size: 1.5rem; font-weight: 600; color: #000; margin-bottom: 0.5rem;">Today's Top Stories</h1>
    <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
      <p style="font-size: 0.95rem; color: #666;">{total_articles} stories across {active_categories} categories</p>
      <span style="background: #e8f5e9; color: #2e7d32; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">Updated {time_ago}</span>
    </div>
  </div>

  <div class="category-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 2rem; margin-bottom: 3rem;">
    {cards_html}
  </div>

  {empty_notice}

  <div style="background: #000; color: #666; padding: 2rem; text-align: center; font-family: -apple-system, sans-serif; font-size: 0.75rem; border-top: 3px solid #c8102e; margin-top: 3rem;">
    <div style="margin-bottom: 0.5rem; color: #999;">SoCal Industrial Journal</div>
    <div style="margin-bottom: 0.75rem;">Bloomberg • Wall Street Journal • Green Street • Connect CRE • BisNow • CoStar • GlobeSt</div>
    <div style="font-size: 0.7rem; color: #555;">Rolling 72-hour window • Updates every 2 hours</div>
  </div>

</div>

</body>
</html>'''
        return homepage_html
        homepage_html = f'''<!DOCTYPE html>
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

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: Georgia, serif;
            background: #fafafa;
            color: #000;
            line-height: 1.6;
            padding-top: 160px;
        }}

        @media (max-width: 768px) {{
            body {{ padding-top: 180px; }}
            .category-grid {{ grid-template-columns: 1fr !important; }}
        }}
    </style>
</head>
<body>
{generate_header('home')}

<div style="max-width: 1200px; margin: 0 auto; padding: 2rem;">
  
  <div style="text-align: center; margin-bottom: 3rem;">
    <h1 style="font-family: Georgia, serif; font-size: 1.5rem; font-weight: 600; color: #000; margin-bottom: 0.5rem;">Today's Top Stories</h1>
    <p style="font-size: 0.95rem; color: #666;">{total_articles} stories across 7 categories • Updated every 2 hours</p>
  </div>

  <div class="category-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 2rem; margin-bottom: 3rem;">
    {cards_html}
  </div>

  <div style="background: #000; color: #666; padding: 2rem; text-align: center; font-family: -apple-system, sans-serif; font-size: 0.75rem; border-top: 3px solid #c8102e; margin-top: 3rem;">
    <div style="margin-bottom: 0.5rem; color: #999;">SoCal Industrial Journal</div>
    <div style="margin-bottom: 0.75rem;">Bloomberg • Wall Street Journal • Green Street • Connect CRE • BisNow • CoStar • GlobeSt</div>
    <div style="font-size: 0.7rem; color: #555;">Rolling 72-hour window • Updates every 2 hours</div>
  </div>

</div>

</body>
</html>'''
        return homepage_html
    
    # Generate category page
    def generate_category_page(cat_key, cat_title):
        articles = categories[cat_key]
        style = category_styles[cat_key]
        cat_color = style['color']
        cat_icon = style['icon']
        
        if len(articles) == 0:
            articles_html = f'''
    <div style="background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid {cat_color}; padding: 3rem; text-align: center; margin-bottom: 2rem;">
      <h2 style="font-family: Georgia, serif; font-size: 1.5rem; color: #999; margin-bottom: 0.5rem;">No stories yet in this category</h2>
      <p style="font-family: Georgia, serif; font-size: 0.95rem; color: #999;">Check back soon for the latest updates</p>
    </div>'''
        else:
            article_cards = []
            for article in articles:
                is_paywalled = article.get('source_type', 'free') == 'paywalled'
                paywall_badge = ''
                request_access = ''
                
                if is_paywalled:
                    paywall_badge = f'<span style="background: #fff5f5; color: {cat_color}; padding: 0.15rem 0.4rem; font-family: -apple-system, sans-serif; font-size: 0.6rem; border-radius: 2px; border: 1px solid #ffe0e0; margin-left: 0.5rem;">🔒</span>'
                    request_access = f'<a href="mailto:{YOUR_EMAIL}" style="font-family: -apple-system, sans-serif; color: {cat_color}; text-decoration: none; font-size: 0.85rem; margin-left: 1.5rem;">Request access →</a>'
                
                article_cards.append(f'''
    <div style="background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid {cat_color}; padding: 2rem; margin-bottom: 1.5rem;">
      <div style="margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
        <span style="font-family: -apple-system, sans-serif; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: {cat_color};">{article['source']}</span>
        <span style="font-family: -apple-system, sans-serif; font-size: 0.7rem; color: #999;">• {article['date']}</span>
        {paywall_badge}
      </div>
      
      <h3 style="font-family: Georgia, serif; font-size: 1.75rem; font-weight: 700; line-height: 1.3; margin: 0 0 1rem; color: #000;">{article['headline']}</h3>
      
      <p style="font-family: Georgia, serif; font-size: 1rem; line-height: 1.7; color: #333; margin: 0 0 1.25rem;">
        {article['summary']}
      </p>
      
      <div style="display: flex; align-items: center;">
        <a href="{article['url']}" target="_blank" style="font-family: -apple-system, sans-serif; color: #000; text-decoration: none; font-weight: 500; font-size: 0.85rem; border-bottom: 1px solid #000; padding-bottom: 2px;">Read full story</a>
        {request_access}
      </div>
    </div>''')
            
            articles_html = '\n'.join(article_cards)
        
        page_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cat_title} | SoCal Industrial Journal</title>
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

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: Georgia, serif;
            background: #fafafa;
            color: #000;
            line-height: 1.6;
            padding-top: 160px;
        }}

        @media (max-width: 768px) {{
            body {{ padding-top: 180px; }}
        }}
    </style>
</head>
<body>
{generate_header(cat_key)}

<div style="max-width: 900px; margin: 0 auto; padding: 2rem;">
  
  <div style="margin-bottom: 3rem;">
    <a href="index.html" style="font-family: -apple-system, sans-serif; font-size: 0.8rem; color: {cat_color}; text-decoration: none; margin-bottom: 1rem; display: inline-block;">← Back to Home</a>
    <h1 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.5rem; font-weight: 400; color: #000; margin-bottom: 0.5rem;">{cat_icon} {cat_title}</h1>
    <p style="font-size: 0.95rem; color: #666;">{len(articles)} {'story' if len(articles) == 1 else 'stories'}</p>
  </div>

  {articles_html}

  <div style="background: #000; color: #666; padding: 2rem; text-align: center; font-family: -apple-system, sans-serif; font-size: 0.75rem; border-top: 3px solid #c8102e; margin-top: 3rem;">
    <div style="margin-bottom: 0.5rem; color: #999;">SoCal Industrial Journal</div>
    <div style="margin-bottom: 0.75rem;">Bloomberg • Wall Street Journal • Green Street • Connect CRE • BisNow • CoStar • GlobeSt</div>
    <div style="font-size: 0.7rem; color: #555;">Rolling 72-hour window • Updates every 2 hours</div>
  </div>

</div>

</body>
</html>'''
        return page_html
    
    # Generate all pages
    print("📄 Generating homepage...")
    homepage = generate_homepage()
    
    # Write homepage
    import os
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(homepage)
    print("   ✓ Homepage created")
    
    # Generate category pages
    print("📄 Generating category pages...")
    for cat_key, cat_title in section_titles.items():
        page_html = generate_category_page(cat_key, cat_title)
        with open(f'docs/{cat_key}.html', 'w', encoding='utf-8') as f:
            f.write(page_html)
        print(f"   ✓ {cat_title} page created ({len(categories[cat_key])} articles)")
    
    print(f"✅ Generated 8 HTML pages (1 homepage + 7 category pages)")
    
    return homepage  # Return homepage HTML for compatibility
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
        
        # If no articles in this section, show placeholder
        if not articles:
            sections_html += f'''
    <!-- {title} Section -->
    <section id="{category_key}">
      <div style="background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid #c8102e; margin-bottom: 2.5rem; padding: 2.5rem; text-align: center;">
        <h3 style="font-family: Georgia, serif; font-size: 1.5rem; color: #999; margin-bottom: 0.5rem;">No stories yet in {title}</h3>
        <p style="font-family: Georgia, serif; font-size: 0.95rem; color: #999;">Check back soon for the latest updates</p>
      </div>
    </section>
'''
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
    <section id="{category_key}">
    {hero_html}
    {secondary_html}
    {tertiary_html}
    </section>
'''
    
    # Convert UTC to Pacific Time for display (handles PST/PDT automatically)
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    
    # Calculate Pacific offset based on current date (handles DST automatically)
    # Pacific is UTC-8 (PST) or UTC-7 (PDT)
    # Simple DST check: second Sunday in March to first Sunday in November
    year = utc_now.year
    month = utc_now.month
    
    # Rough DST check (March-November is usually PDT)
    if 3 < month < 11:  # April through October
        is_dst = True
    elif month == 3:  # March - check if past second Sunday
        is_dst = utc_now.day > 14
    elif month == 11:  # November - check if before first Sunday
        is_dst = utc_now.day <= 7
    else:
        is_dst = False
    
    pacific_offset = timedelta(hours=-7 if is_dst else -8)
    pacific_now = utc_now + pacific_offset
    time_zone_abbr = 'PDT' if is_dst else 'PST'
    
    current_date = pacific_now.strftime('%A, %B %d, %Y')
    total_articles = len(data['articles'])
    
    # Generate navigation with all sections (even empty ones)
    nav_items = []
    for category_key, title in section_titles.items():
        is_first = category_key == 'economics'
        # Dim the color if section is empty
        has_articles = len(categories[category_key]) > 0
        if is_first:
            style = 'color: #c8102e; text-decoration: none; border-bottom: 2px solid #c8102e; padding-bottom: 0.5rem;'
        elif has_articles:
            style = 'color: #666; text-decoration: none; padding-bottom: 0.5rem;'
        else:
            style = 'color: #ccc; text-decoration: none; padding-bottom: 0.5rem;'  # Lighter for empty sections
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

        html {{
            scroll-behavior: smooth;
            scroll-padding-top: 6rem;
        }}

        body {{
            font-family: Georgia, serif;
            background: #fafafa;
            color: #000;
            line-height: 1.6;
        }}

        section {{
            scroll-margin-top: 2rem;
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
          <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 0.75rem; color: #999; margin: 0.5rem 0 0; letter-spacing: 0.15em; text-transform: uppercase;">{current_date} • Rolling 72-Hour Brief</p>
        </div>
        <div style="text-align: right; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 0.75rem; color: #999;">
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
      <div style="font-size: 0.7rem; color: #555;">Rolling 72-hour window • Updates every 2 hours</div>
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
