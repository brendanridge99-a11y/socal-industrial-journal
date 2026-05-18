#!/usr/bin/env python3
"""
SoCal Industrial Journal - Automated News Aggregator
Searches Bloomberg, WSJ, Green Street, Connect CRE, BisNow, CoStar, GlobeSt,
Supply Chain Dive, Inland Valley Daily Bulletin, San Bernardino Sun, IE Business Daily
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
                "sources": ["Bloomberg", "Wall Street Journal", "Reuters", "Politico", "Green Street", "Connect CRE", "BisNow", "CoStar", "GlobeSt", "The Real Deal", "Commercial Observer", "Propmodo", "Supply Chain Dive", "FreightWaves", "Journal of Commerce", "DC Velocity", "Pacific Maritime Magazine", "Industry Week", "Modern Materials Handling", "Food Logistics", "Los Angeles Times", "CalMatters", "Los Angeles Business Journal", "San Diego Business Journal", "IE Business Daily", "Daily Bulletin", "Los Angeles Daily News", "Press-Telegram", "San Gabriel Valley Tribune", "Whittier Daily News", "The Sun", "The Press-Enterprise", "Redlands Daily Facts", "Pasadena Star-News", "Orange County Register", "Daily Breeze", "San Diego Union-Tribune"],
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

WIRE SERVICES & NATIONAL BUSINESS:
- Bloomberg (including Bloomberg Law at bloomberg.com/law and Bloomberg Intelligence sector research)
- Wall Street Journal (including WSJ Logistics Report at wsj.com/logistics and WSJ Pro Bankruptcy at wsj.com/pro/bankruptcy)
- Reuters (reuters.com, including Reuters California News at reuters.com/world/us/california)
- Politico (politico.com — federal policy, trade, regulatory pipeline)

CRE & INDUSTRIAL TRADE PRESS:
- Green Street
- Connect CRE
- BisNow
- CoStar
- GlobeSt
- The Real Deal (therealdeal.com)
- Commercial Observer (commercialobserver.com)
- Propmodo (propmodo.com)

SUPPLY CHAIN, FREIGHT & LOGISTICS:
- Supply Chain Dive (supplychaindive.com)
- FreightWaves (freightwaves.com)
- Journal of Commerce / JOC (joc.com)
- DC Velocity (dcvelocity.com)
- Pacific Maritime Magazine (pacmar.com)

MANUFACTURING & INDUSTRY VERTICALS:
- Industry Week (industryweek.com)
- Modern Materials Handling (mmh.com)
- Food Logistics (foodlogistics.com)

CALIFORNIA & REGIONAL:
- Los Angeles Times (latimes.com)
- CalMatters (calmatters.org)
- Los Angeles Business Journal (labusinessjournal.com)
- San Diego Business Journal (sdbj.com)
- IE Business Daily (iebusinessdaily.com)
- Daily Bulletin / Inland Valley Daily Bulletin (dailybulletin.com)
- Los Angeles Daily News (dailynews.com)
- Press-Telegram (presstelegram.com)
- San Gabriel Valley Tribune (sgvtribune.com)
- Whittier Daily News (whittierdailynews.com)
- The Sun / San Bernardino Sun (sbsun.com)
- The Press-Enterprise (pe.com)
- Redlands Daily Facts (redlandsdailyfacts.com)
- Pasadena Star-News (pasadenastarnews.com)
- Orange County Register (ocregister.com)
- Daily Breeze (dailybreeze.com)
- San Diego Union-Tribune (sandiegouniontribune.com)

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
# CLUSTERING
# ─────────────────────────────────────────────────────────────

def cluster_articles(articles):
    """
    Group articles about the same real-world event into clusters.

    Strategy (two-phase, conservative):

    Phase 1 — Candidate filtering (cheap, no AI):
      Two articles are candidate pairs only if they share ALL of:
        • Same category
        • Published within 48 hours of each other
        • At least one overlapping named token (company / proper noun ≥ 5 chars)

    Phase 2 — AI confirmation (one batch call):
      Send all candidate pairs to Claude in a single prompt.
      Claude returns only the pairs it is CERTAIN cover the same
      specific event — same deal, same filing, same announcement.
      Conservative instruction: when in doubt, do NOT group.

    Returns a list of "display items": each item is either
      • a single article dict (unchanged), or
      • a cluster dict  {
            'is_cluster': True,
            'articles': [...],          # 2+ article dicts
            'category': str,
            'cluster_headline': str,    # filled later by synthesize_cluster()
            'cluster_summary':  str,    # filled later
            'added_at': str,
            'date': str,
        }
    """
    import re
    from datetime import timezone

    print("🔗 Clustering articles...")

    if len(articles) < 2:
        print("   Not enough articles to cluster")
        return [dict(a) for a in articles]

    # ── helpers ──────────────────────────────────────────────

    def parse_date_dt(article):
        try:
            return datetime.strptime(article.get('date', ''), "%B %d, %Y")
        except Exception:
            return None

    def extract_tokens(text):
        """Return set of capitalised tokens ≥5 chars (rough named-entity proxy)."""
        words = re.findall(r"[A-Z][a-zA-Z]{4,}", text)
        # Drop very common title-case words that aren't entities
        stopwords = {
            'Federal', 'Reserve', 'California', 'Southern', 'Northern',
            'United', 'States', 'American', 'January', 'February', 'March',
            'April', 'August', 'September', 'October', 'November', 'December',
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
            'Sunday', 'Report', 'According', 'announced', 'Industrial',
            'Estate', 'Business', 'Company', 'Group', 'Management',
        }
        return {w for w in words if w not in stopwords}

    def tokens_overlap(a1, a2):
        t1 = extract_tokens(a1['headline'] + ' ' + a1.get('summary', ''))
        t2 = extract_tokens(a2['headline'] + ' ' + a2.get('summary', ''))
        return bool(t1 & t2)

    def within_48h(a1, a2):
        d1, d2 = parse_date_dt(a1), parse_date_dt(a2)
        if d1 is None or d2 is None:
            return False
        return abs((d1 - d2).total_seconds()) <= 48 * 3600

    # ── Phase 1: candidate pairs ──────────────────────────────
    candidate_pairs = []
    arts = list(articles)
    for i in range(len(arts)):
        for j in range(i + 1, len(arts)):
            a1, a2 = arts[i], arts[j]
            if a1.get('category') != a2.get('category'):
                continue
            if not within_48h(a1, a2):
                continue
            if not tokens_overlap(a1, a2):
                continue
            candidate_pairs.append((i, j))

    print(f"   Phase 1: {len(candidate_pairs)} candidate pairs from {len(arts)} articles")

    if not candidate_pairs:
        print("   No candidates — all articles remain standalone")
        return [dict(a) for a in arts]

    # ── Phase 2: AI confirmation ──────────────────────────────
    # Build a single prompt listing all candidate pairs
    pair_lines = []
    for idx, (i, j) in enumerate(candidate_pairs):
        a1, a2 = arts[i], arts[j]
        pair_lines.append(
            f"PAIR {idx+1}:\n"
            f"  A: [{a1['source']}] {a1['headline']}\n"
            f"     {a1.get('summary','')[:200]}\n"
            f"  B: [{a2['source']}] {a2['headline']}\n"
            f"     {a2.get('summary','')[:200]}"
        )

    pairs_text = "\n\n".join(pair_lines)

    confirmation_prompt = f"""You are a strict editorial clustering engine for a news aggregation system.

