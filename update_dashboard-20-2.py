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
SUMMARIES_FILE = 'summaries_cache.json'
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

CRITICAL: Only include articles published in the {time_window}. Double-check the publication date. Articles older than 24 hours should NOT be included. The date field must accurately reflect when the article was published.

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
    normalized = headline.lower().strip()
    return hashlib.md5(f"{normalized}{source}".encode()).hexdigest()[:12]

def add_new_articles(data, new_articles):
    """Add new articles to database with robust deduplication and date validation"""
    added_count = 0
    skipped_count = 0
    current_time = datetime.utcnow().isoformat() + "Z"
    
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
            article_date = datetime.strptime(article_date_str, "%B %d, %Y")
            hours_old = (datetime.utcnow() - article_date).total_seconds() / 3600
            
            if hours_old > RETENTION_HOURS:
                skipped_count += 1
                days_old = int(hours_old / 24)
                print(f"⏭️  Skipped (too old - {days_old} days, {int(hours_old)} hours): {article['headline'][:50]}...")
                continue
                
        except (ValueError, AttributeError) as e:
            skipped_count += 1
            print(f"⏭️  Skipped (invalid date '{article_date_str}'): {article['headline'][:50]}...")
            continue
        
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

# ─────────────────────────────────────────────────────────────
# SUMMARIES GENERATION (once daily)
# ─────────────────────────────────────────────────────────────

