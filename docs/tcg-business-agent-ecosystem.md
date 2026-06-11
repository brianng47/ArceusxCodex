# TCG Business Agent Ecosystem

## Purpose

This document defines the target specialist ecosystem for a TCG business built
around content creation, online sales, daily market awareness, and personal
upskilling.

The important design decision: Brian should not need to manually ask Arceus to
"build an agent" every time. In the mature system, Brian gives Arceus a business
ask, and Arceus decides which skills, adapters, agents, and workflows are needed
to complete it.

## Source Signals

Research signals used for this blueprint:

- TCGplayer has a REST API using bearer-token requests and exposes catalog data,
  including Pokemon as a category.
- eBay's Inventory API models inventory items, offers, inventory locations, and
  published listings; eBay also notes that API-created listings should be
  managed through the API rather than edited manually in Seller Hub.
- Shopify's REST Admin API is now legacy for new public apps; new Shopify app
  work should prefer the GraphQL Admin API path.
- YouTube Data API covers videos, channels, playlists, comments, captions, and
  other channel resources. YouTube Analytics and Reporting APIs support custom
  dashboards and reporting automation.
- Google Analytics Data API supports custom dashboards, reporting automation,
  and integrations with business applications.
- Google Ads API supports campaign, asset, reporting, recommendation, and
  shopping-related work, but mutations should stay approval-gated.

## Operating Model

Arceus should treat each user request as an intent-routing problem:

1. Understand the business objective.
2. Classify the request:
   - conversation;
   - memory capture;
   - research;
   - content creation;
   - listing or inventory work;
   - analytics;
   - agent or workflow creation;
   - external action requiring approval.
3. Select existing components.
4. If a needed component does not exist, draft the missing component spec.
5. Ask for approval only when required by risk.
6. Execute locally through Codex or a specialist runtime.
7. Record result, files changed, decisions, metrics, and next actions.

This means "agent creation" is not a separate user burden. It is a system
behavior triggered when Arceus discovers a missing capability.

## Skill Library

Skills are reusable operating procedures. They are lighter than agents and
should be created before adding a new specialist.

### Business Strategy Skills

- TCG product positioning.
- Offer construction: singles, sealed, slabs, bundles, mystery packs, starter
  bundles, collection lots.
- Margin math and unit economics.
- Pricing thesis writing.
- Launch planning.
- Competitive teardown.
- Promotion calendar planning.
- Customer segment definition.
- Risk review for hype-driven inventory.

### TCG Domain Skills

- Card identification and normalization.
- Set, rarity, condition, language, and variant classification.
- Grading candidate assessment.
- Market price comparison.
- Buylist versus marketplace decisioning.
- Sealed product expected value estimation.
- Rotation, meta, banlist, and demand-event tracking.
- Collection intake workflow.

### Content Skills

- Short-form hook writing.
- TCG story mining: pulls, chase cards, nostalgia, meta relevance, collector
  psychology.
- Video scriptwriting.
- Live selling run-of-show planning.
- Product photography shot lists.
- Thumbnail and title ideation.
- UGC brief writing.
- Repurposing long content into shorts, posts, email, and listings.
- Brand voice enforcement.

### Commerce Skills

- Listing copywriting.
- SEO title construction.
- Condition note writing.
- SKU naming rules.
- Inventory intake checklist.
- Order issue triage.
- Customer response drafting.
- Return/refund decision support.
- Fraud and suspicious-order review.

### Analytics Skills

- Daily KPI readout.
- Funnel analysis.
- Content performance diagnosis.
- Product performance diagnosis.
- Inventory aging analysis.
- Sell-through and repricing rules.
- Campaign performance summary.
- Cash conversion cycle tracking.

### Personal Upskilling Skills

- Daily learning brief.
- Skill gap diagnosis.
- Reading list synthesis.
- Practice task generation.
- Reflection capture.
- Weekly review.
- Decision journal update.
- Mental model library maintenance.

## Tool Adapters

Tool adapters are deterministic integrations. They should be built with narrow
permissions and explicit approval gates.

### Core Internal Adapters

- Arceus memory adapter:
  - Postgres now;
  - Notion and Obsidian later.
- File/project adapter:
  - read project files;
  - propose writes;
  - apply approved changes.
- Codex runtime adapter:
  - run handoffs;
  - capture result;
  - record memory.
- Dashboard adapter:
  - show plans;
  - show risk;
  - collect approvals;
  - display results.

### TCG Data Adapters

- TCGplayer adapter:
  - catalog lookup;
  - product normalization;
  - price lookup;
  - category/set metadata.