Below are candidate pairs of news articles that may or may not cover the same real-world event.

YOUR TASK: For each pair, decide if articles A and B are reporting on the EXACT SAME specific event.

STRICT RULES — a pair qualifies ONLY if ALL of the following are true:
1. Same specific company, property, or named entity as the primary subject
2. Same specific event (same deal, same announcement, same filing, same decision)
3. Same location or jurisdiction (city/region must match — Ontario CA ≠ Ontario Canada)
4. Published within 48 hours of each other

DO NOT group if:
- They involve the same company but different events (e.g., Amazon lease vs. Amazon earnings)
- They cover the same broad topic but different specific incidents (e.g., two different port delays)
- One is a follow-up or reaction piece rather than the same announcement
- You are uncertain — when in doubt, do NOT group

Return ONLY a JSON array of pair numbers that pass ALL rules. Example: [1, 3, 5]
If no pairs qualify, return: []
Do not return any explanation or other text.

CANDIDATE PAIRS:
{pairs_text}
"""

    confirmed_indices = set()
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": confirmation_prompt}]
        )
        response_text = message.content[0].text.strip()
        # Parse the returned array
        json_start = response_text.find('[')
        json_end   = response_text.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            confirmed_pair_numbers = json.loads(response_text[json_start:json_end])
            confirmed_indices = {n - 1 for n in confirmed_pair_numbers}  # 0-indexed
        print(f"   Phase 2: AI confirmed {len(confirmed_indices)} pairs for clustering")
    except Exception as e:
        print(f"   ⚠️  Clustering AI call failed ({e}) — all articles remain standalone")
        return [dict(a) for a in arts]

    if not confirmed_indices:
        print("   No pairs confirmed — all articles remain standalone")
        return [dict(a) for a in arts]

    # ── Build clusters from confirmed pairs (union-find) ──────
    parent = list(range(len(arts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for idx in confirmed_indices:
        i, j = candidate_pairs[idx]
        union(i, j)

    # Group by root
    from collections import defaultdict
    groups = defaultdict(list)
    for i in range(len(arts)):
        groups[find(i)].append(i)

    display_items = []
    clustered_ids = set()

    for root, members in groups.items():
        if len(members) == 1:
            continue  # standalone — handled below
        # Multi-member cluster
        cluster_arts = [arts[i] for i in members]
        clustered_ids.update(members)

        # Use the most recent date in the cluster
        dates = [parse_date_dt(a) for a in cluster_arts if parse_date_dt(a)]
        best_date = max(dates) if dates else datetime.utcnow()

        display_items.append({
            'is_cluster':       True,
            'articles':         cluster_arts,
            'category':         cluster_arts[0]['category'],
            'cluster_headline': '',   # filled by synthesize_cluster()
            'cluster_summary':  '',   # filled by synthesize_cluster()
            'date':             best_date.strftime("%B %d, %Y"),
            'added_at':         cluster_arts[0].get('added_at', ''),
            'source_count':     len(cluster_arts),
        })
        sources = ', '.join(a['source'] for a in cluster_arts)
        print(f"   ✅ Cluster ({len(cluster_arts)} sources): {cluster_arts[0]['headline'][:55]}... [{sources}]")

    # Add all standalone articles
    for i in range(len(arts)):
        if i not in clustered_ids:
            display_items.append(dict(arts[i]))

    print(f"   Result: {len([d for d in display_items if d.get('is_cluster')])} clusters + "
          f"{len([d for d in display_items if not d.get('is_cluster')])} standalone articles")

    return display_items


def synthesize_cluster(cluster, summaries_cache):
    """
    Generate a synthesized headline + summary for a cluster of articles.
    Uses a cache key so the same cluster isn't re-synthesized every 2 hours.
    Cache key = sorted tuple of article IDs in the cluster.
    """
    # Build a stable cache key from the article IDs
    ids = sorted(a.get('id', a['headline'][:20]) for a in cluster['articles'])
    cache_key = 'cluster_' + '_'.join(ids)

    if cache_key in summaries_cache:
        cached = summaries_cache[cache_key]
        cluster['cluster_headline'] = cached['headline']
        cluster['cluster_summary']  = cached['summary']
        return cluster

    # Build context for the AI
    articles_text = "\n\n".join([
        f"Source: {a['source']}\nHeadline: {a['headline']}\nSummary: {a['summary']}"
        for a in cluster['articles']
    ])

    prompt = f"""Below are {len(cluster['articles'])} news articles from different outlets covering the same event.

{articles_text}

Your task:
1. Write a SHORT, specific headline (max 12 words) that captures the core event. Be concrete — include the company name, location, and action (e.g. "Prologis Leases 800,000 SF Facility to Amazon in Ontario").
2. Write a 3-4 sentence factual synthesis that pulls the best specific details from ALL sources — include square footage, dollar figures, company names, broker names, locations, and any other concrete facts reported across the articles. Do NOT speculate or add analysis. Wire-service style only.

