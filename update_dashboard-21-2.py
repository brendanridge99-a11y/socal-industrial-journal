#!/usr/bin/env python3
"""
SoCal Industrial Journal - Automated News Aggregator
v21-0: Rebuilt category structure and editorial logic
Categories: Economy · Industries · Logistics · Policy · SoCal
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

# ─────────────────────────────────────────────────────────────
# SUBMARKET DEFINITIONS
# Cities sourced from SoCal_Markets_by_City.xlsx
# Used to tag socal articles with their submarket
# ─────────────────────────────────────────────────────────────

SUBMARKET_CITIES = {
    'inland-empire': [
        'adelanto', 'apple valley', 'banning', 'barstow', 'beaumont',
        'bloomington', 'calimesa', 'cherry valley', 'chino', 'chino hills',
        'colton', 'corona', 'eastvale', 'fontana', 'grand terrace',
        'hesperia', 'highland', 'indio', 'jurupa valley', 'lake elsinore',
        'loma linda', 'march air reserve base', 'menifee', 'mentone',
        'montclair', 'moreno valley', 'murrieta', 'norco', 'oak hills',
        'ontario', 'perris', 'rancho cucamonga', 'redlands', 'rialto',
        'riverside', 'san bernardino', 'san jacinto', 'temecula', 'upland',
        'victorville', 'yucaipa', 'inland empire',
    ],
    'los-angeles': [
        'agoura hills', 'alhambra', 'altadena', 'arcadia', 'arleta',
        'artesia', 'azusa', 'baldwin park', 'bell', 'bell gardens',
        'bellflower', 'beverly hills', 'burbank', 'calabasas', 'canoga park',
        'canyon country', 'carson', 'castaic', 'cerritos', 'chatsworth',
        'city of industry', 'claremont', 'commerce', 'compton', 'covina',
        'cudahy', 'culver city', 'diamond bar', 'downey', 'duarte',
        'east rancho dominguez', 'el monte', 'el segundo', 'encino',
        'gardena', 'glendale', 'glendora', 'granada hills', 'hacienda heights',
        'harbor city', 'hawaiian gardens', 'hawthorne', 'hermosa beach',
        'hollywood', 'huntington park', 'inglewood', 'irwindale',
        'la crescenta', 'la mirada', 'la puente', 'la verne', 'lakewood',
        'lancaster', 'lawndale', 'lomita', 'long beach', 'los angeles',
        'lynwood', 'manhattan beach', 'marina del rey', 'maywood',
        'mission hills', 'monrovia', 'montebello', 'monterey park',
        'newbury park', 'newhall', 'north hills', 'north hollywood',
        'northridge', 'norwalk', 'pacoima', 'palmdale', 'panorama city',
        'paramount', 'pasadena', 'pico rivera', 'playa vista', 'pomona',
        'rancho dominguez', 'rancho palos verdes', 'redondo beach', 'reseda',
        'rolling hills estates', 'rosemead', 'rowland heights', 'san dimas',
        'san fernando', 'san gabriel', 'san pedro', 'santa clarita',
        'santa fe springs', 'santa monica', 'sherman oaks', 'signal hill',
        'south el monte', 'south gate', 'south pasadena', 'studio city',
        'sun valley', 'sunland', 'sylmar', 'tarzana', 'temple city',
        'thousand oaks', 'toluca lake', 'torrance', 'tujunga',
        'universal city', 'valencia', 'van nuys', 'vernon', 'walnut',
        'west covina', 'west hills', 'west hollywood', 'westlake village',
        'whittier', 'wilmington', 'woodland hills',
    ],
    'orange-county': [
        'aliso viejo', 'anaheim', 'brea', 'buena park', 'capistrano beach',
        'corona del mar', 'costa mesa', 'cypress', 'dana point',
        'foothill ranch', 'fountain valley', 'fullerton', 'garden grove',
        'huntington beach', 'irvine', 'la habra', 'la palma', 'ladera ranch',
        'laguna beach', 'laguna hills', 'laguna niguel', 'laguna woods',
        'lake forest', 'los alamitos', 'mission viejo', 'newport beach',
        'orange', 'placentia', 'rancho santa margarita', 'san clemente',
        'san juan capistrano', 'santa ana', 'seal beach', 'stanton',
        'tustin', 'westminster', 'yorba linda', 'orange county',
    ],
    'san-diego': [
        'bonita', 'cardiff by the sea', 'carlsbad', 'chula vista',
        'coronado', 'del mar', 'el cajon', 'encinitas', 'escondido',
        'imperial beach', 'la jolla', 'la mesa', 'lakeside', 'lemon grove',
        'national city', 'oceanside', 'otay mesa', 'poway',
        'rancho santa fe', 'san diego', 'san marcos', 'san ysidro',
        'santee', 'solana beach', 'spring valley', 'vista', 'san diego county',
    ],
}

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
                "sources": [
                    "Bloomberg", "Wall Street Journal", "Reuters", "Politico",
                    "Green Street", "Connect CRE", "BisNow", "CoStar", "GlobeSt",
                    "The Real Deal", "Commercial Observer", "Propmodo",
                    "Supply Chain Dive", "FreightWaves", "Journal of Commerce",
                    "DC Velocity", "Pacific Maritime Magazine",
                    "Industry Week", "Modern Materials Handling", "Food Logistics",
                    "Los Angeles Times", "CalMatters", "Los Angeles Business Journal",
                    "San Diego Business Journal", "IE Business Daily",
                    "Daily Bulletin", "Los Angeles Daily News", "Press-Telegram",
                    "San Gabriel Valley Tribune", "Whittier Daily News", "The Sun",
                    "The Press-Enterprise", "Redlands Daily Facts", "Pasadena Star-News",
                    "Orange County Register", "Daily Breeze", "San Diego Union-Tribune"
                ],
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

# ─────────────────────────────────────────────────────────────
# RSS HARVEST INGESTION
# Reads rss_harvest.json written by the Cloudflare Worker.
# Categorizes raw RSS items via a lightweight Claude call
# (no web search tool — just headline + description → category).
# ─────────────────────────────────────────────────────────────

RSS_HARVEST_FILE = 'rss_harvest.json'

# Map RSS source names → canonical source names used in _base_score()
RSS_SOURCE_NAMES = {
    'FreightWaves':              'FreightWaves',
    'Journal of Commerce':       'Journal of Commerce',
    'Supply Chain Dive':         'Supply Chain Dive',
    'DC Velocity':               'DC Velocity',
    'Pacific Maritime':          'Pacific Maritime Magazine',
    'The Real Deal':             'The Real Deal',
    'Connect CRE':               'Connect CRE',
    'GlobeSt':                   'GlobeSt',
    'BisNow':                    'BisNow',
    'Commercial Observer':       'Commercial Observer',
    'Propmodo':                  'Propmodo',
    'Industry Week':             'Industry Week',
    'Modern Materials Handling': 'Modern Materials Handling',
    'Food Logistics':            'Food Logistics',
    'Los Angeles Times':         'Los Angeles Times',
    'CalMatters':                'CalMatters',
    'Los Angeles Business Journal': 'Los Angeles Business Journal',
    'San Diego Business Journal':'San Diego Business Journal',
    'IE Business Daily':         'IE Business Daily',
    'Daily Bulletin':            'Daily Bulletin',
    'The Press-Enterprise':      'The Press-Enterprise',
    'The Sun':                   'The Sun',
    'Redlands Daily Facts':      'Redlands Daily Facts',
    'Los Angeles Daily News':    'Los Angeles Daily News',
    'Press-Telegram':            'Press-Telegram',
    'Daily Breeze':              'Daily Breeze',
    'San Gabriel Valley Tribune':'San Gabriel Valley Tribune',
    'Pasadena Star-News':        'Pasadena Star-News',
    'Whittier Daily News':       'Whittier Daily News',
    'Orange County Register':    'Orange County Register',
    'San Diego Union-Tribune':   'San Diego Union-Tribune',
}

# Sources that are broadly relevant — apply loose inclusion filter
# (accept most articles). Sources where we need tighter filtering
# because they cover non-industrial topics heavily.
BROAD_SOURCES = {
    'Los Angeles Times', 'Los Angeles Business Journal',
    'San Diego Business Journal', 'CalMatters',
    'Orange County Register', 'San Diego Union-Tribune',
    'Los Angeles Daily News', 'Press-Telegram', 'Daily Breeze',
    'San Gabriel Valley Tribune', 'Pasadena Star-News', 'Whittier Daily News',
    'Daily Bulletin', 'The Press-Enterprise', 'The Sun', 'Redlands Daily Facts',
    'IE Business Daily',
}

# Sources where almost every article is relevant — minimal filtering needed
SPECIALTY_SOURCES = {
    'FreightWaves', 'Journal of Commerce', 'Supply Chain Dive', 'DC Velocity',
    'Pacific Maritime', 'The Real Deal', 'Connect CRE', 'GlobeSt', 'BisNow',
    'Commercial Observer', 'Propmodo', 'Industry Week', 'Modern Materials Handling',
    'Food Logistics',
}


def load_rss_harvest():
    """
    Read rss_harvest.json written by the Cloudflare Worker.
    Returns list of raw article dicts, or [] if file missing/stale.
    Considers harvest stale if older than 3 hours.
    """
    from datetime import timezone
    try:
        with open(RSS_HARVEST_FILE, 'r') as f:
            harvest = json.load(f)
    except FileNotFoundError:
        print("   ℹ️  No rss_harvest.json found — skipping RSS tier")
        return []
    except json.JSONDecodeError as e:
        print(f"   ⚠️  rss_harvest.json parse error: {e} — skipping RSS tier")
        return []

    # Staleness check
    harvested_at = harvest.get('harvested_at', '')
    if harvested_at:
        try:
            harvest_dt = datetime.fromisoformat(harvested_at.replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - harvest_dt).total_seconds() / 3600
            if age_hours > 3:
                print(f"   ⚠️  rss_harvest.json is {age_hours:.1f}h old — skipping RSS tier")
                return []
        except Exception:
            pass

    articles = harvest.get('articles', [])
    success = harvest.get('feeds_successful', 0)
    total = harvest.get('feeds_attempted', 0)
    count = harvest.get('articles_count', len(articles))
    print(f"   📡 RSS harvest: {success}/{total} feeds · {count} articles")

    # Log per-feed status
    for fs in harvest.get('feed_status', []):
        if not fs.get('success'):
            print(f"      ❌ {fs['source']}: {fs.get('error', 'unknown error')}")

    return articles


def categorize_rss_articles(raw_items, existing_articles):
    """
    Takes raw RSS items (headline + url + source + description),
    filters out duplicates against existing database, then sends
    batches to Claude for categorization + summary generation.

    Uses no web search tool — classification from headline/description only.
    Returns list of fully-formed article dicts ready for add_new_articles().
    """
    if not raw_items:
        return []

    print(f"🗂️  Categorizing {len(raw_items)} RSS items...")

    # Pre-filter: deduplicate against existing database
    existing_urls = {a['url'] for a in existing_articles}
    existing_headlines = {a['headline'].lower().strip() for a in existing_articles}

    candidates = []
    for item in raw_items:
        if item['url'] in existing_urls:
            continue
        if item['headline'].lower().strip() in existing_headlines:
            continue
        candidates.append(item)

    print(f"   {len(candidates)} after dedup against database ({len(raw_items) - len(candidates)} already known)")

    if not candidates:
        return []

    # Split into specialty (include most) and broad (filter aggressively)
    specialty = [i for i in candidates if RSS_SOURCE_NAMES.get(i['source'], i['source']) in SPECIALTY_SOURCES]
    broad = [i for i in candidates if RSS_SOURCE_NAMES.get(i['source'], i['source']) in BROAD_SOURCES]
    other = [i for i in candidates if i not in specialty and i not in broad]

    print(f"   Specialty sources: {len(specialty)} items")
    print(f"   Broad sources (filtered): {len(broad)} items")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    all_results = []

    # Process specialty sources in larger batches (less filtering needed)
    all_results.extend(_categorize_batch(client, specialty, batch_size=20, strict_filter=False))

    # Process broad sources in smaller batches with strict industrial filter
    all_results.extend(_categorize_batch(client, broad + other, batch_size=15, strict_filter=True))

    print(f"   ✅ {len(all_results)} articles accepted after categorization")
    return all_results


def _categorize_batch(client, items, batch_size=20, strict_filter=False):
    """
    Send one batch of RSS items to Claude for categorization.
    Returns list of article dicts.
    """
    if not items:
        return []

    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = _run_categorization_call(client, batch, strict_filter)
        results.extend(batch_results)
        print(f"   Batch {i//batch_size + 1}: {len(batch_results)}/{len(batch)} accepted")

    return results


def _run_categorization_call(client, items, strict_filter=False):
    """
    Single categorization API call for a batch of RSS items.
    No web search — works from headline + description only.
    Returns list of article dicts.
    """
    today = datetime.utcnow().strftime("%B %d, %Y")

    filter_instruction = """