- eBay adapter:
  - inventory items;
  - offers;
  - published listings;
  - order and fulfillment sync.
- Shopify adapter:
  - products;
  - variants;
  - inventory;
  - orders;
  - customers;
  - discounts.
- Marketplace export adapter:
  - CSV import/export for platforms without stable APIs.
- Grading tracker adapter:
  - PSA/BGS/CGC submission tracker, initially manual or spreadsheet-based.

### Content and Social Adapters

- YouTube Data adapter:
  - video metadata;
  - channel data;
  - playlists;
  - comments.
- YouTube Analytics adapter:
  - video and channel performance.
- TikTok/Instagram adapter:
  - start with manual exports or approved APIs;
  - publishing should remain approval-gated.
- Canva adapter:
  - thumbnails;
  - product cards;
  - social templates.
- Remotion adapter:
  - repeatable video generation.
- Image/video generation adapters:
  - product-safe creative variants;
  - thumbnails;
  - ad creatives;
  - UGC concepts.

### Marketing and Analytics Adapters

- Google Analytics adapter:
  - traffic;
  - ecommerce;
  - channel performance.
- Google Ads adapter:
  - read campaigns and recommendations first;
  - create or mutate campaigns only with approval.
- Meta Ads adapter:
  - read performance first;
  - mutate only with approval.
- Email/SMS adapter:
  - draft campaigns;
  - segment customers;
  - send only after approval.

### Operations Adapters

- Spreadsheet adapter:
  - inventory models;
  - buying sheets;
  - repricing exports.
- Notion adapter:
  - business wiki;
  - agent specs;
  - decisions;
  - content calendar.
- Gmail adapter:
  - supplier emails;
  - customer escalations;
  - partnership outreach.
- Shipping adapter:
  - labels, tracking, and exception handling later.

## Specialist Agents

Agents own recurring judgment-heavy functions. Each agent should have a clear
permission profile, memory scope, and test tasks.

### Arceus Brain

Owns:

- intent routing;
- missing capability detection;
- task decomposition;
- approval discipline;
- memory updates;
- final synthesis.

Should not:

- publish externally without approval;
- mutate financial or ad systems without approval;
- silently create unbounded agent chains.

### TCG Market Analyst

Owns:

- market trend briefs;
- chase card monitoring;
- sealed product watchlists;
- price movement explanations;
- buy/sell/hold hypotheses.

Inputs:

- TCGplayer;
- eBay sold/listed data where available;
- marketplace exports;
- social/content trend signals.

Outputs:

- daily opportunity list;
- risk notes;
- suggested buys;
- repricing recommendations.

### Inventory and Pricing Agent

Owns:

- SKU hygiene;
- condition notes;
- price bands;
- inventory aging;
- repricing proposals;
- dead-stock identification.

Approval:

- can propose prices automatically;
- cannot publish price changes without approval until promoted.

### Listing Agent

Owns:

- listing titles;
- descriptions;
- condition language;
- image requirements;
- category mapping;
- cross-listing preparation.

Outputs:

- Shopify product draft;
- eBay offer draft;
- marketplace CSV rows;
- missing-field checklist.

### Content Strategist Agent

Owns:

- weekly content plan;
- hooks;
- scripts;
- trend mapping;
- repurposing plan.

Works with:

- TCG Market Analyst;
- Creative Director;
- Video Production Agent.

### Creative Director Agent

Owns:

- brand consistency;
- creative concepts;
- thumbnail direction;
- campaign visuals;
- product photography briefs.

Approval:

- can generate mockups;
- cannot publish creative externally without approval.

### Video Production Agent

Owns:

- shorts scripts;
- long-form outlines;
- edit decision lists;
- Remotion templates;
- caption packs.

Outputs:

- script;
- shot list;
- edit plan;
- thumbnail prompt;
- title variants.

### Live Commerce Agent

Owns:

- live stream agenda;
- product run order;
- talking points;
- offer pacing;
- post-live recap.

Useful for:

- TikTok Shop;
- YouTube Live;
- Whatnot-style selling;
- Instagram Live.

### Customer Experience Agent

Owns:

- customer replies;
- order issue triage;
- returns;
- refund recommendations;
- review response drafts.

Approval:

- can draft replies;
- sending remains approval-gated.

### Ads and Growth Agent

Owns:

- campaign briefs;
- creative testing matrix;
- landing page angle;
- budget recommendations;
- performance readouts.

Approval:

- can read performance;
- cannot create, change, or spend ad budget without approval.

### Analytics Agent

Owns:

- KPI dashboard;
- channel attribution;
- content-to-commerce analysis;
- cohort and retention analysis;
- weekly business review.