Return ONLY valid JSON in this exact format with no other text:
{{"headline": "...", "summary": "..."}}"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        json_start = response_text.find('{')
        json_end   = response_text.rfind('}') + 1
        result = json.loads(response_text[json_start:json_end])

        cluster['cluster_headline'] = result.get('headline', cluster['articles'][0]['headline'])
        cluster['cluster_summary']  = result.get('summary',  cluster['articles'][0]['summary'])

        # Cache it
        summaries_cache[cache_key] = {
            'headline': cluster['cluster_headline'],
            'summary':  cluster['cluster_summary'],
        }
        print(f"   ✅ Synthesized: {cluster['cluster_headline'][:60]}...")

    except Exception as e:
        # Fallback: use highest-scoring article's content
        print(f"   ⚠️  Synthesis failed ({e}) — using lead article")
        cluster['cluster_headline'] = cluster['articles'][0]['headline']
        cluster['cluster_summary']  = cluster['articles'][0]['summary']

    return cluster


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
        'economics':    'Economics',
        'supply-chain': 'Supply Chain & Logistics',
        'industries':   'Industrial',
        'politics':     'Politics',
        'business':     'Business',
        'tech':         'Tech',
        'local-deals':  'Local Deals & Developments',
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

        if cat_key == 'local-deals':
            prompt = f"""Below are Southern California real estate and business news items from the past 72 hours:

{article_context}

Write exactly 1 sentence — no more than 50 words — highlighting the most notable deal, transaction, or development across these stories. Be specific — include the property, company, location, or dollar figure that makes it newsworthy. Do not speculate or advise."""
        else:
            prompt = f"""Below are {cat_title} news articles from the past 72 hours:

{article_context}

Write exactly 1 sentence — no more than 50 words — summarizing the broad state of play in {cat_title} right now. Stay at the macro level. Do not reference specific deals, companies, or properties unless they represent the defining story of the period. Do not speculate or advise."""

        try:
            summary_text = call_claude_for_summary(prompt)
            summaries[cat_key] = summary_text
            print(f"   ✅ {cat_title}: summary generated")
        except Exception as e:
            print(f"   ⚠️  {cat_title}: summary failed ({e})")
            summaries[cat_key] = None

        # Also generate a longer 75-word summary for the category page header
        if cat_key == 'local-deals':
            long_prompt = f"""Below are Southern California real estate and business news items from the past 72 hours:

{article_context}

Write a concise editorial summary — no more than 75 words — of the most significant deals, transactions, and developments across these stories. Be specific with names, locations, and figures. Factual and direct. No speculation or advice."""
        else:
            long_prompt = f"""Below are {cat_title} news articles from the past 72 hours:

{article_context}

Write a concise editorial summary — no more than 75 words — of the key themes and developments in {cat_title} over the past 72 hours. Stay macro. Identify the dominant trend and any notable shifts. Factual and direct. No speculation or advice."""

        try:
            long_summary_text = call_claude_for_summary(long_prompt)
            summaries[f"{cat_key}_long"] = long_summary_text
            print(f"   ✅ {cat_title}: long summary generated")
        except Exception as e:
            print(f"   ⚠️  {cat_title}: long summary failed ({e})")
            summaries[f"{cat_key}_long"] = None

    # Generate the Bottom Line — synthesizes all categories
    all_summaries_context = "\n\n".join([
        f"{section_titles[k]}: {v}"
        for k, v in summaries.items()
        if v is not None and k in section_titles
    ])

    if all_summaries_context:
        bottom_line_prompt = f"""You are writing a one-sentence macro summary for a news digest read by Southern California industrial real estate brokers.

Below are today's category summaries:

{all_summaries_context}

Write exactly 1 sentence — no more than 50 words — that captures the single dominant macro force shaping the business environment right now — the kind of big-picture theme a CFO or senior executive would describe when asked "what's going on out there?" Think interest rates, trade policy, consumer demand, capital markets, global supply chain — the macro signal beneath the daily noise. Be direct and specific. No speculation, no advice."""

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