INCLUSION FILTER (strict — these are general publications):
Include ONLY articles with a clear, direct connection to:
- Industrial/commercial real estate transactions, development, or market conditions
- Supply chain, logistics, freight, port, or warehouse operations
- Tenant industries: major retailer, distributor, manufacturer, e-commerce operator
- California/SoCal economic or regulatory conditions affecting business
- Macroeconomic forces (Fed, rates, tariffs, GDP, employment, commodities)
- Policy directly affecting industrial operations, development, or trade

EXCLUDE: Crime, sports, entertainment, residential real estate, local politics
with no business angle, restaurant/food reviews, local events, weather,
obituaries, school district news, and any story with zero industrial relevance.
""" if strict_filter else """
INCLUSION FILTER (permissive — these are specialty trade publications):
These publications are pre-screened for relevance. Include unless the article
is clearly off-topic (e.g. a company profile piece with no news, an event
announcement with no market insight, or pure opinion with no factual content).
"""

    items_text = "\n\n".join([
        f"ITEM {idx+1}:\n"
        f"Source: {item['source']}\n"
        f"Headline: {item['headline']}\n"
        f"Description: {item.get('description', 'No description available')[:250]}"
        for idx, item in enumerate(items)
    ])

    prompt = f"""You are the editorial engine for the SoCal Industrial Journal — a professional intelligence publication for Southern California industrial real estate professionals.

Today's date: {today}

You will receive a batch of RSS feed items. For each item:
1. Decide whether to INCLUDE or EXCLUDE based on the filter below
2. If INCLUDE: assign a category and write a 3-4 sentence wire-service summary
3. If EXCLUDE: simply omit the item from your output

{filter_instruction}

CATEGORIES (assign exactly one):
- economy: Macro forces — Fed, rates, bonds, GDP, employment, commodities, capital markets, REIT performance, global economics
- industries: Tenant operations — expansions, closures, relocations, bankruptcies, reshoring, e-commerce strategy, operational decisions
- logistics: Movement of goods — ports, ocean freight, trucking, rail, air cargo, trade flows, inventory dynamics, supply chain disruption
- policy: Government actions — CARB, AB5, zoning, tariffs, infrastructure funding, labor regulations, building codes
- socal: Southern California specific — IE/LA/OC/SD industrial leases, sales, development, local market intelligence

SECONDARY CATEGORIES (optional, max 2, only when strongly relevant):
economy / industries / logistics / policy / socal

ARTICLE SUMMARY STANDARD — CRITICAL:
Wire service only. Report ONLY what the source states. Specific facts, figures, company names, locations.
NEVER: speculation, inference, "could impact", "may affect", market implications not in the source.
3-4 sentences. AP/Reuters style. Facts only.

SOURCE_TYPE: Mark as "paywalled" if the source typically requires subscription. Otherwise "free".
Paywalled sources: Wall Street Journal, Bloomberg, Green Street, Commercial Observer, CoStar.
All others in this batch: "free".

RSS ITEMS TO PROCESS:
{items_text}

Return ONLY valid JSON — no preamble, no explanation:
{{
  "articles": [
    {{
      "item_index": 1,
      "headline": "Exact headline from source",
      "source": "Source name as given",
      "source_type": "free or paywalled",
      "date": "{today}",
      "url": "URL from the RSS item",
      "summary": "3-4 sentence factual summary. Wire service standard.",
      "category": "economy / industries / logistics / policy / socal",
      "secondary_categories": []
    }}
  ]
}}

Include item_index so we can match back to original items for URL/date.
If no items pass the filter, return: {{"articles": []}}
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
            # No web_search tool — working from headline/description only
        )

        response_text = message.content[0].text.strip()

        # Clean markdown fences
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start < 0 or json_end <= json_start:
            return []

        result = json.loads(response_text[json_start:json_end])
        accepted = result.get('articles', [])

        # Restore original URLs and dates from RSS items (more reliable than Claude's)
        item_map = {idx+1: item for idx, item in enumerate(items)}
        enriched = []
        for art in accepted:
            idx = art.get('item_index')
            original = item_map.get(idx)
            if original:
                art['url'] = original['url']  # always use RSS URL
                art['source'] = RSS_SOURCE_NAMES.get(
                    original['source'], original['source']
                )
                # Use raw_date if available; Python date validator will handle formatting
                if original.get('raw_date'):
                    art['_raw_date'] = original['raw_date']
            enriched.append(art)

        return enriched

    except json.JSONDecodeError as e:
        print(f"      ⚠️  JSON parse error in categorization batch: {e}")
        return []
    except Exception as e:
        print(f"      ⚠️  Categorization batch failed: {e}")
        return []


def _parse_raw_date(raw_date_str):
    """
    Parse raw RSS date strings into "Month DD, YYYY" format.
    Handles RFC 2822 (Mon, 18 May 2026 10:30:00 +0000),
    ISO 8601 (2026-05-18T10:30:00Z), and common variations.
    Returns formatted string or None if unparseable.
    """
    if not raw_date_str:
        return None
    raw = raw_date_str.strip()

    # Try standard formats
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',     # RFC 2822: Mon, 18 May 2026 10:30:00 +0000
        '%a, %d %b %Y %H:%M:%S GMT',     # RFC 2822 GMT variant
        '%a, %d %b %Y %H:%M:%S +0000',   # explicit +0000
        '%Y-%m-%dT%H:%M:%S%z',           # ISO 8601 with tz
        '%Y-%m-%dT%H:%M:%SZ',            # ISO 8601 Z suffix
        '%Y-%m-%dT%H:%M:%S',             # ISO 8601 no tz
        '%Y-%m-%d %H:%M:%S',             # common variant
        '%Y-%m-%d',                       # date only
        '%B %d, %Y',                      # already formatted
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime('%B %d, %Y')
        except ValueError:
            continue

    # Try stripping timezone name at end (e.g. "Mon, 18 May 2026 10:30:00 EDT")
    import re
    cleaned = re.sub(r'\s+[A-Z]{2,4}$', '', raw)
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime('%B %d, %Y')
        except ValueError:
            continue

    return None


def normalize_rss_dates(articles):
    """
    Post-process RSS-sourced articles to convert raw_date to formatted date.
    Articles without a parseable date get today's date (conservative assumption).
    """
    today_str = datetime.utcnow().strftime('%B %d, %Y')
    for art in articles:
        raw = art.pop('_raw_date', None)
        if raw:
            parsed = _parse_raw_date(raw)
            if parsed:
                art['date'] = parsed
                continue
        # Fall back to today if no raw date or unparseable
        if not art.get('date') or art['date'] == today_str:
            art['date'] = today_str
    return articles