def load_summaries_cache():
    """Load the existing summaries cache from disk"""
    try:
        with open(SUMMARIES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_summaries_cache(cache):
    """Persist summaries cache to disk"""
    with open(SUMMARIES_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def get_pacific_date_str():
    """Return today's date as a string in Pacific time (YYYY-MM-DD)"""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    month = utc_now.month
    if 3 < month < 11:
        is_dst = True
    elif month == 3:
        is_dst = utc_now.day > 14
    elif month == 11:
        is_dst = utc_now.day <= 7
    else:
        is_dst = False
    pacific_now = utc_now + timedelta(hours=-7 if is_dst else -8)
    return pacific_now.strftime('%Y-%m-%d')

def call_claude_for_summary(prompt_text):
    """Make a single Claude API call (no web search) and return the text response"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt_text}]
    )
    return message.content[0].text.strip()

def generate_summaries(data):
    """
    Generate AI summaries for each category + a Bottom Line summary.
    Only runs once per calendar day (Pacific time). Caches results in
    summaries_cache.json. Returns the summaries dict.
    """
    print("📝 Checking summaries cache...")

    today = get_pacific_date_str()
    cache = load_summaries_cache()

    # Return cached summaries if already generated today
    if cache.get('date') == today and cache.get('summaries'):
        print(f"   ✅ Summaries already generated for {today}, using cache")
        return cache['summaries']

    print(f"   Generating fresh summaries for {today}...")

    # Group articles by category
    section_titles = {
        'economics': 'Economics',
        'industries': 'Industries',
        'business': 'Business',
        'tech': 'Tech',
        'politics': 'Politics',
        'supply-chain': 'Supply Chain & Logistics',
        'local-deals': 'Local Deals & Developments'
    }

    categories = {k: [] for k in section_titles}
    for article in data['articles']:
        cat = article.get('category', 'industries')
        if cat in categories:
            categories[cat].append(article)

    summaries = {}

    # Generate a summary for each category that has articles
    for cat_key, cat_title in section_titles.items():
        articles = categories[cat_key]
        if not articles:
            summaries[cat_key] = None
            print(f"   ⏭️  {cat_title}: no articles, skipping")
            continue

        # Build article context for this category
        article_context = "\n\n".join([
            f"Headline: {a['headline']}\nSource: {a['source']}\nDate: {a['date']}\nSummary: {a['summary']}"
            for a in articles
        ])

        prompt = f"""You are writing a one-sentence editorial summary for a section of a news digest read by Southern California industrial real estate brokers.

Below are the {cat_title} news articles from the past 72 hours:

{article_context}

Write exactly 1 sentence — no more — capturing the single most important development in this category right now. Be specific and factual. Include a key figure or named entity if relevant. Do not speculate or advise."""

        try:
            summary_text = call_claude_for_summary(prompt)
            summaries[cat_key] = summary_text
            print(f"   ✅ {cat_title}: summary generated")
        except Exception as e:
            print(f"   ⚠️  {cat_title}: summary failed ({e})")
            summaries[cat_key] = None

    # Generate the Bottom Line — synthesizes all categories
    all_summaries_context = "\n\n".join([
        f"{section_titles[k]}: {v}"
        for k, v in summaries.items()
        if v is not None
    ])

    if all_summaries_context:
        bottom_line_prompt = f"""You are writing a one-sentence macro summary for a news digest read by Southern California industrial real estate brokers.

Below are today's category summaries:

{all_summaries_context}

Write exactly 1 sentence that captures the single dominant macro force shaping the business environment right now — the kind of big-picture theme a CFO or senior executive would describe when asked "what's going on out there?" Think interest rates, trade policy, consumer demand, capital markets, global supply chain — the macro signal beneath the daily noise. Be direct and specific. No speculation, no advice."""

        try:
            bottom_line = call_claude_for_summary(bottom_line_prompt)
            summaries['bottom_line'] = bottom_line
            print(f"   ✅ Bottom Line generated")
        except Exception as e:
            print(f"   ⚠️  Bottom Line failed ({e})")
            summaries['bottom_line'] = None
    else:
        summaries['bottom_line'] = None

    # Save to cache with today's date
    cache = {'date': today, 'summaries': summaries}
    save_summaries_cache(cache)
    print(f"   💾 Summaries cached for {today}")

    return summaries

# ─────────────────────────────────────────────────────────────
# HTML GENERATION
# ─────────────────────────────────────────────────────────────

def generate_html(data, summaries):
    """Generate magazine-style Front Page and category pages"""
    
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
            return datetime(2000, 1, 1)
    
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
    
    current_date = pacific_now.strftime('%A, %B %d, %Y')
    total_articles = len(data['articles'])
    
    # ── Shared sticky header (used on all pages) ──────────────
    def generate_header(active_page='home'):
        nav_items = []
        for cat_key, cat_title in section_titles.items():
            short_title = cat_title.split(' & ')[0] if ' & ' in cat_title else cat_title.split()[0]
            nav_items.append(
                f'<a href="{cat_key}.html" style="font-family: -apple-system, sans-serif; font-size: 0.7rem; '
                f'font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: #666; text-decoration: none;">'
                f'{short_title}</a>'
            )
        
        nav_html = '\n        '.join(nav_items)
        front_page_color = '#c8102e' if active_page == 'home' else '#666'
        
        return f'''
  <div style="position: fixed; top: 0; left: 0; right: 0; background: #000; color: #fff; z-index: 1000; border-bottom: 3px solid #c8102e; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="text-align: center; padding: 1.5rem 2rem 1rem;">
      <a href="index.html" style="text-decoration: none; color: inherit;">
        <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 2rem; font-weight: 400; letter-spacing: -0.02em; margin-bottom: 0.5rem;">SoCal Industrial Journal</div>
      </a>
      <div style="font-size: 0.7rem; color: #999; letter-spacing: 0.15em; text-transform: uppercase;">{current_date} • Rolling 72-Hour Brief</div>
    </div>
    
    <div style="background: #fff; border-top: 1px solid #333; padding: 0.75rem 2rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
      <a href="index.html" style="font-family: -apple-system, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: {front_page_color}; text-decoration: none;">Front Page</a>
      {nav_html}
    </div>
  </div>'''

    # ── Front Page (homepage) ─────────────────────────────────
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
                empty_categories.append(cat_title)
                continue
            
            # Use AI summary if available, otherwise fall back gracefully
            ai_summary = summaries.get(cat_key) if summaries else None
            if not ai_summary:
                # Fallback: use truncated summary from most recent article
                ai_summary = articles[0]['summary'][:200] + '...' if len(articles[0]['summary']) > 200 else articles[0]['summary']
            
            # Hover shadow derived from category color
            rgb = tuple(int(cat_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            hover_shadow = f'0 4px 12px rgba({rgb[0]},{rgb[1]},{rgb[2]},0.15)'
            
            cards_html += f'''
    <a href="{cat_key}.html" style="background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid {cat_color}; padding: 2rem; cursor: pointer; text-decoration: none; color: inherit; display: block; transition: all 0.2s;" onmouseover="this.style.borderLeftWidth='6px'; this.style.boxShadow='{hover_shadow}'; this.style.transform='translateY(-2px)';" onmouseout="this.style.borderLeftWidth='4px'; this.style.boxShadow='none'; this.style.transform='translateY(0)';">
      <div style="font-family: -apple-system, sans-serif; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: {cat_color}; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
        {cat_icon} {cat_title}
        <span style="background: {cat_color}; color: #fff; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.65rem; font-weight: 600;">{article_count} {'story' if article_count == 1 else 'stories'}</span>
      </div>
      <p style="font-family: Georgia, serif; font-size: 0.95rem; line-height: 1.65; color: #333; margin-bottom: 1.25rem;">{ai_summary}</p>
      <div style="font-family: -apple-system, sans-serif; font-size: 0.8rem; font-weight: 500; color: {cat_color};">View all {cat_title} stories →</div>
    </a>
'''
        
        # Bottom Line banner
        bottom_line_text = summaries.get('bottom_line') if summaries else None
        if bottom_line_text:
            bottom_line_html = f'''
  <div style="background: #000; border-left: 6px solid #c8102e; padding: 2rem 2.5rem; margin-bottom: 2.5rem; border-radius: 2px;">
    <div style="font-family: -apple-system, sans-serif; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase; color: #c8102e; margin-bottom: 0.75rem;">⬛ The Bottom Line</div>
    <p style="font-family: Georgia, serif; font-size: 1.1rem; line-height: 1.7; color: #fff; margin: 0;">{bottom_line_text}</p>
  </div>'''
        else:
            bottom_line_html = ''

        # Empty categories notice
        empty_notice = ''
        if empty_categories:
            empty_list = ', '.join(empty_categories)
            empty_notice = f'''
  <div style="text-align: center; margin: 3rem 0; padding: 1.5rem; background: #f5f5f5; border-radius: 8px;">
    <p style="font-size: 0.9rem; color: #666;">
      {empty_list} {'category has' if len(empty_categories) == 1 else 'categories have'} no stories yet. Check back soon for updates.
    </p>
  </div>'''
        
        # "Updated X ago" timestamp
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
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoCal Industrial Journal | Front Page</title>
    <meta http-equiv="refresh" content="7200">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
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

  <div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-family: Georgia, serif; font-size: 1.5rem; font-weight: 600; color: #000; margin-bottom: 0.5rem;">Front Page</h1>
    <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
      <p style="font-size: 0.95rem; color: #666;">{total_articles} stories across {active_categories} categories</p>
      <span style="background: #e8f5e9; color: #2e7d32; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">Updated {time_ago}</span>
    </div>
  </div>

  {bottom_line_html}

  <div class="category-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 2rem; margin-bottom: 3rem;">
    {cards_html}
  </div>

  {empty_notice}

  <div style="background: #000; color: #666; padding: 2rem; text-align: center; font-family: -apple-system, sans-serif; font-size: 0.75rem; border-top: 3px solid #c8102e; margin-top: 3rem;">
    <div style="margin-bottom: 0.5rem; color: #999;">SoCal Industrial Journal</div>
    <div style="margin-bottom: 0.75rem;">Bloomberg • Wall Street Journal • Green Street • Connect CRE • BisNow • CoStar • GlobeSt</div>
    <div style="font-size: 0.7rem; color: #555;">Rolling 72-hour window • Updates every 2 hours • Summaries refreshed daily</div>
  </div>

</div>
</body>
</html>'''

    # ── Category page ─────────────────────────────────────────
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
        
        return f'''<!DOCTYPE html>
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
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
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
    <a href="index.html" style="font-family: -apple-system, sans-serif; font-size: 0.8rem; color: {cat_color}; text-decoration: none; margin-bottom: 1rem; display: inline-block;">← Back to Front Page</a>
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

    # ── Write all pages ────────────────────────────────────────
    import os
    os.makedirs('docs', exist_ok=True)

    print("📄 Generating Front Page...")
    homepage = generate_homepage()
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(homepage)
    print("   ✓ Front Page created")
    
    print("📄 Generating category pages...")
    for cat_key, cat_title in section_titles.items():
        page_html = generate_category_page(cat_key, cat_title)
        with open(f'docs/{cat_key}.html', 'w', encoding='utf-8') as f:
            f.write(page_html)
        print(f"   ✓ {cat_title} page created ({len(categories[cat_key])} articles)")
    
    print("✅ Generated 8 HTML pages (1 Front Page + 7 category pages)")
    return homepage

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

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

    # Generate (or load cached) AI summaries — once daily
    summaries = generate_summaries(data)
    
    # Generate HTML pages
    print("🎨 Generating HTML...")
    generate_html(data, summaries)
    
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print(f"   Total articles: {len(data['articles'])}")
    print(f"   New this run: {added_count}")
    print(f"   Next update: In 2 hours")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