def generate_html(data, summaries, display_items=None):
    """Generate warm premium magazine Front Page and category pages"""

    # Fall back to flat article list if no display_items provided
    if display_items is None:
        display_items = [dict(a) for a in data['articles']]

    # ── Design tokens ─────────────────────────────────────────
    # Palette: cream base, deep ink, terracotta accent, warm category tones
    CREAM       = '#FAF7F2'
    PARCHMENT   = '#F0EBE1'
    INK         = '#1C1917'
    INK_LIGHT   = '#44403C'
    RULE        = '#D6CFC4'
    ACCENT      = '#B5451B'          # terracotta — replaces JLL red
    ACCENT_WARM = '#C9622F'          # hover/lighter
    MUTED       = '#78716C'

    # Category palette — warm, distinct, non-neon
    CAT_COLORS = {
        'economics':    '#7C5C3E',   # warm brown
        'industries':   '#3D6B5E',   # forest green
        'business':     '#4A5F82',   # slate blue
        'tech':         '#6B4F7A',   # muted plum
        'politics':     '#8B4A3A',   # brick
        'supply-chain': '#4E6B5E',   # teal green
        'local-deals':  '#7A6040',   # saddle
    }

    CAT_ICONS = {
        'economics': '◈', 'industries': '◉', 'business': '◆',
        'tech': '◎', 'politics': '◐', 'supply-chain': '◍', 'local-deals': '◑'
    }

    # Shared font import string
    FONTS = "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Serif+Display:ital@0;1&family=Jost:wght@300;400;500;600&display=swap"

    # Shared <style> block — used on all pages
    SHARED_CSS = f'''
        :root {{
            --cream: {CREAM};
            --parchment: {PARCHMENT};
            --ink: {INK};
            --ink-light: {INK_LIGHT};
            --rule: {RULE};
            --accent: {ACCENT};
            --accent-warm: {ACCENT_WARM};
            --muted: {MUTED};
        }}
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{
            font-family: 'Jost', sans-serif;
            background: var(--cream);
            color: var(--ink);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}

        /* ── Header ── */
        .site-header {{
            position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
            background: var(--ink);
            border-bottom: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 2px 20px rgba(28,25,23,0.25);
        }}
        .header-inner {{
            text-align: center;
            padding: 1.25rem 2rem 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.07);
        }}
        .masthead {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 2.4rem;
            font-weight: 400;
            letter-spacing: 0.06em;
            color: #fff;
            text-decoration: none;
            display: block;
            margin-bottom: 0.3rem;
        }}
        .masthead-sub {{
            font-family: 'Jost', sans-serif;
            font-size: 0.7rem;
            font-weight: 400;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.45);
        }}
        .site-nav {{
            display: flex;
            justify-content: center;
            gap: 0;
            background: var(--ink);
            padding: 0 2rem;
            overflow-x: auto;
        }}
        .site-nav a {{
            font-family: 'Jost', sans-serif;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.45);
            text-decoration: none;
            padding: 0.7rem 1rem;
            border-bottom: 2px solid transparent;
            transition: color 0.2s, border-color 0.2s;
            white-space: nowrap;
        }}
        .site-nav a:hover {{ color: rgba(255,255,255,0.85); }}
        .site-nav a.active {{
            color: #fff;
            border-bottom-color: var(--accent);
        }}

        /* ── Bottom Line banner ── */
        .bottom-line {{
            background: var(--ink);
            border-left: 3px solid var(--accent);
            padding: 1.75rem 2.25rem;
            margin-bottom: 2.5rem;
        }}
        .bottom-line-label {{
            font-family: 'Jost', sans-serif;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.6rem;
        }}
        .bottom-line-text {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 1.45rem;
            font-weight: 400;
            font-style: italic;
            line-height: 1.6;
            color: rgba(255,255,255,0.92);
        }}

        /* ── Front Page category cards ── */
        .fp-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        .fp-card {{
            background: #fff;
            border: 1px solid var(--rule);
            border-top: 3px solid var(--cat-color, var(--accent));
            padding: 1.5rem;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }}
        .fp-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(28,25,23,0.1);
        }}
        .fp-card-label {{
            font-family: 'Jost', sans-serif;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--cat-color, var(--accent));
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        .fp-card-count {{
            background: var(--cat-color, var(--accent));
            color: #fff;
            font-size: 0.62rem;
            padding: 0.1rem 0.4rem;
            border-radius: 2px;
            font-weight: 600;
        }}
        .fp-card-summary {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 1.2rem;
            font-weight: 400;
            line-height: 1.6;
            color: var(--ink-light);
            flex: 1;
            margin-bottom: 1.25rem;
        }}
        .fp-card-cta {{
            font-family: 'Jost', sans-serif;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--cat-color, var(--accent));
        }}

        /* ── Article grid (category pages) ── */
        .article-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        .article-card {{
            background: #fff;
            border: 1px solid var(--rule);
            border-top: 3px solid var(--cat-color, var(--accent));
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
        }}
        .article-meta {{
            font-family: 'Jost', sans-serif;
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--cat-color, var(--accent));
            margin-bottom: 0.65rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            flex-wrap: wrap;
        }}
        .article-meta .date {{
            color: var(--muted);
            font-weight: 400;
        }}
        .article-headline {{
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 1.2rem;
            font-weight: 400;
            line-height: 1.35;
            color: var(--ink);
            margin-bottom: 0.85rem;
        }}
        .article-summary {{
            font-family: 'Jost', sans-serif;
            font-size: 0.9rem;
            font-weight: 400;
            line-height: 1.75;
            color: var(--ink-light);
            flex: 1;
            margin-bottom: 1.1rem;
        }}
        .article-read {{
            font-family: 'Jost', sans-serif;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--ink);
            text-decoration: none;
            border-bottom: 1px solid var(--rule);
            padding-bottom: 1px;
            display: inline-block;
            transition: border-color 0.15s;
        }}
        .article-read:hover {{ border-color: var(--ink); }}

        /* ── Page header (category pages) ── */
        .page-header {{
            border-bottom: 1px solid var(--rule);
            padding-bottom: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        .back-link {{
            font-family: 'Jost', sans-serif;
            font-size: 0.65rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--muted);
            text-decoration: none;
            display: inline-block;
            margin-bottom: 1rem;
        }}
        .back-link:hover {{ color: var(--accent); }}
        .page-title {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 2.75rem;
            font-weight: 300;
            letter-spacing: 0.02em;
            color: var(--ink);
            margin-bottom: 0.35rem;
        }}
        .page-count {{
            font-family: 'Jost', sans-serif;
            font-size: 0.7rem;
            color: var(--muted);
            letter-spacing: 0.05em;
        }}

        /* ── Footer ── */
        .site-footer {{
            background: var(--ink);
            color: rgba(255,255,255,0.35);
            padding: 2rem;
            text-align: center;
            font-family: 'Jost', sans-serif;
            font-size: 0.65rem;
            letter-spacing: 0.08em;
            margin-top: 4rem;
            border-top: 3px solid var(--accent);
        }}
        .site-footer .footer-name {{
            color: rgba(255,255,255,0.6);
            font-weight: 500;
            margin-bottom: 0.5rem;
            font-size: 0.7rem;
        }}
        .site-footer .footer-sources {{ margin-bottom: 0.5rem; }}

        /* ── Divider ── */
        .ruled {{ border: none; border-top: 1px solid var(--rule); margin: 2rem 0; }}

        /* ── Status badge ── */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: #EEFAF2;
            color: #2D6A4F;
            font-family: 'Jost', sans-serif;
            font-size: 0.62rem;
            font-weight: 500;
            letter-spacing: 0.06em;
            padding: 0.25rem 0.65rem;
            border-radius: 2px;
        }}
        .status-dot {{
            width: 5px; height: 5px;
            background: #2D6A4F;
            border-radius: 50%;
            display: inline-block;
        }}

        /* ── Paywall badge ── */
        .paywall-badge {{
            font-size: 0.55rem;
            color: var(--muted);
            border: 1px solid var(--rule);
            padding: 0.1rem 0.35rem;
            border-radius: 2px;
        }}

        /* ── Category page summary banner ── */
        .cat-summary-banner {{
            background: var(--parchment);
            border-left: 3px solid var(--cat-color, var(--accent));
            padding: 1.5rem 2rem;
            margin-bottom: 2.5rem;
        }}
        .cat-summary-text {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 1.2rem;
            font-weight: 400;
            line-height: 1.65;
            color: var(--ink);
        }}

        /* ── Top Articles section ── */
        .section-label {{
            font-family: 'Jost', sans-serif;
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 1rem;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid var(--rule);
        }}
        .top-article-card {{
            background: #fff;
            border: 1px solid var(--rule);
            border-top: 3px solid var(--cat-color, var(--accent));
            padding: 1.75rem;
            display: flex;
            flex-direction: column;
            position: relative;
        }}
        .top-badge {{
            font-family: 'Jost', sans-serif;
            font-size: 0.58rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--cat-color, var(--accent));
            background: var(--parchment);
            padding: 0.2rem 0.5rem;
            border-radius: 2px;
            display: inline-block;
            margin-bottom: 0.75rem;
            align-self: flex-start;
        }}
        .top-article-headline {{
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 1.3rem;
            font-weight: 400;
            line-height: 1.3;
            color: var(--ink);
            margin-bottom: 0.85rem;
        }}

        /* ── All stories divider ── */
        .all-stories-divider {{
            margin: 2.5rem 0 1.5rem;
        }}

        /* ── Cluster card ── */
        .cluster-sources {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.4rem;
            margin-top: 1rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--rule);
        }}
        .cluster-sources-label {{
            font-family: 'Jost', sans-serif;
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--muted);
            margin-right: 0.25rem;
        }}
        .cluster-source-link {{
            font-family: 'Jost', sans-serif;
            font-size: 0.68rem;
            font-weight: 500;
            color: var(--cat-color, var(--accent));
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.15s;
            padding-bottom: 1px;
        }}
        .cluster-source-link:hover {{
            border-bottom-color: var(--cat-color, var(--accent));
        }}
        .cluster-source-sep {{
            color: var(--rule);
            font-size: 0.65rem;
        }}
        .cluster-badge {{
            font-family: 'Jost', sans-serif;
            font-size: 0.58rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #fff;
            background: var(--cat-color, var(--accent));
            padding: 0.15rem 0.5rem;
            border-radius: 2px;
            display: inline-block;
            margin-left: auto;
        }}
            grid-column: 1 / -1;
            text-align: center;
            padding: 3rem;
            background: var(--parchment);
            border: 1px solid var(--rule);
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 1.1rem;
            color: var(--muted);
        }}

        /* ── Responsive ── */
        @media (max-width: 900px) {{
            .fp-grid, .article-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @media (max-width: 600px) {{
            .fp-grid, .article-grid {{ grid-template-columns: 1fr; }}
            .masthead {{ font-size: 1.5rem; }}
            body {{ padding-top: 170px !important; }}
        }}
'''

    # ── Group & sort display items by category ────────────────
    categories = {k: [] for k in ['economics','supply-chain','industries','politics','business','tech','local-deals']}
    for item in display_items:
        cat = item.get('category', 'industries')
        if cat in categories:
            categories[cat].append(item)

    def parse_date(article):
        try:
            return datetime.strptime(article.get('date',''), "%B %d, %Y")
        except:
            return datetime(2000, 1, 1)

    def importance_score(item):
        """Score articles/clusters by newsworthiness for Top Articles selection"""
        # For clusters, score the best individual article then add multi-source bonus
        if item.get('is_cluster'):
            best = max(item['articles'], key=lambda a: _base_score(a))
            bonus = (item['source_count'] - 1) * 5  # +5 per additional source
            return _base_score(best) + bonus
        return _base_score(item)

    def _base_score(article):
        score = 0
        headline = article.get('headline', '').lower()
        source   = article.get('source', '').lower()

        if source in ['wall street journal', 'bloomberg', 'wsj', 'reuters']:
            score += 50
        elif source in ['green street', 'costar']:
            score += 30
        elif source in ['los angeles times', 'los angeles business journal']:
            score += 30
        elif source in ['supply chain dive', 'freightwaves', 'journal of commerce',
                        'the real deal', 'commercial observer', 'politico']:
            score += 25
        elif source in ['calmatters', 'industry week', 'modern materials handling',
                        'food logistics', 'dc velocity', 'pacific maritime magazine',
                        'propmodo']:
            score += 20
        elif source in ['daily bulletin', 'los angeles daily news', 'press-telegram',
                        'san gabriel valley tribune', 'whittier daily news', 'the sun',
                        'the press-enterprise', 'redlands daily facts', 'pasadena star-news',
                        'orange county register', 'daily breeze', 'san diego union-tribune',
                        'san diego business journal', 'ie business daily']:
            score += 25   # Regional SoCal papers always locally relevant
        else:
            score += 10

        for kw in ['breaking','exclusive','major','unprecedented','historic','largest','biggest','first-ever']:
            if kw in headline: score += 30; break
        for kw in ['bankruptcy','bankrupt','collapse','acquisition','acquires','merger','layoff','lays off','closes','shuts down','billion','million sf','record']:
            if kw in headline: score += 20; break
        for kw in ['fed ','federal reserve','interest rate','recession','inflation','gdp','tariff','regulation']:
            if kw in headline: score += 15; break
        for kw in ['inland empire','riverside','san bernardino','ontario','fontana','moreno valley','los angeles','orange county','san diego']:
            if kw in headline: score += 25; break

        try:
            days_old = (datetime.now() - parse_date(article)).days
            score += 15 if days_old == 0 else (10 if days_old == 1 else (5 if days_old == 2 else 0))
        except:
            pass
        return score

    for cat in categories:
        categories[cat].sort(key=parse_date, reverse=True)

    section_titles = {
        'economics':    'Economics',
        'supply-chain': 'Supply Chain & Logistics',
        'industries':   'Industrial',
        'politics':     'Politics',
        'business':     'Business',
        'tech':         'Tech',
        'local-deals':  'Local Deals & Developments',
    }

    # Short names shown in nav — supply-chain shows as "Logistics"
    nav_short_titles = {
        'economics':    'Economics',
        'supply-chain': 'Logistics',
        'industries':   'Industrial',
        'politics':     'Politics',
        'business':     'Business',
        'tech':         'Tech',
        'local-deals':  'Local',
    }

    # ── Pacific time ──────────────────────────────────────────
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    month = utc_now.month
    if 3 < month < 11:    is_dst = True
    elif month == 3:      is_dst = utc_now.day > 14
    elif month == 11:     is_dst = utc_now.day <= 7
    else:                 is_dst = False
    pacific_now  = utc_now + timedelta(hours=-7 if is_dst else -8)
    current_date = pacific_now.strftime('%A, %B %d, %Y')
    total_articles = len(data['articles'])

    # ── "Updated X ago" ───────────────────────────────────────
    last_update_time = data.get('last_updated', datetime.utcnow().isoformat() + "Z")
    last_update_dt   = datetime.fromisoformat(last_update_time.replace('Z', '+00:00'))
    minutes_ago = int((datetime.now(timezone.utc) - last_update_dt).total_seconds() / 60)
    if minutes_ago < 60:
        time_ago = f"{minutes_ago}m ago"
    else:
        time_ago = f"{minutes_ago // 60}h ago"

    # ── Shared header ─────────────────────────────────────────
    def generate_header(active_page='home'):
        # Build nav with inline active styling
        nav_items = []
        for cat_key, cat_title in section_titles.items():
            short = nav_short_titles[cat_key]
            is_active = active_page == cat_key
            color = 'color:#fff; border-bottom-color:var(--accent);' if is_active else ''
            nav_items.append(
                f'<a href="{cat_key}.html" style="{color}" class="site-nav-link">{short}</a>'
            )

        fp_style = 'color:#fff; border-bottom-color:var(--accent);' if active_page == 'home' else ''

        return f'''<header class="site-header">
  <div class="header-inner">
    <a href="index.html" class="masthead">SoCal Industrial Journal</a>
    <div class="masthead-sub">{current_date} &nbsp;·&nbsp; Rolling 72-Hour Brief</div>
  </div>
  <nav class="site-nav">
    <a href="index.html" class="site-nav-link" style="{fp_style}">Front Page</a>
    {''.join(nav_items)}
  </nav>
</header>'''

    # ── Front Page ────────────────────────────────────────────
    def generate_homepage():
        # Bottom Line
        bottom_line_text = (summaries or {}).get('bottom_line')
        if bottom_line_text:
            bottom_line_html = f'''<div class="bottom-line">
  <div class="bottom-line-label">The Bottom Line</div>
  <p class="bottom-line-text">{bottom_line_text}</p>
</div>'''
        else:
            bottom_line_html = ''

        # Category cards
        cards_html = ''
        empty_cats = []
        active_count = 0

        for cat_key, cat_title in section_titles.items():
            arts    = categories[cat_key]
            count   = len(arts)
            color   = CAT_COLORS[cat_key]
            icon    = CAT_ICONS[cat_key]

            if count == 0:
                empty_cats.append(cat_title)
                continue

            active_count += 1
            ai_summary = (summaries or {}).get(cat_key)
            if not ai_summary:
                ai_summary = arts[0]['summary'][:220] + '…'

            label = cat_title
            cards_html += f'''<a href="{cat_key}.html" class="fp-card" style="--cat-color:{color};">
  <div class="fp-card-label">
    <span>{icon} {label}</span>
    <span class="fp-card-count">{count}</span>
  </div>
  <p class="fp-card-summary">{ai_summary}</p>
  <div class="fp-card-cta">View all stories →</div>
</a>
'''

        empty_notice = ''
        if empty_cats:
            joined = ', '.join(empty_cats)
            empty_notice = f'<p style="font-family:\'Jost\',sans-serif;font-size:0.8rem;color:var(--muted);text-align:center;margin:2rem 0;">{joined} {"has" if len(empty_cats)==1 else "have"} no stories yet — check back soon.</p>'

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SoCal Industrial Journal | Front Page</title>
  <meta http-equiv="refresh" content="7200">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONTS}" rel="stylesheet">
  <style>{SHARED_CSS}
    body {{ padding-top: 120px; }}
    @media (max-width: 600px) {{ body {{ padding-top: 140px; }} }}
  </style>