def _build_editorial_prompt_core():
    """
    Returns the shared editorial mission, category definitions, tiebreakers,
    summary standard, and output format that every search call uses.
    Source list and any call-specific instructions are prepended by the caller.
    """
    return """
═══════════════════════════════════════════════════════════════
EDITORIAL MISSION
═══════════════════════════════════════════════════════════════

The SoCal Industrial Journal serves brokers, tenants, investors, developers,
and operators whose world touches Southern California industrial real estate.
It is a one-stop intelligence source — not a narrow trade publication.

The governing inclusion question for every article is:
"Would an industrially-minded person need to know this to be fully informed?"

If yes — include it, regardless of whether it explicitly mentions real estate.
The industrial lens is applied through how articles are categorized and summarized,
not by restricting what topics are covered.

EXCLUDE only:
- Pure residential real estate with no industrial angle
- Celebrity, entertainment, or sports with no economic or real estate angle
- Political horse-race coverage with no policy substance
- Stories with zero bearing on business, capital, commerce, or operations

═══════════════════════════════════════════════════════════════
CATEGORIES — DEFINITIONS AND TIEBREAKERS
═══════════════════════════════════════════════════════════════

There are FIVE categories. Assign each article to exactly ONE primary category.
The primary category is determined by what the story is PRIMARILY about — its
main subject — not whether the topic is touched on.

──────────────────────────────────────────────────────────────
CATEGORY 1: economy
──────────────────────────────────────────────────────────────
WHAT IT COVERS: The macroeconomic and financial environment that shapes
industrial real estate demand, capital flows, tenant business conditions,
and investment activity.

INCLUDE:
- Monetary policy: Fed decisions, interest rates, quantitative tightening/easing
- Credit markets: Corporate borrowing costs, bond yields, CMBS spreads, bank
  lending, credit availability, debt funds, life company activity
- Economic indicators: GDP, employment, consumer spending, business investment,
  PMI, retail sales, consumer confidence, leading indicators
- Currency and commodities: Dollar strength, oil and gas prices, diesel, metals,
  agricultural commodities, construction materials costs
- Capital markets: Equity trends, REIT performance nationally, institutional
  capital flows, foreign investment into US assets, IPOs, M&A as financial events
- Banking and finance: Bank health, commercial lending standards, financial
  regulation, fintech affecting capital markets
- Global economics: Trade balances, emerging markets, currency movements,
  geopolitical economic events

TECH STORIES → economy: If the technology represents a major capital markets
event, investment signal, or macroeconomic force rather than an operational
development. Example: A $2B institutional investment round in warehouse robotics
belongs here — it signals where capital is flowing, not how a warehouse operates.

TIEBREAKER vs industries: If a company story is about financial performance,
earnings, stock price, or capital structure with no operational news — it is
economy. If it is about what a company is doing operationally — it is industries.
Amazon Q3 earnings → economy. Amazon opening fulfillment centers → industries.

──────────────────────────────────────────────────────────────
CATEGORY 2: industries
──────────────────────────────────────────────────────────────
WHAT IT COVERS: The tenant universe. What companies and industries are doing
operationally — expansions, contractions, strategic shifts — that signal
changes in demand for industrial space.

The governing question: Does this tell us something about how a company uses,
needs, or thinks about physical space and operations?

INCLUDE:
- Operational decisions: Expansions, new facilities, closures, relocations,
  network restructuring, distribution strategy changes
- Bankruptcies and restructurings with real estate implications
- Reshoring, nearshoring, and manufacturing investment decisions
- Retail store opening and closing programs
- E-commerce fulfillment strategy evolution and last-mile network changes
- Labor decisions signaling operational scale: mass hiring or layoffs in
  operations, logistics, or manufacturing roles
- Industry-wide structural shifts in how sectors use physical space
- New entrants into markets where they will need industrial space

PRIORITY TENANT INDUSTRIES (highest to lowest):
1. Logistics and distribution — 3PLs, freight forwarders, last-mile operators
2. Retail and e-commerce — store networks, fulfillment, direct-to-consumer
3. Consumer goods and food and beverage — CPG, cold storage, grocery distribution
4. Tech and advanced manufacturing — data centers, EV, semiconductor assembly
5. Automotive and EV — manufacturing, parts distribution, EV supply chain
6. Aerospace and defense — contractors, manufacturing, government supply chain
7. Construction and building materials — equipment, materials, distribution
8. Healthcare supply chain — medical devices, pharmaceutical distribution
   (operational and supply chain angle required — not clinical healthcare)
9. Energy and renewables — solar, EV charging infrastructure, energy storage
   (operational or infrastructure angle required)

EXCLUDE from industries:
- Pure financial performance with no operational news
- Executive changes without a strategic operational announcement
- Stock price movements, analyst ratings, shareholder activity
- Earnings reports that contain no operational guidance or news

TECH STORIES → industries: If the technology changes how a specific tenant
industry operates, produces, or manages its supply chain internally.
Example: Amazon deploying a new robotic picking system in fulfillment centers —
this is about how a tenant operates, not about the movement of goods.

──────────────────────────────────────────────────────────────
CATEGORY 3: logistics
──────────────────────────────────────────────────────────────
WHAT IT COVERS: The movement of goods at every geographic scale — global to
local. Ports, freight, shipping, rail, trucking, air cargo, trade flows,
and inventory dynamics that drive industrial demand signals.

INCLUDE:
- Ports and shipping: LA/Long Beach port activity, container volumes, congestion,
  drayage, labor, automation. Also: Rotterdam, Shanghai, Houston, Seattle, New
  York — because what happens at any major port flows through SoCal's supply chain
- Ocean freight: Container rates, vessel supply, shipping alliances, blank sailings,
  transpacific and transatlantic lane dynamics
- Freight and trucking: Truckload and LTL rates, carrier performance, driver market,
  fuel costs, capacity trends, spot vs contract rate dynamics
- Rail and intermodal: Class I railroad performance, intermodal volumes, inland
  ports, rail infrastructure investments
- Air cargo: Air freight rates, express delivery capacity, airport cargo operations
- Parcel and last mile: UPS, FedEx, USPS, regional carriers, delivery economics,
  returns infrastructure — as system-level dynamics, not company strategy
- 3PL sector performance as a system participant and demand signal
- Trade flows: Import and export volumes, trade lane shifts, nearshoring and
  reshoring effects on cargo patterns, customs and border activity
- Inventory dynamics: Inventory-to-sales ratios, safety stock trends,
  just-in-time vs just-in-case shifts — these directly signal warehouse demand
- Infrastructure investment: Highway funding, port expansion, rail investment,
  anything changing the physical capacity of the goods movement system
- Supply chain disruption: Weather, geopolitical events, labor actions,
  anything interrupting the flow of goods at scale

TECH STORIES → logistics: If the technology changes how goods move, how ports
operate, how freight is tracked, or how delivery networks function.
Example: Autonomous trucks beginning commercial routes, or AI-powered freight
matching platforms — these change the movement system itself.

TIEBREAKER vs industries: Movement of goods and the infrastructure that supports
it → logistics. A company's operational strategy and space decisions → industries.
FedEx cutting delivery routes → logistics. FedEx closing distribution centers → industries.

TIEBREAKER vs socal: A logistics trend, rate, or system dynamic → logistics
regardless of geography. A specific SoCal facility or infrastructure project → socal.
LA/LB port volume trends → logistics. New rail facility breaking ground in San
Bernardino → socal.

──────────────────────────────────────────────────────────────
CATEGORY 4: policy
──────────────────────────────────────────────────────────────
WHAT IT COVERS: Government actions that change the cost, feasibility, or
strategy of building, operating, or occupying industrial space — or that
change the operating environment of the businesses that use it.

THREE POLICY DIMENSIONS:

1. Operating environment — regulations affecting how tenants run their businesses:
   - CARB truck emissions rules and zero emission vehicle mandates
   - Warehouse worker protection laws: quotas, rest periods, injury reporting
   - AB5 and gig worker classification affecting logistics operators
   - Minimum wage increases affecting tenant operating costs
   - Water and energy mandates affecting industrial facilities
   - OSHA warehouse safety rules
   - EPA environmental compliance requirements
   - DOT trucking regulations: hours of service, weight limits, vehicle standards
   - Labor relations: NLRB decisions affecting logistics and manufacturing
   - Union activity and collective bargaining outcomes

2. Development environment — regulations affecting how industrial space gets built:
   - CEQA and entitlement processes for industrial development
   - City and county zoning changes — industrial moratoriums are high priority
   - AB98 and warehouse development standards
   - Development impact fees and permitting requirements
   - Environmental impact requirements: stormwater, air quality, noise, setbacks
   - Building codes affecting industrial construction
   - Federal and state incentives for manufacturing or distribution investment

3. Trade and market environment — policy affecting goods flow and capital:
   - Tariffs and trade agreements: direct effect on import volumes and tenant demand
   - Port and customs policy
   - Tax policy: corporate tax, property tax, 1031 exchanges, opportunity zones
   - Federal infrastructure bills and what gets funded
   - Sanctions and trade restrictions affecting specific tenant industries
   - Foreign investment policy affecting capital flows into US industrial assets

ALSO INCLUDE policy affecting major tenant industries specifically:
- Automotive and EV regulations driving manufacturing transition
- Food safety regulations affecting distribution tenants
- Defense spending and contract policy affecting aerospace tenants
- Healthcare regulations affecting medical device and pharmaceutical distribution

EXCLUDE: Political horse-race coverage, elections, polling, and personality-
driven political stories with no direct policy substance or business implication.

TIEBREAKER vs logistics: The government action itself → policy. The operational
or market impact of that action → logistics.
CARB adopts new zero emission truck mandate → policy.
Trucking industry scrambles to comply with new CARB rules → logistics.

TIEBREAKER vs socal: Statewide or national policy → policy. Policy specifically
originating in or targeted at SoCal industrial markets → socal.
AB98 signed statewide → policy. City of Chino Hills passes industrial moratorium → socal.

──────────────────────────────────────────────────────────────
CATEGORY 5: socal
──────────────────────────────────────────────────────────────
WHAT IT COVERS: Everything specifically happening in Southern California
industrial real estate — the complete local picture for brokers, investors,
tenants, and developers operating in these markets.

TWO STORY TYPES:

Type 1 — Market activity (the deal sheet):
- Industrial leases: tenant, landlord, square footage, submarket, brokers
- Investment sales: building and land sales, portfolio deals, entity-level
  transactions involving SoCal industrial assets
- Development: ground breakings, construction starts, spec development,
  build-to-suit announcements, project completions
- Land activity: acquisitions, entitlements, rezoning for industrial use
- Submarket trends: vacancy rates, absorption figures, rent movements,
  supply pipeline data for IE, LA, OC, and SD
- Investment activity: institutional capital targeting SoCal industrial,
  REIT acquisitions, fund activity in the market
- Market reports: broker reports, CoStar data, Green Street analysis
  specifically covering SoCal industrial submarkets

Type 2 — Local industrial intelligence:
- Policy, regulatory, or government actions specifically targeting SoCal
  industrial markets: city industrial moratoriums, local zoning decisions,
  submarket-specific ordinances
- Infrastructure with direct industrial real estate implications for SoCal:
  port expansions, highway projects, rail investments affecting specific
  SoCal industrial submarkets
- Major employer moves specifically affecting SoCal industrial markets:
  significant tenant expansions, relocations, or closures in IE, LA, OC, SD

SUBMARKET PRIORITY ORDER:
1. Inland Empire — highest priority (largest US industrial market by size)
2. Los Angeles — second priority (port adjacency, infill industrial, largest metro)
3. San Diego — third priority (border logistics, cross-border manufacturing)
4. Orange County — fourth priority

EXCLUDE from socal:
- Office, retail, residential, or mixed-use deals even if in SoCal
- General SoCal business news without a direct industrial real estate angle
- National or statewide stories without a specific SoCal industrial transaction,
  trend, or development directly attached

KEY RULE: If a policy story is specifically about SoCal industrial (a city
moratorium, a local zoning decision, a submarket ordinance) — it belongs in
socal, not policy. The local specificity takes precedence.

═══════════════════════════════════════════════════════════════
TECHNOLOGY TIEBREAKER SUMMARY
═══════════════════════════════════════════════════════════════

Ask: What is the technology primarily doing in this story?

Moving goods or operating delivery/port infrastructure → logistics
Operating a specific tenant business internally → industries
Moving capital or signaling macro investment trends → economy

Examples:
- Autonomous trucks on I-10 commercial routes → logistics
- Amazon deploying robotic pickers in fulfillment centers → industries
- $2B institutional round in warehouse robotics → economy
- Port of Long Beach AI crane automation → logistics
- Walmart rolling out AI inventory management → industries
- Proptech investment hits record high → economy

═══════════════════════════════════════════════════════════════
SECONDARY CATEGORIES
═══════════════════════════════════════════════════════════════

After assigning the primary category, optionally assign up to 2 secondary
categories where the article has STRONG, DIRECT relevance — not tangential.

Valid secondary categories: economy, industries, logistics, policy, socal

SECONDARY CATEGORY EXAMPLES:
- A Prologis lease in Ontario → primary: socal, secondary: ["industries"]
- A Fed rate decision → primary: economy, secondary: [] (too broad)
- Amazon building a Fontana fulfillment center → primary: socal, secondary: ["industries", "logistics"]
- A CARB truck emissions ruling → primary: policy, secondary: ["logistics"]
- IE vacancy report → primary: socal, secondary: ["economy"]
- Port automation investment → primary: logistics, secondary: ["economy"]

═══════════════════════════════════════════════════════════════
ARTICLE SUMMARY STANDARD
═══════════════════════════════════════════════════════════════

CRITICAL: Article summaries must be wire-service standard. Report ONLY what
the source explicitly states. Include specific facts, figures, names, and
direct statements from the article.

NEVER include:
- Speculation or implications ("could impact", "may affect", "might signal")
- Market connections drawn by inference ("this suggests demand will...")
- Analysis or broker perspective
- Any language beyond what the source directly reports

Write 3-4 sentences. AP/Reuters style. Facts only.

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════

Return ONLY valid JSON. No other text.

{
  "articles": [
    {
      "headline": "Exact article headline",
      "source": "Source name",
      "source_type": "paywalled or free",
      "date": "May 12, 2026",
      "url": "Direct URL to article",
      "summary": "3-4 sentence factual summary. Wire-service standard. Report only what the source states. Specific facts, figures, names. No speculation, no inference, no market implications.",
      "category": "primary category key (economy / industries / logistics / policy / socal)",
      "secondary_categories": ["optional", "secondary"]
    }
  ]
}

CRITICAL: Only include articles published in the PAST 24 HOURS. Verify publication
date carefully. Return ONLY valid JSON. If no articles found: {"articles": []}
"""