Outputs:

- what changed;
- why it likely changed;
- what to do next;
- confidence and caveats.

### Supplier and Sourcing Agent

Owns:

- supplier research;
- distributor terms;
- buy opportunity comparisons;
- negotiation drafts;
- purchase risk memo.

Approval:

- cannot purchase or commit funds.

### Compliance and Risk Agent

Owns:

- platform policy checks;
- giveaway rules;
- copyright/trademark risk;
- claim substantiation;
- high-risk action review.

Important:

- This is not legal advice.
- It is a risk filter that should escalate uncertain issues.

### Personal Chief of Staff Agent

Owns:

- daily briefing;
- calendar-aware priorities later;
- learning queue;
- weekly review;
- personal operating system upkeep.

Outputs:

- daily brief;
- recommended focus block;
- skill to practice;
- decision to revisit.

## Workflows

Workflows combine agents and tool adapters to complete outcomes.

### Daily TCG Command Brief

Runs each morning.

Steps:

1. Pull overnight sales, orders, content metrics, and market changes.
2. Identify inventory needing action.
3. Identify content opportunities.
4. Identify personal upskilling recommendation.
5. Present a dashboard briefing with:
   - "what changed";
   - "what matters";
   - "recommended actions";
   - "approval needed".

### New Product Intake

Use when new cards, sealed products, slabs, or lots enter inventory.

Steps:

1. Identify product.
2. Normalize metadata.
3. Estimate market price.
4. Draft SKU and condition notes.
5. Recommend channel:
   - hold;
   - list now;
   - grade;
   - bundle;
   - use as content asset.
6. Create listing drafts after approval.

### Content-to-Commerce Sprint

Use when Brian asks for content that drives sales.

Steps:

1. Market Analyst identifies current product angles.
2. Content Strategist creates hook matrix.
3. Creative Director drafts thumbnail and visual direction.
4. Video Production Agent creates scripts.
5. Listing Agent ensures products are ready.
6. Analytics Agent tracks performance after publishing.

### Weekly Repricing

Steps:

1. Pull current inventory.
2. Pull market references.
3. Find stale inventory and price drift.
4. Produce repricing proposal.
5. Ask approval before publishing.

### Launch Campaign

Steps:

1. Define product/offering.
2. Build landing/listing assets.
3. Build content sequence.
4. Build email/social calendar.
5. Draft ad creatives.
6. Get approval.
7. Publish in controlled sequence.
8. Monitor results.

### Customer Recovery

Use when there are late shipments, unhappy buyers, return issues, or damaged
cards.

Steps:

1. Summarize customer issue.
2. Pull order context.
3. Recommend fair resolution.
4. Draft response.
5. Ask approval before sending or refunding.

### Daily Upskill Brief

Runs daily or on demand.

Inputs:

- current business priorities;
- recent mistakes;
- skills Brian wants;
- saved learning backlog;
- market changes.

Outputs:

- one concept to learn;
- one practical drill;
- one article/video/resource;
- one reflection question;
- one action to apply in the business.

## Dashboard Views Needed

To make this non-terminal-first, the dashboard needs these views:

- Conversation:
  - voice/text input;
  - Arceus response;
  - voice-over state.
- Plan:
  - task decomposition;
  - agents selected;
  - expected output.
- Risk and Approval:
  - risk category;
  - requested permissions;
  - approve/deny/revise by text or voice.
- Execution:
  - running agents;
  - lifecycle states;
  - logs behind "view details".
- Results:
  - files changed;
  - listing drafts;
  - content assets;
  - recommendations;
  - next actions.
- Memory:
  - decision saved;
  - agent improved;
  - business rule updated.
- Agent Ecosystem:
  - active agents;
  - missing capabilities;
  - permission profiles;
  - test tasks.

## Build Order

Do not build all agents first. Build the operating loop first.

Recommended order:

1. Agent component registry:
   - skills;
   - tool adapters;
   - specialist agents;
   - workflows;
   - permissions.
2. Dashboard task planner:
   - show selected components;
   - show missing components;
   - show risk.
3. Approval gate:
   - approve/deny/revise;
   - text first;
   - voice later.
4. First business workflow:
   - Daily TCG Command Brief.
5. First revenue workflow:
   - New Product Intake or Content-to-Commerce Sprint.
6. External integrations:
   - start read-only;
   - promote to write/publish after trust is proven.

## Key Principle

The mature system should feel resourceful because Arceus has a catalog of
capabilities and can assemble them automatically.

That resourcefulness should come from structured components and memory, not
from letting one vague agent improvise across every tool with unlimited power.