</head>
<body>
{generate_header('home')}

<main style="max-width: 1200px; margin: 0 auto; padding: 2.5rem 2rem;">

  <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:1rem; margin-bottom:2rem; padding-bottom:1rem; border-bottom:1px solid var(--rule);">
    <h1 style="font-family:'Cormorant Garamond',Georgia,serif; font-size:1.35rem; font-weight:300; letter-spacing:0.04em; color:var(--ink);">Today's Briefing</h1>
    <div style="display:flex; align-items:center; gap:1rem; flex-wrap:wrap;">
      <span style="font-family:'Jost',sans-serif; font-size:0.7rem; color:var(--muted);">{total_articles} stories · {active_count} sections</span>
      <span class="status-badge"><span class="status-dot"></span>Updated {time_ago}</span>
    </div>
  </div>

  {bottom_line_html}

  <div class="fp-grid">
    {cards_html}
  </div>

  {empty_notice}

</main>

<footer class="site-footer">
  <div class="footer-name">SoCal Industrial Journal</div>
  <div class="footer-sources">Sourced from 37 national, trade, and regional publications &nbsp;·&nbsp; <a href="sources.html" style="color:rgba(255,255,255,0.5);text-decoration:none;border-bottom:1px solid rgba(255,255,255,0.25);">View source directory →</a></div>
  <div>Rolling 72-hour window &nbsp;·&nbsp; Updates every 2 hours &nbsp;·&nbsp; Summaries refreshed daily</div>