def _run_search_call(client, sources_block, call_label, max_tokens=4000):
    """
    Execute one focused search call.
    sources_block: string describing which sources to search and any
                   call-specific instructions for those outlets.
    Returns list of raw article dicts (not yet validated/deduped).
    """
    prompt = f"""Search for the latest news articles published in the PAST 24 HOURS from these specific sources:

{sources_block}

{_build_editorial_prompt_core()}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}]
        )

        response_text = ""
        for block in message.content:
            if hasattr(block, 'type') and block.type == "text":
                response_text += block.text

        if not response_text.strip():
            print(f"   ⚠️  [{call_label}] Empty response")
            return []

        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
        else:
            print(f"   ⚠️  [{call_label}] No JSON found in response")
            return []

        result = json.loads(json_text)
        articles = result.get('articles', [])
        print(f"   ✅ [{call_label}] {len(articles)} articles")
        return articles

    except json.JSONDecodeError as je:
        print(f"   ⚠️  [{call_label}] JSON parse error: {je}")
        return []
    except Exception as e:
        print(f"   ⚠️  [{call_label}] Call failed: {e}")
        return []


def search_new_articles(existing_articles):
    """
    Web search tier — 5 focused calls for sources RSS cannot reach:
      1. Bloomberg (all sections)
      2. Wall Street Journal (+ Logistics Report + Pro Bankruptcy)
      3. Reuters + Politico
      4. CoStar + Green Street (paywalled CRE data)
      5. Open catch-all — any source, breaking news

    RSS tier (Cloudflare Worker) handles the other 28 sources.
    Results merged and deduped before returning.
    """
    print("🔍 Web search tier (wire services + catch-all)...")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    CALL_GROUPS = [

        # ── CALL 1: Bloomberg ──────────────────────────────────
        (
            "Bloomberg",
            """SOURCES FOR THIS SEARCH — Bloomberg only:
- Bloomberg (bloomberg.com) — markets, economics, real estate, law, logistics
- Bloomberg Law (bloomberg.com/law) — regulatory actions, labor rulings, NLRB decisions
- Bloomberg Intelligence — sector research on industrial RE, logistics, tenant industries

Search broadly. Focus on: Fed/monetary policy, CMBS/CRE lending, industrial REIT
performance, tariffs and trade policy, major tenant operational decisions,
supply chain and freight markets, capital markets affecting industrial investment.""",
            5000
        ),

        # ── CALL 2: Wall Street Journal ───────────────────────
        (
            "Wall Street Journal",
            """SOURCES FOR THIS SEARCH — Wall Street Journal only:
- Wall Street Journal (wsj.com) — markets, economy, business, real estate
- WSJ Logistics Report (wsj.com/logistics) — daily freight and supply chain coverage
- WSJ Pro Bankruptcy (wsj.com/pro/bankruptcy) — Chapter 11, restructurings, retail closures

Check wsj.com/logistics specifically — a dedicated beat producing daily
freight/port/trucking coverage. Check wsj.com/pro/bankruptcy for any
retail or industrial tenant filings signaling lease rejections or vacancies.""",
            4000
        ),

        # ── CALL 3: Reuters + Politico ────────────────────────
        (
            "Reuters + Politico",
            """SOURCES FOR THIS SEARCH:
- Reuters (reuters.com) — global wire: economy, markets, trade, corporate news
- Reuters California (reuters.com/world/us/california) — California regulatory and business news
- Politico (politico.com) — federal policy, trade legislation, regulatory pipeline

Check reuters.com/world/us/california for California regulatory actions (CARB,
labor law), port activity, and employer moves. Politico: look for trade/tariff
policy, federal infrastructure funding, NLRB actions, DOT/EPA regulations,
tax policy changes affecting CRE investment.""",
            4000
        ),

        # ── CALL 4: CoStar + Green Street + BisNow ───────────
        (
            "CoStar + Green Street + BisNow",
            """SOURCES FOR THIS SEARCH:
- CoStar (costar.com) — industrial market data, transaction records, submarket analytics
- Green Street (greenstreet.com) — institutional CRE research, REIT analysis, cap rates
- BisNow (bisnow.com) — CRE news and transaction coverage

Search for: IE/LA/OC/SD industrial market reports, vacancy and absorption data,
cap rate trends, REIT industrial performance, institutional capital flows into
industrial real estate, any CoStar submarket intelligence for Southern California,
industrial lease and sale transaction announcements.""",
            3500
        ),

        # ── CALL 5: Manufacturing + Industry Verticals ────────
        (
            "Manufacturing Verticals",
            """SOURCES FOR THIS SEARCH:
- Industry Week (industryweek.com) — manufacturing operations, reshoring, factory investment
- Food Logistics (foodlogistics.com) — cold chain, food distribution, grocery supply chain
- Modern Materials Handling (mmh.com) — warehouse operations, automation, distribution

These cover tenant industries that drive industrial space demand. Look for:
reshoring and nearshoring announcements, factory investments, warehouse automation
deployments, cold storage expansion, food and beverage distribution strategy changes,
any operational decisions signaling changes in space use.""",
            3000
        ),

        # ── CALL 6: SoCal Regional Papers ────────────────────
        (
            "SoCal Regional Newspapers",
            """SOURCES FOR THIS SEARCH — Southern California local newspapers:
- Daily Bulletin / Inland Valley Daily Bulletin (dailybulletin.com) — Ontario, Rancho Cucamonga, Chino, western IE
- The Press-Enterprise (pe.com) — Riverside, Corona, Moreno Valley, Perris
- The Sun / San Bernardino Sun (sbsun.com) — San Bernardino, Fontana, Rialto
- Redlands Daily Facts (redlandsdailyfacts.com) — Redlands, Loma Linda
- Los Angeles Daily News (dailynews.com) — San Fernando Valley, greater LA
- Press-Telegram (presstelegram.com) — Long Beach, Carson, South Bay
- Daily Breeze (dailybreeze.com) — Torrance, Hawthorne, El Segundo
- San Gabriel Valley Tribune (sgvtribune.com) — City of Industry, El Monte
- Pasadena Star-News (pasadenastarnews.com) — Pasadena, eastern San Gabriel Valley
- Whittier Daily News (whittierdailynews.com) — Whittier, Santa Fe Springs
- Orange County Register (ocregister.com) — all of Orange County
- San Diego Union-Tribune (sandiegouniontribune.com) — San Diego County

These local papers are the primary source for: city council industrial zoning
decisions, groundbreaking ceremonies, facility opening/closing announcements,
major employer moves into or out of specific IE/LA/OC/SD cities, local opposition
to warehouse development, and development permit approvals. Search specifically
for stories involving warehouses, distribution centers, manufacturing plants,
logistics operations, industrial parks, freight, and major employers.""",
            4000
        ),

        # ── CALL 7: Open Catch-All ────────────────────────────
        (
            "Breaking News Catch-All",
            """OPEN SEARCH — any source, any relevant topic published in the past 24 hours.

Find the most important news from the past 24 hours relevant to:
- Southern California industrial real estate (IE, LA, OC, San Diego submarkets)
- Supply chain, ports, freight, logistics
- Major tenant industries: retail, e-commerce, manufacturing, distribution
- Macroeconomic forces: Fed, rates, tariffs, employment, GDP
- California policy: CARB, warehouse worker rules, zoning, labor law