</footer>

</body>
</html>'''

    # ── Category page ─────────────────────────────────────────
    def generate_category_page(cat_key, cat_title):
        arts  = categories[cat_key]
        color = CAT_COLORS[cat_key]
        icon  = CAT_ICONS[cat_key]
        count = len(arts)

        if count == 0:
            body_html = '<div class="empty-state">No stories in this category yet — check back soon.</div>'
        else:
            # ── Long summary banner ────────────────────────────
            long_summary = (summaries or {}).get(f"{cat_key}_long")
            if long_summary:
                summary_banner = f'''<div class="cat-summary-banner" style="--cat-color:{color};">
  <p class="cat-summary-text">{long_summary}</p>
</div>'''
            else:
                summary_banner = ''

            # ── Top 3 articles by importance score ────────────
            scored = sorted(arts, key=importance_score, reverse=True)
            top_arts  = scored[:3]
            rest_arts = scored[3:]

            def make_cluster_sources_html(cluster_item):
                """Build the linked source attribution footer for a cluster card."""
                links = []
                for a in cluster_item['articles']:
                    is_pw = a.get('source_type', 'free') == 'paywalled'
                    lock  = ' 🔒' if is_pw else ''
                    links.append(
                        f'<a href="{a["url"]}" target="_blank" class="cluster-source-link">'
                        f'{a["source"]}{lock}</a>'
                    )
                sep = '<span class="cluster-source-sep">·</span>'
                count = cluster_item['source_count']
                return (
                    f'<div class="cluster-sources">'
                    f'<span class="cluster-sources-label">Coverage</span>'
                    f'{sep.join(links)}'
                    f'<span class="cluster-badge">{count} sources</span>'
                    f'</div>'
                )

            def make_card(item, is_top=False):
                is_cluster = item.get('is_cluster', False)

                if is_cluster:
                    headline   = item['cluster_headline'] or item['articles'][0]['headline']
                    summary    = item['cluster_summary']  or item['articles'][0]['summary']
                    date_str   = item['date']
                    sources_html = make_cluster_sources_html(item)
                    top_badge  = '<span class="top-badge">Top Story</span>' if is_top else ''
                    h_class    = 'top-article-headline' if is_top else 'article-headline'
                    card_class = 'top-article-card' if is_top else 'article-card'
                    return f'''<div class="{card_class}" style="--cat-color:{color};">
  {top_badge}
  <div class="article-meta">
    <span class="date">{date_str}</span>
  </div>
  <h3 class="{h_class}">{headline}</h3>
  <p class="article-summary">{summary}</p>
  {sources_html}
</div>'''

                # ── Solo article ──────────────────────────────
                is_paywalled = item.get('source_type','free') == 'paywalled'
                paywall = '<span class="paywall-badge">🔒 Subscriber</span>' if is_paywalled else ''
                article_url_encoded = item["url"].replace("&", "%26")
                subject = f'Article%20Request%3A%20{item["headline"][:60].replace(" ", "%20")}'
                body_enc = f'Hi%20Brendan%2C%0A%0AI%20would%20like%20more%20information%20on%20the%20following%20article%3A%0A%0A{item["headline"]}%0A{article_url_encoded}%0A%0AThanks'
                access = f'&nbsp;&nbsp;<a href="mailto:{YOUR_EMAIL}?subject={subject}&body={body_enc}" style="font-family:\'Jost\',sans-serif;font-size:0.72rem;font-weight:500;color:var(--accent);text-decoration:none;letter-spacing:0.05em;">Request more info →</a>' if is_paywalled else ''

                if is_top:
                    return f'''<div class="top-article-card" style="--cat-color:{color};">
  <span class="top-badge">Top Story</span>
  <div class="article-meta">
    <span>{item["source"]}</span>
    <span class="date">· {item["date"]}</span>
    {paywall}
  </div>
  <h3 class="top-article-headline">{item["headline"]}</h3>
  <p class="article-summary">{item["summary"]}</p>
  <div>
    <a href="{item["url"]}" target="_blank" class="article-read">Read full story</a>{access}
  </div>
</div>'''
                else:
                    return f'''<div class="article-card" style="--cat-color:{color};">
  <div class="article-meta">
    <span>{item["source"]}</span>
    <span class="date">· {item["date"]}</span>
    {paywall}
  </div>
  <h3 class="article-headline">{item["headline"]}</h3>
  <p class="article-summary">{item["summary"]}</p>
  <div>
    <a href="{item["url"]}" target="_blank" class="article-read">Read full story</a>{access}
  </div>
</div>'''

            top_cards_html  = '\n'.join(make_card(a, is_top=True) for a in top_arts)
            rest_cards_html = '\n'.join(make_card(a, is_top=False) for a in rest_arts)

            rest_section = ''
            if rest_arts:
                rest_section = f'''<div class="all-stories-divider">
  <div class="section-label">All Stories</div>
</div>
<div class="article-grid">
  {rest_cards_html}
</div>'''

            body_html = f'''{summary_banner}
<div class="section-label">Top Stories</div>
<div class="article-grid">
  {top_cards_html}
</div>
{rest_section}'''

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{cat_title} | SoCal Industrial Journal</title>
  <meta http-equiv="refresh" content="7200">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONTS}" rel="stylesheet">
  <style>{SHARED_CSS}
    body {{ padding-top: 120px; }}
    @media (max-width: 600px) {{ body {{ padding-top: 140px; }} }}
  </style>
</head>
<body>
{generate_header(cat_key)}

<main style="max-width: 1280px; margin: 0 auto; padding: 2.5rem 2rem;">

  <div class="page-header">
    <a href="index.html" class="back-link">← Front Page</a>
    <h1 class="page-title">{icon} {cat_title}</h1>
    <p class="page-count">{count} {'story' if count == 1 else 'stories'} · {sum(1 for i in arts if i.get('is_cluster')) or 'no'} clusters</p>
  </div>

  {body_html}

</main>

<footer class="site-footer">
  <div class="footer-name">SoCal Industrial Journal</div>
  <div class="footer-sources">Sourced from 37 national, trade, and regional publications &nbsp;·&nbsp; <a href="sources.html" style="color:rgba(255,255,255,0.5);text-decoration:none;border-bottom:1px solid rgba(255,255,255,0.25);">View source directory →</a></div>
  <div>Rolling 72-hour window &nbsp;·&nbsp; Updates every 2 hours</div>
</footer>

</body>
</html>'''

    # ── Source directory page ──────────────────────────────────
    def generate_sources_page():
        source_groups = [
            {
                'title': 'Wire Services & National Business',
                'description': 'Tier-1 financial and general business news with global coverage.',
                'sources': [
                    ('Bloomberg', 'bloomberg.com', 'Global financial news, markets, economics, and Bloomberg Law legal coverage.'),
                    ('Wall Street Journal', 'wsj.com', 'National business news, WSJ Logistics Report, and WSJ Pro Bankruptcy.'),
                    ('Reuters', 'reuters.com', 'International wire service including Reuters California regional news.'),
                    ('Politico', 'politico.com', 'Federal policy, trade legislation, regulatory pipeline, and government affairs.'),
                ]
            },
            {
                'title': 'Commercial Real Estate & Industrial Trade Press',
                'description': 'Specialized publications covering CRE markets, transactions, and industrial real estate.',
                'sources': [
                    ('Green Street', 'greenstreet.com', 'Institutional CRE research, REIT analysis, and cap rate intelligence.'),
                    ('CoStar', 'costar.com', 'Commercial real estate data, transaction records, and market analytics.'),
                    ('BisNow', 'bisnow.com', 'CRE news, events, and market coverage across major metros.'),
                    ('Connect CRE', 'connect.media', 'Deal announcements, project news, and CRE transaction coverage.'),
                    ('GlobeSt', 'globest.com', 'National CRE news with strong industrial and investment coverage.'),
                    ('The Real Deal', 'therealdeal.com', 'Breaking CRE deals, development news, and market intelligence.'),
                    ('Commercial Observer', 'commercialobserver.com', 'CRE finance, CMBS, lending, and investment sales coverage.'),
                    ('Propmodo', 'propmodo.com', 'Proptech, industrial innovation, and real estate technology trends.'),
                ]
            },
            {
                'title': 'Supply Chain, Freight & Logistics',
                'description': 'Specialized trade publications covering the supply chain ecosystem that drives industrial demand.',
                'sources': [
                    ('FreightWaves', 'freightwaves.com', 'Real-time freight market data, trucking rates, and capacity intelligence.'),
                    ('Journal of Commerce', 'joc.com', 'Port operations, ocean freight, intermodal, and global trade flows.'),
                    ('Supply Chain Dive', 'supplychaindive.com', 'Supply chain strategy, disruption news, and logistics operations.'),
                    ('DC Velocity', 'dcvelocity.com', 'Distribution center operations, warehouse management, and 3PL coverage.'),
                    ('Pacific Maritime Magazine', 'pacmar.com', 'LA/Long Beach port operations, labor, and container shipping.'),
                ]
            },
            {
                'title': 'Manufacturing & Industry Verticals',
                'description': 'Trade publications covering the industries that occupy and drive demand for industrial space.',
                'sources': [
                    ('Industry Week', 'industryweek.com', 'Manufacturing operations, reshoring trends, and factory investment.'),
                    ('Modern Materials Handling', 'mmh.com', 'Warehouse operations, automation, and distribution technology.'),
                    ('Food Logistics', 'foodlogistics.com', 'Cold chain, food distribution, and grocery supply chain — a major IE demand driver.'),
                ]
            },
            {
                'title': 'California & Regional Business',
                'description': 'Statewide and metropolitan business publications covering the California economy and policy.',
                'sources': [
                    ('Los Angeles Times', 'latimes.com', 'Statewide business, economic, and policy news from California\'s largest paper.'),
                    ('Los Angeles Business Journal', 'labusinessjournal.com', 'LA-focused business news, deals, and company moves.'),
                    ('CalMatters', 'calmatters.org', 'Nonpartisan California policy and legislation — CARB, AB5, warehouse rules, labor law.'),
                    ('San Diego Business Journal', 'sdbj.com', 'San Diego business, real estate, and economic news.'),
                    ('IE Business Daily', 'iebusinessdaily.com', 'Inland Empire business news, economic development, and local deals.'),
                ]
            },
            {
                'title': 'Southern California Regional Press',
                'description': 'Local newspapers covering communities across the Inland Empire, Los Angeles, Orange County, and San Diego.',
                'sources': [
                    ('Daily Bulletin / Inland Valley Daily Bulletin', 'dailybulletin.com', 'Covers the western Inland Empire including Ontario, Rancho Cucamonga, and Chino.'),
                    ('The Press-Enterprise', 'pe.com', 'Covers Riverside County, including Riverside, Corona, and Moreno Valley.'),
                    ('The Sun / San Bernardino Sun', 'sbsun.com', 'Covers San Bernardino County including San Bernardino, Fontana, and Rialto.'),
                    ('Redlands Daily Facts', 'redlandsdailyfacts.com', 'Covers Redlands, Loma Linda, and the eastern San Bernardino Valley.'),
                    ('Los Angeles Daily News', 'dailynews.com', 'Covers the San Fernando Valley and greater LA County.'),
                    ('Press-Telegram', 'presstelegram.com', 'Covers Long Beach, Carson, and the South Bay industrial corridor.'),
                    ('Daily Breeze', 'dailybreeze.com', 'Covers the South Bay including Torrance, Hawthorne, and El Segundo.'),
                    ('San Gabriel Valley Tribune', 'sgvtribune.com', 'Covers the San Gabriel Valley including City of Industry and El Monte.'),
                    ('Pasadena Star-News', 'pasadenastarnews.com', 'Covers Pasadena and the eastern San Gabriel Valley.'),
                    ('Whittier Daily News', 'whittierdailynews.com', 'Covers Whittier, Santa Fe Springs, and the southeast LA industrial corridor.'),
                    ('Orange County Register', 'ocregister.com', 'Covers all of Orange County business, real estate, and economic news.'),
                    ('San Diego Union-Tribune', 'sandiegouniontribune.com', 'Covers San Diego County business, development, and port activity.'),
                ]
            },
        ]

        total = sum(len(g['sources']) for g in source_groups)

        groups_html = ''
        for group in source_groups:
            rows = ''
            for name, domain, desc in group['sources']:
                rows += f'''<div class="src-row">
  <div class="src-name-wrap">
    <a href="https://{domain}" target="_blank" class="src-name">{name}</a>
    <span class="src-domain">{domain}</span>
  </div>
  <p class="src-desc">{desc}</p>
</div>'''
            groups_html += f'''<div class="src-group">
  <div class="src-group-header">
    <h2 class="src-group-title">{group['title']}</h2>
    <p class="src-group-desc">{group['description']}</p>
  </div>
  <div class="src-rows">{rows}</div>
</div>'''

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Source Directory | SoCal Industrial Journal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONTS}" rel="stylesheet">
  <style>{SHARED_CSS}
    body {{ padding-top: 120px; }}
    @media (max-width: 600px) {{ body {{ padding-top: 140px; }} }}

    .src-group {{
      margin-bottom: 3rem;
      border: 1px solid var(--rule);
      background: #fff;
    }}
    .src-group-header {{
      padding: 1.5rem 2rem 1.25rem;
      border-bottom: 1px solid var(--rule);
      background: var(--parchment);
    }}
    .src-group-title {{
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 1.4rem;
      font-weight: 400;
      color: var(--ink);
      margin-bottom: 0.3rem;
    }}
    .src-group-desc {{
      font-family: 'Jost', sans-serif;
      font-size: 0.78rem;
      color: var(--muted);
      line-height: 1.5;
    }}
    .src-rows {{
      padding: 0.5rem 0;
    }}
    .src-row {{
      display: grid;
      grid-template-columns: 240px 1fr;
      gap: 1.5rem;
      align-items: start;
      padding: 1rem 2rem;
      border-bottom: 1px solid var(--rule);
    }}
    .src-row:last-child {{ border-bottom: none; }}
    .src-name-wrap {{
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }}
    .src-name {{
      font-family: 'Jost', sans-serif;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--ink);
      text-decoration: none;
      transition: color 0.15s;
    }}
    .src-name:hover {{ color: var(--accent); }}
    .src-domain {{
      font-family: 'Jost', sans-serif;
      font-size: 0.68rem;
      color: var(--muted);
      letter-spacing: 0.03em;
    }}
    .src-desc {{
      font-family: 'Jost', sans-serif;
      font-size: 0.82rem;
      color: var(--ink-light);
      line-height: 1.6;
    }}
    @media (max-width: 700px) {{
      .src-row {{ grid-template-columns: 1fr; gap: 0.4rem; }}
    }}
  </style>