Include sources NOT on our primary list if they have genuinely important coverage.
This is the safety net for breaking news that might fall outside our RSS feeds.
Be selective — only include articles with real industrial relevance.""",
            4000
        ),
    ]

    all_raw_articles = []

    for call_num, (label, sources_block, max_tok) in enumerate(CALL_GROUPS, 1):
        print(f"\n   📡 Call {call_num}/7: {label}")
        articles = _run_search_call(client, sources_block, label, max_tokens=max_tok)
        all_raw_articles.extend(articles)

    print(f"\n   📊 7 calls completed — {len(all_raw_articles)} raw articles before dedup")

    # Within-batch deduplication
    seen_headlines = set()
    seen_urls = set()
    deduped = []
    for article in all_raw_articles:
        h = article.get("headline", "").lower().strip()
        u = article.get("url", "").strip()
        if h in seen_headlines or (u and u in seen_urls):
            continue
        seen_headlines.add(h)
        if u:
            seen_urls.add(u)
        deduped.append(article)

    dupes_removed = len(all_raw_articles) - len(deduped)
    if dupes_removed:
        print(f"   🔁 Removed {dupes_removed} within-batch duplicates")
    print(f"   ✅ {len(deduped)} web search articles passed to merge")
    return deduped


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

    # Valid category keys for the new structure
    valid_cats = {'economy', 'industries', 'logistics', 'policy', 'socal'}

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

        # DATE VALIDATION — reject articles outside retention window
        article_date_str = article.get('date', '')
        try:
            article_date = datetime.strptime(article_date_str, "%B %d, %Y")
            hours_old = (datetime.utcnow() - article_date).total_seconds() / 3600

            if hours_old > RETENTION_HOURS:
                skipped_count += 1
                days_old = int(hours_old / 24)
                print(f"⏭️  Skipped (too old - {days_old}d {int(hours_old)}h): {article['headline'][:50]}...")
                continue

        except (ValueError, AttributeError):
            skipped_count += 1
            print(f"⏭️  Skipped (invalid date '{article_date_str}'): {article['headline'][:50]}...")
            continue

        # Normalize category — map legacy keys if any slip through
        category = article.get('category', 'industries')
        legacy_map = {
            'economics': 'economy',
            'business': 'industries',
            'tech': 'industries',
            'supply-chain': 'logistics',
            'politics': 'policy',
            'local-deals': 'socal',
        }
        if category in legacy_map:
            category = legacy_map[category]
        if category not in valid_cats:
            category = 'industries'
        article['category'] = category

        # Validate and clean secondary_categories
        raw_secondary = article.get('secondary_categories', [])
        if isinstance(raw_secondary, list):
            article['secondary_categories'] = [
                legacy_map.get(c, c) for c in raw_secondary
                if legacy_map.get(c, c) in valid_cats
                and legacy_map.get(c, c) != article['category']
            ][:2]
        else:
            article['secondary_categories'] = []

        # Add required fields
        article['id'] = article_id
        article['added_at'] = current_time
        article['timestamp'] = article.get('timestamp', current_time)

        # Tag socal articles with their submarket(s)
        if article['category'] == 'socal':
            article['submarkets'] = tag_submarket(article)

        # SoCal overflow — if a non-socal article mentions a SoCal city,
        # create a lightweight overflow copy in socal so it surfaces in
        # the SoCal tab without cluttering the primary category.
        if article['category'] != 'socal':
            submarkets = tag_submarket_any(article)
            if submarkets:
                overflow = dict(article)
                overflow['id'] = article_id + '_loc'
                overflow['category'] = 'socal'
                overflow['submarkets'] = submarkets
                overflow['is_overflow'] = True
                overflow['overflow_from'] = article['category']
                if overflow['id'] not in existing_ids:
                    data['articles'].append(overflow)
                    existing_ids.add(overflow['id'])
                    print(f"   ↳ SoCal overflow ({', '.join(submarkets)}): {article['headline'][:50]}...")

        # Add the article (once — bug fix from v20)
        data['articles'].append(article)
        existing_ids.add(article_id)
        existing_urls.add(article_url)
        existing_headlines.add(article_headline)
        added_count += 1
        print(f"✅ Added [{article['category']}]: {article['headline'][:60]}...")

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

def tag_submarket(article):
    """
    Assign submarket tag(s) to a socal article.
    Returns list of submarket keys, or ['all'] if no city match found.
    """
    return _match_submarkets(article) or ['all']

def tag_submarket_any(article):
    """
    Check ANY article for SoCal city mentions.
    Returns list of matched submarket keys, or [] if none found.
    Used to create socal overflow copies.
    """
    return _match_submarkets(article)

def _match_submarkets(article):
    """
    Core city-matching logic. Uses word-boundary regex to avoid false positives.
    Returns list of matched submarket keys (may be empty).
    """
    import re
    text = (article.get('headline', '') + ' ' + article.get('summary', '')).lower()
    matched = []
    for submarket, cities in SUBMARKET_CITIES.items():
        for city in cities:
            pattern = r'\b' + re.escape(city) + r'\b'
            if re.search(pattern, text):
                matched.append(submarket)
                break
    return matched

# ─────────────────────────────────────────────────────────────
# CLUSTERING
# ─────────────────────────────────────────────────────────────

def cluster_articles(articles):
    """
    Group articles about the same real-world event into clusters.

    Phase 1 — Candidate filtering (no AI cost):
      Same category + published within 48 hours + overlapping named entity

    Phase 2 — AI confirmation (one batch call):
      Conservative: same entity + same specific event + same location.
      When in doubt, do NOT group.

    Returns display items: each is a single article dict or a cluster dict.
    """
    import re
    from datetime import timezone

    print("🔗 Clustering articles...")

    if len(articles) < 2:
        print("   Not enough articles to cluster")
        return [dict(a) for a in articles]

    def parse_date_dt(article):
        try:
            return datetime.strptime(article.get('date', ''), "%B %d, %Y")
        except Exception:
            return None

    def extract_tokens(text):
        words = re.findall(r"[A-Z][a-zA-Z]{4,}", text)
        stopwords = {
            'Federal', 'Reserve', 'California', 'Southern', 'Northern',
            'United', 'States', 'American', 'January', 'February', 'March',
            'April', 'August', 'September', 'October', 'November', 'December',
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
            'Sunday', 'Report', 'According', 'Industrial', 'Estate', 'Business',
            'Company', 'Group', 'Management',
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

    # Phase 1: candidate pairs
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

    # Phase 2: AI confirmation
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
3. Same location or jurisdiction (Ontario CA ≠ Ontario Canada)
4. Published within 48 hours of each other

DO NOT group if:
- Same company but different events (Amazon lease vs Amazon earnings)
- Same broad topic but different specific incidents
- One is a follow-up rather than the same announcement
- You are uncertain — when in doubt, do NOT group

Return ONLY a JSON array of pair numbers that pass ALL rules. Example: [1, 3, 5]
If no pairs qualify, return: []
No explanation or other text.

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
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            confirmed_pair_numbers = json.loads(response_text[json_start:json_end])
            confirmed_indices = {n - 1 for n in confirmed_pair_numbers}
        print(f"   Phase 2: AI confirmed {len(confirmed_indices)} pairs for clustering")
    except Exception as e:
        print(f"   ⚠️  Clustering AI call failed ({e}) — all articles remain standalone")
        return [dict(a) for a in arts]

    if not confirmed_indices:
        print("   No pairs confirmed — all articles remain standalone")
        return [dict(a) for a in arts]

    # Build clusters via union-find
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

    from collections import defaultdict
    groups = defaultdict(list)
    for i in range(len(arts)):
        groups[find(i)].append(i)

    display_items = []
    clustered_ids = set()

    for root, members in groups.items():
        if len(members) == 1:
            continue
        cluster_arts = [arts[i] for i in members]
        clustered_ids.update(members)

        dates = [parse_date_dt(a) for a in cluster_arts if parse_date_dt(a)]
        best_date = max(dates) if dates else datetime.utcnow()

        display_items.append({
            'is_cluster': True,
            'articles': cluster_arts,
            'category': cluster_arts[0]['category'],
            'cluster_headline': '',
            'cluster_summary': '',
            'date': best_date.strftime("%B %d, %Y"),
            'added_at': cluster_arts[0].get('added_at', ''),
            'source_count': len(cluster_arts),
        })
        sources = ', '.join(a['source'] for a in cluster_arts)
        print(f"   ✅ Cluster ({len(cluster_arts)} sources): {cluster_arts[0]['headline'][:55]}... [{sources}]")

    for i in range(len(arts)):
        if i not in clustered_ids:
            display_items.append(dict(arts[i]))

    print(f"   Result: {len([d for d in display_items if d.get('is_cluster')])} clusters + "
          f"{len([d for d in display_items if not d.get('is_cluster')])} standalone articles")

    return display_items


def synthesize_cluster(cluster, summaries_cache):
    """
    Generate a synthesized headline + summary for a cluster of articles.
    Cached in cluster_cache.json — same cluster not re-synthesized every run.
    """
    ids = sorted(a.get('id', a['headline'][:20]) for a in cluster['articles'])
    cache_key = 'cluster_' + '_'.join(ids)

    if cache_key in summaries_cache:
        cached = summaries_cache[cache_key]
        cluster['cluster_headline'] = cached['headline']
        cluster['cluster_summary'] = cached['summary']
        return cluster

    articles_text = "\n\n".join([
        f"Source: {a['source']}\nHeadline: {a['headline']}\nSummary: {a['summary']}"
        for a in cluster['articles']
    ])

    prompt = f"""Below are {len(cluster['articles'])} news articles from different outlets covering the same event.

{articles_text}

Your task:
1. Write a SHORT, specific headline (max 12 words). Be concrete — include the company name, location, and action. Example: "Prologis Leases 800,000 SF to Amazon in Ontario"
2. Write a 3-4 sentence factual synthesis pulling the best specific details from ALL sources — square footage, dollar figures, company names, broker names, locations, concrete facts. Wire-service style only. No speculation or analysis.

Return ONLY valid JSON:
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
        json_end = response_text.rfind('}') + 1
        result = json.loads(response_text[json_start:json_end])

        cluster['cluster_headline'] = result.get('headline', cluster['articles'][0]['headline'])
        cluster['cluster_summary'] = result.get('summary', cluster['articles'][0]['summary'])

        summaries_cache[cache_key] = {
            'headline': cluster['cluster_headline'],
            'summary': cluster['cluster_summary'],
        }
        print(f"   ✅ Synthesized: {cluster['cluster_headline'][:60]}...")

    except Exception as e:
        print(f"   ⚠️  Synthesis failed ({e}) — using lead article")
        cluster['cluster_headline'] = cluster['articles'][0]['headline']
        cluster['cluster_summary'] = cluster['articles'][0]['summary']

    return cluster


# ─────────────────────────────────────────────────────────────
# SUMMARIES GENERATION (once daily)
# ─────────────────────────────────────────────────────────────

def load_summaries_cache():
    try:
        with open(SUMMARIES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_summaries_cache(cache):
    with open(SUMMARIES_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def get_pacific_date_str():
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
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt_text}]
    )
    return message.content[0].text.strip()