</head>
<body>
{generate_header('sources')}

<main style="max-width: 1000px; margin: 0 auto; padding: 2.5rem 2rem;">

  <div class="page-header">
    <a href="index.html" class="back-link">← Front Page</a>
    <h1 class="page-title">Source Directory</h1>
    <p class="page-count">{total} publications across 6 categories</p>
  </div>

  <p style="font-family:'Jost',sans-serif;font-size:0.88rem;color:var(--ink-light);line-height:1.75;margin-bottom:2.5rem;max-width:680px;">
    The SoCal Industrial Journal aggregates news from {total} sources spanning wire services, national business press,
    CRE trade publications, supply chain and logistics trade press, industry verticals, and regional Southern California
    newspapers. Each run searches the past 24 hours across all sources; articles are retained for 72 hours.
  </p>

  {groups_html}

</main>

<footer class="site-footer">
  <div class="footer-name">SoCal Industrial Journal</div>
  <div class="footer-sources">Sourced from {total} national, trade, and regional publications</div>
  <div>Rolling 72-hour window &nbsp;·&nbsp; Updates every 2 hours &nbsp;·&nbsp; Summaries refreshed daily</div>
</footer>

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
        print(f"   ✓ {cat_title} page ({len(categories[cat_key])} articles)")

    print("📄 Generating source directory page...")
    sources_page = generate_sources_page()
    with open('docs/sources.html', 'w', encoding='utf-8') as f:
        f.write(sources_page)
    print("   ✓ Source directory created")

    print("✅ Generated 9 HTML pages (1 Front Page + 7 category pages + 1 Source Directory)")
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

    # ── Clustering ────────────────────────────────────────────
    # Build display items: clusters + standalone articles
    # Load cluster synthesis cache (persists across runs)
    cluster_synth_cache = {}
    try:
        with open('cluster_cache.json', 'r') as f:
            cluster_synth_cache = json.load(f)
    except FileNotFoundError:
        pass

    display_items = cluster_articles(data['articles'])

    # Synthesize headlines/summaries for any new clusters
    needs_save = False
    for item in display_items:
        if item.get('is_cluster'):
            synth_key = 'cluster_' + '_'.join(
                sorted(a.get('id', a['headline'][:20]) for a in item['articles'])
            )
            if synth_key not in cluster_synth_cache:
                needs_save = True
            synthesize_cluster(item, cluster_synth_cache)

    if needs_save:
        with open('cluster_cache.json', 'w') as f:
            json.dump(cluster_synth_cache, f, indent=2)
        print("   💾 Cluster synthesis cache saved")

    # ── HTML generation ───────────────────────────────────────
    print("🎨 Generating HTML...")
    generate_html(data, summaries, display_items)
    
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print(f"   Total articles: {len(data['articles'])}")
    print(f"   New this run: {added_count}")
    clusters = [d for d in display_items if d.get('is_cluster')]
    print(f"   Clusters formed: {len(clusters)}")
    print(f"   Next update: In 2 hours")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