def generate_summaries(data):
    """
    Generate AI summaries for each category + the Bottom Line.
    Runs once per calendar day (Pacific time). Cached in summaries_cache.json.

    SUMMARY ARCHITECTURE:
    - Front Page card summaries: 3 sentences max, 13 words per sentence max.
      Mood and direction of the category. Scannable in 5 seconds.
    - Category page long summaries: 3 sentences max, 20 words per sentence.
      Three-part structure: where are we / what is driving it / what to watch.
    - Bottom Line: 2-3 sentences, 20 words per sentence. Cross-category synthesis.
      The single most important thing an industrially-minded person needs to know today.

    VOICE: Authoritative, confident, specific. Write like the most informed
    person in the room who has read everything. Short declarative sentences.
    No hedging. No subordinate clauses. No compound thoughts crammed together.

    ARTICLE SUMMARIES: Zero inference. Wire service standard. Summaries used as
    context for category summaries report only what sources state.

    JLL MARKET DATA (if loaded): Use only as supporting evidence when current
    news genuinely warrants a sourced market observation. Never force a connection.
    Never use to show sophistication. Let the data speak only when it must.
    """
    print("📝 Checking summaries cache...")

    today = get_pacific_date_str()
    cache = load_summaries_cache()

    if cache.get('date') == today and cache.get('summaries'):
        print(f"   ✅ Summaries already generated for {today}, using cache")
        return cache['summaries']

    print(f"   Generating fresh summaries for {today}...")

    section_titles = {
        'economy':    'Economy',
        'industries': 'Industries',
        'logistics':  'Logistics',
        'policy':     'Policy',
        'socal':      'SoCal',
    }

    categories = {k: [] for k in section_titles}
    for article in data['articles']:
        cat = article.get('category', 'industries')
        # Normalize legacy keys
        legacy_map = {
            'economics': 'economy', 'business': 'industries', 'tech': 'industries',
            'supply-chain': 'logistics', 'politics': 'policy', 'local-deals': 'socal',
        }
        cat = legacy_map.get(cat, cat)
        if cat in categories:
            categories[cat].append(article)

    summaries = {}

    # ── Per-category summaries ────────────────────────────────
    for cat_key, cat_title in section_titles.items():
        articles = categories[cat_key]
        if not articles:
            summaries[cat_key] = None
            summaries[f"{cat_key}_long"] = None
            print(f"   ⏭️  {cat_title}: no articles, skipping")
            continue

        article_context = "\n\n".join([
            f"Headline: {a['headline']}\nSource: {a['source']}\nDate: {a['date']}\nSummary: {a['summary']}"
            for a in articles
        ])

        # ── Front Page card summary (short) ───────────────────
        if cat_key == 'socal':
            short_prompt = f"""You are writing the Front Page summary card for the SoCal section of the SoCal Industrial Journal — a professional intelligence publication for Southern California industrial real estate.

Below are the SoCal industrial articles from the past 72 hours:

{article_context}

Write a summary of current conditions in Southern California industrial real estate.

STRICT FORMAT RULES:
- Maximum 3 sentences
- Maximum 13 words per sentence
- Short, declarative statements only
- No subordinate clauses, no hedging language, no compound thoughts
- Each sentence must stand alone and be immediately clear

CONTENT RULES:
- Capture the mood and direction of the SoCal industrial market right now
- Broad enough to represent the whole market, not just one deal
- Specific enough to feel genuinely informed
- Do NOT draw market connections or make inferences beyond what the articles report
- Do NOT speculate, predict, or advise
- Save deal-specific details for the category page

Write only the summary. No preamble."""

        elif cat_key == 'economy':
            short_prompt = f"""You are writing the Front Page summary card for the Economy section of the SoCal Industrial Journal — a professional intelligence publication for Southern California industrial real estate.

Below are the Economy articles from the past 72 hours:

{article_context}

Write a summary of current macroeconomic conditions as they relate to industrial business, capital, and operations.

STRICT FORMAT RULES:
- Maximum 3 sentences
- Maximum 13 words per sentence
- Short, declarative statements only
- No subordinate clauses, no hedging language, no compound thoughts
- Each sentence must stand alone and be immediately clear

CONTENT RULES:
- Capture the macro mood and direction — rates, capital, economic conditions
- Broad enough to represent the whole category, not just one story
- Specific enough to feel genuinely informed
- Do NOT draw market connections or make inferences beyond what articles report
- Do NOT speculate, predict, or advise
- Save specific data points for the category page

Write only the summary. No preamble."""

        else:
            short_prompt = f"""You are writing the Front Page summary card for the {cat_title} section of the SoCal Industrial Journal — a professional intelligence publication for Southern California industrial real estate.

Below are the {cat_title} articles from the past 72 hours:

{article_context}

Write a summary of current conditions in {cat_title} as they relate to industrial real estate, tenants, and operations.

STRICT FORMAT RULES:
- Maximum 3 sentences
- Maximum 13 words per sentence
- Short, declarative statements only
- No subordinate clauses, no hedging language, no compound thoughts
- Each sentence must stand alone and be immediately clear

CONTENT RULES:
- Capture the mood and direction of {cat_title} right now
- Broad enough to represent the whole category, not just one story
- Specific enough to feel genuinely informed
- Do NOT draw market connections or make inferences beyond what articles report
- Do NOT speculate, predict, or advise
- Save specific details for the category page

Write only the summary. No preamble."""

        try:
            summary_text = call_claude_for_summary(short_prompt)
            summaries[cat_key] = summary_text
            print(f"   ✅ {cat_title}: front page summary generated")
        except Exception as e:
            print(f"   ⚠️  {cat_title}: front page summary failed ({e})")
            summaries[cat_key] = None

        # ── Category page long summary ─────────────────────────
        if cat_key == 'socal':
            long_prompt = f"""You are writing the editorial summary banner for the SoCal page of the SoCal Industrial Journal — a professional intelligence publication for Southern California industrial real estate.

Below are the SoCal industrial articles from the past 72 hours:

{article_context}

Write a 3-sentence editorial summary of the SoCal industrial market right now.

STRICT FORMAT RULES:
- Exactly 3 sentences
- Maximum 20 words per sentence
- Short, declarative statements only
- No subordinate clauses, no hedging language

THREE-PART STRUCTURE — one sentence each:
1. WHERE ARE WE: The current state of the SoCal industrial market in one clear statement
2. WHAT IS DRIVING IT: The dominant force — supply, demand, capital, or regulatory — shaping conditions
3. WHAT TO WATCH: The most important trend or development to monitor near term

CONTENT RULES:
- More specific and substantive than the Front Page summary
- Can reference specific submarkets, trends, or conditions
- Do NOT invent market connections beyond what the articles report
- Do NOT speculate or predict — observe and describe only
- Authoritative and direct

Write only the summary. No preamble."""

        elif cat_key == 'economy':
            long_prompt = f"""You are writing the editorial summary banner for the Economy page of the SoCal Industrial Journal — a professional intelligence publication for Southern California industrial real estate.

Below are the Economy articles from the past 72 hours:

{article_context}

Write a 3-sentence editorial summary of current macroeconomic conditions.

STRICT FORMAT RULES:
- Exactly 3 sentences
- Maximum 20 words per sentence
- Short, declarative statements only
- No subordinate clauses, no hedging language

THREE-PART STRUCTURE — one sentence each:
1. WHERE ARE WE: The current macro environment in one clear establishing statement
2. WHAT IS DRIVING IT: The dominant force — rates, trade, credit, growth signals — behind current conditions
3. WHAT TO WATCH: The most important upcoming indicator, decision, or development to monitor

CONTENT RULES:
- More specific and substantive than the Front Page summary
- Can reference specific rates, indicators, or economic conditions
- Do NOT draw market connections beyond what articles report
- Do NOT speculate or predict — observe and describe only
- Authoritative and direct

Write only the summary. No preamble."""

        else:
            long_prompt = f"""You are writing the editorial summary banner for the {cat_title} page of the SoCal Industrial Journal — a professional intelligence publication for Southern California industrial real estate.

Below are the {cat_title} articles from the past 72 hours:

{article_context}

Write a 3-sentence editorial summary of current conditions in {cat_title}.

STRICT FORMAT RULES:
- Exactly 3 sentences
- Maximum 20 words per sentence
- Short, declarative statements only
- No subordinate clauses, no hedging language

THREE-PART STRUCTURE — one sentence each:
1. WHERE ARE WE: The current state of {cat_title} in one clear establishing statement
2. WHAT IS DRIVING IT: The dominant force or forces shaping current conditions
3. WHAT TO WATCH: The most important trend, development, or decision to monitor near term

CONTENT RULES:
- More specific and substantive than the Front Page summary
- Can reference specific companies, trends, or conditions from the articles
- Do NOT draw market connections beyond what articles report
- Do NOT speculate or predict — observe and describe only
- Authoritative and direct

Write only the summary. No preamble."""

        try:
            long_summary_text = call_claude_for_summary(long_prompt)
            summaries[f"{cat_key}_long"] = long_summary_text
            print(f"   ✅ {cat_title}: category page summary generated")
        except Exception as e:
            print(f"   ⚠️  {cat_title}: category page summary failed ({e})")
            summaries[f"{cat_key}_long"] = None

    # ── Bottom Line ───────────────────────────────────────────
    # Build context from all category summaries
    all_summaries_context = "\n\n".join([
        f"{section_titles[k]}:\n{v}"
        for k, v in summaries.items()
        if v is not None and k in section_titles
    ])

    # Also include raw article headlines across all categories for fuller context
    all_headlines = "\n".join([
        f"[{a.get('category','').upper()}] {a['headline']}"
        for a in data['articles']
        if not a.get('is_overflow')
    ])

    if all_summaries_context:
        bottom_line_prompt = f"""You are writing the Bottom Line — the lead editorial statement of the SoCal Industrial Journal, a professional intelligence publication for Southern California industrial real estate.

The Bottom Line appears at the top of the Front Page above all category cards. It is the first thing every reader sees. It answers the question: "What does an industrially-minded person most need to understand about the world right now?"

CATEGORY SUMMARIES FROM TODAY:
{all_summaries_context}

ARTICLE HEADLINES FROM TODAY:
{all_headlines}

Write the Bottom Line.

STRICT FORMAT RULES:
- 2-3 sentences maximum
- Maximum 20 words per sentence
- Short, declarative statements only
- No subordinate clauses, no hedging language, no compound thoughts

CONTENT RULES — CRITICAL:
- Synthesize ACROSS all five categories — never drawn from just one
- Find the thread that connects the categories, not a list of separate signals
- Capture the single most important thing shaping the industrial business environment today
- Draw only from what the articles and summaries above are reporting
- NEVER predict — always observe what is already happening
- NEVER invent market connections beyond what the reporting supports
- Authoritative and confident — not cautious or hedged
- The industrially-minded reader should finish this and feel immediately oriented

WRONG (a list of separate signals):
"Freight rates are rising, the Fed held rates, and IE vacancy is climbing."

RIGHT (a synthesized observation):
"The industrial economy is navigating a simultaneous reset in capital costs, tenant demand, and supply. Conditions are shifting faster than most market participants expected."

Write only the Bottom Line. No preamble."""

        try:
            bottom_line = call_claude_for_summary(bottom_line_prompt)
            summaries['bottom_line'] = bottom_line
            print(f"   ✅ Bottom Line generated")
        except Exception as e:
            print(f"   ⚠️  Bottom Line failed ({e})")
            summaries['bottom_line'] = None
    else:
        summaries['bottom_line'] = None

    cache = {'date': today, 'summaries': summaries}
    save_summaries_cache(cache)
    print(f"   💾 Summaries cached for {today}")

    return summaries

# ─────────────────────────────────────────────────────────────
# HTML GENERATION
# ─────────────────────────────────────────────────────────────

def generate_html(data, summaries, display_items=None):
    """Generate warm premium magazine Front Page and category pages"""

    if display_items is None:
        display_items = [dict(a) for a in data['articles']]

    # ── Design tokens ─────────────────────────────────────────
    CREAM       = '#FAF7F2'
    PARCHMENT   = '#F0EBE1'
    INK         = '#1C1917'
    INK_LIGHT   = '#44403C'
    RULE        = '#D6CFC4'
    ACCENT      = '#B5451B'
    ACCENT_WARM = '#C9622F'
    MUTED       = '#78716C'

    # Five-category palette
    CAT_COLORS = {
        'economy':    '#7C5C3E',   # warm brown
        'industries': '#3D6B5E',   # forest green
        'logistics':  '#4E6B5E',   # teal green
        'policy':     '#8B4A3A',   # brick
        'socal':      '#7A6040',   # saddle
    }

    CAT_ICONS = {
        'economy':    '◈',
        'industries': '◆',
        'logistics':  '◍',
        'policy':     '◐',
        'socal':      '◑',
    }

    FONTS = "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Serif+Display:ital@0;1&family=Jost:wght@300;400;500;600&display=swap"

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
            font-size: 1.15rem;
            font-weight: 400;
            line-height: 1.7;
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

        /* ── Section labels ── */
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
        .all-stories-divider {{
            margin: 2.5rem 0 1.5rem;
        }}

        /* ── Cross-category tags ── */
        .cross-cat-wrap {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-top: 0.75rem;
        }}
        .cross-cat-tag {{
            font-family: 'Jost', sans-serif;
            font-size: 0.6rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--muted);
            border: 1px solid var(--rule);
            padding: 0.15rem 0.45rem;
            border-radius: 2px;
            text-decoration: none;
            transition: color 0.15s, border-color 0.15s;
        }}
        .cross-cat-tag:hover {{
            color: var(--ink);
            border-color: var(--ink-light);
        }}
        .cross-cat-label {{
            font-family: 'Jost', sans-serif;
            font-size: 0.6rem;
            color: var(--muted);
            letter-spacing: 0.06em;
            align-self: center;
        }}

        /* ── Overflow indicator (SoCal tab) ── */
        .overflow-badge {{
            font-family: 'Jost', sans-serif;
            font-size: 0.58rem;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            border: 1px dashed var(--rule);
            padding: 0.12rem 0.4rem;
            border-radius: 2px;
            margin-left: 0.4rem;
        }}

        /* ── Submarket filter bar ── */
        .submarket-bar {{
            background: var(--parchment);
            border-bottom: 1px solid var(--rule);
            padding: 0.75rem 2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        .submarket-label {{
            font-family: 'Jost', sans-serif;
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--muted);
            margin-right: 0.5rem;
        }}
        .submarket-btn {{
            font-family: 'Jost', sans-serif;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.06em;
            color: var(--ink-light);
            background: #fff;
            border: 1px solid var(--rule);
            padding: 0.35rem 0.85rem;
            border-radius: 2px;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .submarket-btn:hover {{
            border-color: var(--cat-color, var(--accent));
            color: var(--cat-color, var(--accent));
        }}
        .submarket-btn.active {{
            background: var(--cat-color, var(--accent));
            border-color: var(--cat-color, var(--accent));
            color: #fff;
        }}
        .submarket-count {{
            font-size: 0.6rem;
            opacity: 0.75;
            margin-left: 0.2rem;
        }}
        .sm-hidden {{ display: none !important; }}

        /* ── Cluster cards ── */
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

    # ── Category structure ─────────────────────────────────────
    section_titles = {
        'economy':    'Economy',
        'industries': 'Industries',
        'logistics':  'Logistics',
        'policy':     'Policy',
        'socal':      'SoCal',
    }

    # Nav order: Front Page first, then categories
    nav_order = ['economy', 'industries', 'logistics', 'policy', 'socal']

    categories = {k: [] for k in section_titles}
    for item in display_items:
        cat = item.get('category', 'industries')
        # Normalize legacy keys
        legacy_map = {
            'economics': 'economy', 'business': 'industries', 'tech': 'industries',
            'supply-chain': 'logistics', 'politics': 'policy', 'local-deals': 'socal',
        }
        cat = legacy_map.get(cat, cat)
        if cat in categories:
            categories[cat].append(item)

    def parse_date(item):
        try:
            return datetime.strptime(item.get('date', ''), "%B %d, %Y")
        except:
            return datetime(2000, 1, 1)

    def importance_score(item):
        if item.get('is_cluster'):
            best = max(item['articles'], key=lambda a: _base_score(a))
            bonus = (item['source_count'] - 1) * 5
            return _base_score(best) + bonus
        return _base_score(item)

    def _base_score(article):
        score = 0
        headline = article.get('headline', '').lower()
        source = article.get('source', '').lower()

        # Source quality tiers
        if source in ['wall street journal', 'bloomberg', 'wsj', 'reuters']:
            score += 50
        elif source in ['green street', 'costar', 'los angeles times', 'los angeles business journal']:
            score += 30
        elif source in ['supply chain dive', 'freightwaves', 'journal of commerce',
                        'the real deal', 'commercial observer', 'politico']:
            score += 25
        elif source in ['calmatters', 'industry week', 'modern materials handling',
                        'food logistics', 'dc velocity', 'pacific maritime magazine', 'propmodo']:
            score += 20
        elif source in ['daily bulletin', 'los angeles daily news', 'press-telegram',
                        'san gabriel valley tribune', 'whittier daily news', 'the sun',
                        'the press-enterprise', 'redlands daily facts', 'pasadena star-news',
                        'orange county register', 'daily breeze', 'san diego union-tribune',
                        'san diego business journal', 'ie business daily']:
            score += 25
        else:
            score += 10

        # Keyword bonuses
        for kw in ['breaking', 'exclusive', 'major', 'unprecedented', 'historic', 'largest', 'biggest', 'first-ever']:
            if kw in headline:
                score += 30
                break
        for kw in ['bankruptcy', 'bankrupt', 'collapse', 'acquisition', 'acquires', 'merger',
                   'layoff', 'lays off', 'closes', 'shuts down', 'billion', 'million sf', 'record']:
            if kw in headline:
                score += 20
                break
        for kw in ['fed ', 'federal reserve', 'interest rate', 'recession', 'inflation', 'gdp', 'tariff', 'regulation']:
            if kw in headline:
                score += 15
                break
        for kw in ['inland empire', 'riverside', 'san bernardino', 'ontario', 'fontana',
                   'moreno valley', 'los angeles', 'orange county', 'san diego']:
            if kw in headline:
                score += 25
                break

        # Recency bonus
        try:
            days_old = (datetime.now() - parse_date(article)).days
            score += 15 if days_old == 0 else (10 if days_old == 1 else (5 if days_old == 2 else 0))
        except:
            pass

        return score

    for cat in categories:
        categories[cat].sort(key=parse_date, reverse=True)

    # ── Pacific time ──────────────────────────────────────────
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
    current_date = pacific_now.strftime('%A, %B %d, %Y')
    total_articles = len(data['articles'])

    last_update_time = data.get('last_updated', datetime.utcnow().isoformat() + "Z")
    last_update_dt = datetime.fromisoformat(last_update_time.replace('Z', '+00:00'))
    minutes_ago = int((datetime.now(timezone.utc) - last_update_dt).total_seconds() / 60)
    time_ago = f"{minutes_ago}m ago" if minutes_ago < 60 else f"{minutes_ago // 60}h ago"

    # ── Shared header ─────────────────────────────────────────
    def generate_header(active_page='home'):
        nav_items = []
        for cat_key in nav_order:
            cat_title = section_titles[cat_key]
            is_active = active_page == cat_key
            style = 'color:#fff; border-bottom-color:var(--accent);' if is_active else ''
            nav_items.append(
                f'<a href="{cat_key}.html" style="{style}" class="site-nav-link">{cat_title}</a>'
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
        bottom_line_text = (summaries or {}).get('bottom_line')
        if bottom_line_text:
            bottom_line_html = f'''<div class="bottom-line">
  <div class="bottom-line-label">The Bottom Line</div>
  <p class="bottom-line-text">{bottom_line_text}</p>
</div>'''
        else:
            bottom_line_html = ''

        cards_html = ''
        empty_cats = []
        active_count = 0

        for cat_key in nav_order:
            cat_title = section_titles[cat_key]
            arts = categories[cat_key]
            count = len(arts)
            color = CAT_COLORS[cat_key]
            icon = CAT_ICONS[cat_key]

            if count == 0:
                empty_cats.append(cat_title)
                continue

            active_count += 1
            ai_summary = (summaries or {}).get(cat_key)
            if not ai_summary:
                ai_summary = arts[0].get('summary', '')[:220] + '…'

            cards_html += f'''<a href="{cat_key}.html" class="fp-card" style="--cat-color:{color};">
  <div class="fp-card-label">
    <span>{icon} {cat_title}</span>
    <span class="fp-card-count">{count}</span>
  </div>
  <p class="fp-card-summary">{ai_summary}</p>
  <div class="fp-card-cta">View all stories →</div>
</a>
'''

        empty_notice = ''
        if empty_cats:
            joined = ', '.join(empty_cats)
            empty_notice = f'<p style="font-family:\'Jost\',sans-serif;font-size:0.8rem;color:var(--muted);text-align:center;margin:2rem 0;">{joined} {"has" if len(empty_cats) == 1 else "have"} no stories yet — check back soon.</p>'

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
        arts = categories[cat_key]
        color = CAT_COLORS[cat_key]
        icon = CAT_ICONS[cat_key]
        count = len(arts)

        if count == 0:
            body_html = f'<div style="grid-column:1/-1;text-align:center;padding:3rem;background:var(--parchment);border:1px solid var(--rule);font-family:\'Cormorant Garamond\',Georgia,serif;font-size:1.1rem;color:var(--muted);">No stories in this category yet — check back soon.</div>'
        else:
            long_summary = (summaries or {}).get(f"{cat_key}_long")
            if long_summary:
                summary_banner = f'''<div class="cat-summary-banner" style="--cat-color:{color};">
  <p class="cat-summary-text">{long_summary}</p>
</div>'''
            else:
                summary_banner = ''

            scored = sorted(arts, key=importance_score, reverse=True)
            top_arts = scored[:3]
            rest_arts = scored[3:]

            def get_item_submarkets(item):
                if item.get('is_cluster'):
                    sm = set()
                    for a in item['articles']:
                        for s in a.get('submarkets', ['all']):
                            sm.add(s)
                    return list(sm) if sm else ['all']
                return item.get('submarkets', ['all'])

            def sm_attr(item):
                if cat_key != 'socal':
                    return ''
                sms = get_item_submarkets(item)
                return f' data-submarket="{" ".join(sms)}"'

            def make_cluster_sources_html(cluster_item):
                links = []
                for a in cluster_item['articles']:
                    is_pw = a.get('source_type', 'free') == 'paywalled'
                    lock = ' 🔒' if is_pw else ''
                    links.append(
                        f'<a href="{a["url"]}" target="_blank" class="cluster-source-link">'
                        f'{a["source"]}{lock}</a>'
                    )
                sep = '<span class="cluster-source-sep">·</span>'
                c = cluster_item['source_count']
                return (
                    f'<div class="cluster-sources">'
                    f'<span class="cluster-sources-label">Coverage</span>'
                    f'{sep.join(links)}'
                    f'<span class="cluster-badge">{c} sources</span>'
                    f'</div>'
                )

            def make_card(item, is_top=False):
                is_cluster = item.get('is_cluster', False)
                attr = sm_attr(item)

                if is_cluster:
                    headline = item['cluster_headline'] or item['articles'][0]['headline']
                    summary = item['cluster_summary'] or item['articles'][0]['summary']
                    date_str = item['date']
                    sources_html = make_cluster_sources_html(item)
                    top_badge = '<span class="top-badge">Top Story</span>' if is_top else ''
                    h_class = 'top-article-headline' if is_top else 'article-headline'
                    card_class = 'top-article-card' if is_top else 'article-card'
                    return f'''<div class="{card_class}"{attr} style="--cat-color:{color};">
  {top_badge}
  <div class="article-meta">
    <span class="date">{date_str}</span>
  </div>
  <h3 class="{h_class}">{headline}</h3>
  <p class="article-summary">{summary}</p>
  {sources_html}
</div>'''

                # Solo article
                is_paywalled = item.get('source_type', 'free') == 'paywalled'
                is_overflow = item.get('is_overflow', False)
                paywall = '<span class="paywall-badge">🔒 Subscriber</span>' if is_paywalled else ''

                # Overflow badge — show source category
                overflow_cat_titles = {
                    'economy': 'Economy', 'industries': 'Industries',
                    'logistics': 'Logistics', 'policy': 'Policy',
                }
                overflow_badge = f'<span class="overflow-badge">via {overflow_cat_titles.get(item.get("overflow_from", ""), "")}</span>' if is_overflow else ''

                article_url_encoded = item["url"].replace("&", "%26")
                subject = f'Article%20Request%3A%20{item["headline"][:60].replace(" ", "%20")}'
                body_enc = f'Hi%20Brendan%2C%0A%0AI%20would%20like%20more%20information%20on%20the%20following%20article%3A%0A%0A{item["headline"]}%0A{article_url_encoded}%0A%0AThanks'
                access = f'&nbsp;&nbsp;<a href="mailto:{YOUR_EMAIL}?subject={subject}&body={body_enc}" style="font-family:\'Jost\',sans-serif;font-size:0.72rem;font-weight:500;color:var(--accent);text-decoration:none;letter-spacing:0.05em;">Request more info →</a>' if is_paywalled else ''

                # Cross-category tags (not on overflow cards)
                cross_cats = item.get('secondary_categories', []) if not is_overflow else []
                if cross_cats:
                    tag_links = ''.join(
                        f'<a href="{c}.html" class="cross-cat-tag">{section_titles.get(c, c)}</a>'
                        for c in cross_cats
                        if c in section_titles
                    )
                    cross_cat_html = f'<div class="cross-cat-wrap"><span class="cross-cat-label">Also in</span>{tag_links}</div>'
                else:
                    cross_cat_html = ''

                if is_top:
                    return f'''<div class="top-article-card"{attr} style="--cat-color:{color};">
  <span class="top-badge">Top Story</span>
  <div class="article-meta">
    <span>{item["source"]}</span>
    <span class="date">· {item["date"]}</span>
    {paywall}{overflow_badge}
  </div>
  <h3 class="top-article-headline">{item["headline"]}</h3>
  <p class="article-summary">{item["summary"]}</p>
  <div>
    <a href="{item["url"]}" target="_blank" class="article-read">Read full story</a>{access}
  </div>
  {cross_cat_html}
</div>'''
                else:
                    return f'''<div class="article-card"{attr} style="--cat-color:{color};">
  <div class="article-meta">
    <span>{item["source"]}</span>
    <span class="date">· {item["date"]}</span>
    {paywall}{overflow_badge}
  </div>
  <h3 class="article-headline">{item["headline"]}</h3>
  <p class="article-summary">{item["summary"]}</p>
  <div>
    <a href="{item["url"]}" target="_blank" class="article-read">Read full story</a>{access}
  </div>
  {cross_cat_html}
</div>'''

            top_cards_html = '\n'.join(make_card(a, is_top=True) for a in top_arts)
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

        # ── Submarket filter bar (SoCal only) ─────────────────
        submarket_bar_html = ''
        submarket_js = ''
        if cat_key == 'socal' and count > 0:
            sm_counts = {'inland-empire': 0, 'los-angeles': 0, 'orange-county': 0, 'san-diego': 0}
            for item in arts:
                sms = get_item_submarkets(item) if item.get('is_cluster') else item.get('submarkets', ['all'])
                for sm in sms:
                    if sm in sm_counts:
                        sm_counts[sm] += 1

            sm_labels = {
                'inland-empire': 'Inland Empire',
                'los-angeles': 'Los Angeles',
                'orange-county': 'Orange County',
                'san-diego': 'San Diego',
            }

            btn_html = f'<button class="submarket-btn active" data-sm="all" onclick="filterSM(this)" style="--cat-color:{color};">All <span class="submarket-count">({count})</span></button>'
            for sm_key, sm_label in sm_labels.items():
                c = sm_counts[sm_key]
                if c > 0:
                    btn_html += f'<button class="submarket-btn" data-sm="{sm_key}" onclick="filterSM(this)" style="--cat-color:{color};">{sm_label} <span class="submarket-count">({c})</span></button>'

            submarket_bar_html = f'''<div class="submarket-bar" style="--cat-color:{color};">
  <span class="submarket-label">Filter by submarket</span>
  {btn_html}
</div>'''

            submarket_js = '''<script>
function filterSM(btn) {
  document.querySelectorAll('.submarket-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const sm = btn.dataset.sm;
  const cards = document.querySelectorAll('[data-submarket]');
  cards.forEach(card => {
    if (sm === 'all') {
      card.classList.remove('sm-hidden');
    } else {
      const cardSMs = card.dataset.submarket.split(' ');
      if (cardSMs.includes(sm) || cardSMs.includes('all')) {
        card.classList.remove('sm-hidden');
      } else {
        card.classList.add('sm-hidden');
      }
    }
  });
  document.querySelectorAll('.article-grid, .fp-grid').forEach(grid => {
    const visible = [...grid.querySelectorAll('[data-submarket]')]
      .filter(c => !c.classList.contains('sm-hidden'));
    const label = grid.previousElementSibling;
    if (label && label.classList.contains('section-label')) {
      label.style.display = visible.length ? '' : 'none';
    }
    grid.style.display = visible.length ? '' : 'none';
  });
}
</script>'''

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
{submarket_bar_html}

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

{submarket_js}
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
    .src-rows {{ padding: 0.5rem 0; }}
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
    <p class="page-count">{total} publications across 6 tiers</p>
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

    print("✅ Generated 7 HTML pages (1 Front Page + 5 category pages + 1 Source Directory)")
    return homepage

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    data = load_articles()
    data = remove_old_articles(data)

    # ── Tier 1: RSS harvest (Cloudflare Worker output) ────────
    print("\n📥 RSS Tier")
    rss_raw = load_rss_harvest()
    rss_articles = []
    if rss_raw:
        rss_articles = categorize_rss_articles(rss_raw, data['articles'])
        rss_articles = normalize_rss_dates(rss_articles)
        print(f"   RSS tier: {len(rss_articles)} articles ready")
    else:
        print("   RSS tier: 0 articles (harvest not available)")

    # ── Tier 2: Web search (wire services + catch-all) ────────
    print("\n🌐 Web Search Tier")
    web_articles = search_new_articles(data['articles'])

    # ── Merge both tiers ──────────────────────────────────────
    print(f"\n🔀 Merging tiers: {len(rss_articles)} RSS + {len(web_articles)} web search")
    all_new = rss_articles + web_articles

    # Cross-tier deduplication by URL and headline
    seen_urls = set()
    seen_headlines = set()
    merged = []
    for art in all_new:
        u = art.get('url', '').strip()
        h = art.get('headline', '').lower().strip()
        if (u and u in seen_urls) or h in seen_headlines:
            continue
        seen_urls.add(u)
        seen_headlines.add(h)
        merged.append(art)

    cross_dupes = len(all_new) - len(merged)
    if cross_dupes:
        print(f"   Removed {cross_dupes} cross-tier duplicates")
    print(f"   {len(merged)} unique articles entering database pipeline")

    data, added_count = add_new_articles(data, merged)
    save_articles(data)

    summaries = generate_summaries(data)

    # ── Clustering ────────────────────────────────────────────
    cluster_synth_cache = {}
    try:
        with open('cluster_cache.json', 'r') as f:
            cluster_synth_cache = json.load(f)
    except FileNotFoundError:
        pass

    display_items = cluster_articles(data['articles'])

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

    print("🎨 Generating HTML...")
    generate_html(data, summaries, display_items)

    from datetime import timezone
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print(f"   Total articles in database: {len(data['articles'])}")
    print(f"   New this run: {added_count}")
    print(f"   └─ From RSS tier: {len(rss_articles)}")
    print(f"   └─ From web search tier: {len(web_articles)}")
    clusters = [d for d in display_items if d.get('is_cluster')]
    print(f"   Clusters formed: {len(clusters)}")
    print(f"   Next update: In 2 hours")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
