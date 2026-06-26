#!/usr/bin/env python3
"""
Laravel Daily Digest Generator
Cycles through Laravel docs topics in order, one per day.
Writes a markdown digest to laravel-digest/YYYY-MM-DD.md
"""

import datetime
import os
import json

# Laravel 11 docs topics — ordered from foundational to advanced
# Each entry: (topic_slug, display_name, key_concepts)
TOPICS = [
    ("installation", "Installation & Configuration", [
        "Environment files (.env)",
        "APP_KEY, APP_ENV, APP_DEBUG",
        "Config caching: `php artisan config:cache`",
        "Accessing config: `config('app.name')`",
        "Service providers bootstrapping order",
    ]),
    ("routing", "Routing", [
        "Route methods: get, post, put, patch, delete, any, match",
        "Route parameters & constraints: `{id}`, `->where('id', '[0-9]+')`",
        "Named routes: `->name('users.index')`, `route('users.index')`",
        "Route groups: prefix, middleware, namespace",
        "Route model binding: implicit (type-hint) vs explicit (RouteServiceProvider)",
        "Fallback routes: `Route::fallback()`",
        "When to use: routes/web.php vs routes/api.php",
    ]),
    ("middleware", "Middleware", [
        "Global vs route-specific middleware",
        "Middleware groups (web, api)",
        "Middleware parameters: `->middleware('role:admin')`",
        "Terminable middleware (runs after response sent)",
        "Creating: `php artisan make:middleware`",
        "Registering in bootstrap/app.php (Laravel 11)",
        "When to use: auth checks, logging, throttling, CORS",
    ]),
    ("controllers", "Controllers", [
        "Resource controllers: `php artisan make:controller --resource`",
        "Single-action controllers: `__invoke()`",
        "Dependency injection in constructor vs method",
        "Form request injection for validation",
        "When to keep thin: delegate to service/action classes",
        "API controllers: `--api` flag (no create/edit)",
    ]),
    ("requests", "HTTP Requests & Validation", [
        "Accessing input: `$request->input()`, `$request->all()`, `$request->only()`",
        "Form Requests: `php artisan make:request`",
        "`authorize()` method — return true or policy check",
        "`rules()` method — validation rules array",
        "Custom messages: `messages()`, `attributes()`",
        "After hooks: `withValidator()`",
        "When to use Form Request vs inline `$request->validate()`",
    ]),
    ("responses", "Responses & Views", [
        "Response helpers: `response()->json()`, `response()->download()`",
        "Blade templating: `@extends`, `@section`, `@yield`, `@include`",
        "Blade components: `<x-component>`, `php artisan make:component`",
        "View composers & creators",
        "Returning JSON from controllers (API pattern)",
        "Resource responses: `JsonResource`, `ResourceCollection`",
    ]),
    ("eloquent-basics", "Eloquent ORM — Basics", [
        "Model conventions: table name, primary key, timestamps",
        "Mass assignment: `$fillable` vs `$guarded`",
        "CRUD: `create()`, `find()`, `update()`, `delete()`",
        "Query builder on models: `where()`, `orderBy()`, `limit()`",
        "Soft deletes: `SoftDeletes` trait, `withTrashed()`, `restore()`",
        "Scopes: local (`scopeActive()`) vs global (boot method)",
        "When to use: Eloquent vs raw Query Builder vs DB facade",
    ]),
    ("eloquent-relationships", "Eloquent Relationships", [
        "hasOne, hasMany, belongsTo, belongsToMany",
        "hasManyThrough, hasOneThrough",
        "Polymorphic: morphTo, morphMany, morphToMany",
        "Eager loading: `with()`, `load()` — solve N+1",
        "Constraining eager loads: `with(['posts' => fn($q) => $q->latest()])`",
        "Lazy eager loading vs eager loading",
        "withCount(), withSum(), withAvg()",
        "When to define inverse: always add belongsTo on child",
    ]),
    ("eloquent-advanced", "Eloquent — Advanced Patterns", [
        "Observers: `php artisan make:observer` — created, updated, deleted, etc.",
        "When to use Observers vs Model Events vs Listeners",
        "Observers: best for model lifecycle logic (audit logs, cache busting)",
        "Mutators & Casts: `$casts`, custom cast classes",
        "Accessors: `get{Name}Attribute()` → new: `Attribute::make(get:...)`",
        "Pruning models: `MassPrunable`, `Prunable` traits",
        "Replicating models: `$model->replicate()`",
    ]),
    ("collections", "Collections", [
        "Lazy collections for large datasets",
        "Key methods: map, filter, reject, reduce, groupBy, keyBy",
        "pluck(), unique(), flatten(), chunk()",
        "Higher-order messages: `$collection->filter->isActive()`",
        "collect() helper vs Eloquent collection",
        "When to chain vs when to use array functions",
        "Custom collection classes on models",
    ]),
    ("service-container", "Service Container & Binding", [
        "Auto-resolution via type-hints (zero-config DI)",
        "Binding: `$this->app->bind()`, `singleton()`, `instance()`",
        "Contextual binding: different impl per class",
        "Tagging: bind multiple, resolve by tag",
        "When you need explicit binding vs auto-resolution",
        "Resolving: `app()`, `resolve()`, `make()`",
    ]),
    ("service-providers", "Service Providers", [
        "`register()` — bind things into container",
        "`boot()` — use bindings (view composers, event listeners, routes)",
        "Deferred providers: `$defer = true`, `provides()`",
        "When to create your own vs use existing",
        "Order: register all → boot all",
        "Package service providers: auto-discovery via composer.json",
    ]),
    ("facades", "Facades & Contracts", [
        "How facades work: `__callStatic` → container resolution",
        "Real-time facades: `use Facades\\App\\Services\\MyService`",
        "Contracts (interfaces): swap implementations easily",
        "Facade vs dependency injection — when to use each",
        "Testing: `Cache::fake()`, `Mail::fake()`, `Event::fake()`",
        "Common facades: Cache, DB, Log, Mail, Queue, Storage, Event",
    ]),
    ("events", "Events & Listeners", [
        "`php artisan make:event`, `make:listener`",
        "Registering in EventServiceProvider (or auto-discovery)",
        "Firing: `event(new UserRegistered($user))` or `Event::dispatch()`",
        "Queued listeners: implement `ShouldQueue`",
        "Event subscribers: handle multiple events in one class",
        "When to use Events vs Observers vs direct calls",
        "Events: decouple side effects (send email, notify Slack)",
    ]),
    ("queues", "Queues & Jobs", [
        "`php artisan make:job ProcessPayment`",
        "Dispatching: `ProcessPayment::dispatch()`, `->delay()`, `->onQueue()`",
        "Job chaining: `Bus::chain([])->dispatch()`",
        "Batching: `Bus::batch([])->then()->catch()->dispatch()`",
        "Failed jobs: `failed_jobs` table, `->onFailure()`",
        "Queue workers: `php artisan queue:work`, `queue:listen`",
        "Horizon for Redis queues",
        "When to queue: anything slow (email, API calls, heavy computation)",
    ]),
    ("cache", "Caching", [
        "Drivers: file, redis, memcached, database, array",
        "`Cache::put()`, `get()`, `remember()`, `rememberForever()`, `forget()`",
        "`Cache::tags()` — tag-based invalidation (Redis/Memcached only)",
        "Cache locking: `Cache::lock('key')` — prevent race conditions",
        "HTTP response caching",
        "When to cache: expensive queries, external API responses, computed values",
        "Cache busting strategy with Observers",
    ]),
    ("repositories", "Repository Pattern in Laravel", [
        "Repository = abstraction over data source",
        "Interface → Eloquent implementation → bind in ServiceProvider",
        "When to use: large apps, multiple data sources, TDD",
        "When NOT to use: small apps, adds unnecessary complexity",
        "Thin controllers → repository → Eloquent",
        "Alternatives: Service classes, Action classes (single-responsibility)",
        "Combine with: Query objects for complex queries",
    ]),
    ("actions-services", "Action & Service Classes", [
        "Action class = single responsibility, one `execute()` or `__invoke()`",
        "`php artisan make:class Actions/CreateInvoice`",
        "Service class = groups related business logic",
        "When Actions > Services: distinct, testable operations",
        "When Services > Actions: related ops that share state/deps",
        "Both > fat controllers and fat models",
        "Inject via constructor, use in controllers/jobs/commands",
    ]),
    ("auth", "Authentication & Authorization", [
        "Starter kits: Breeze (simple), Jetstream (full-featured)",
        "Auth guards: web (session), api (token/sanctum)",
        "Policies: `php artisan make:policy PostPolicy --model=Post`",
        "Gates: simple closures for non-model authorization",
        "`$this->authorize()` in controllers, `@can` in Blade",
        "Sanctum: SPA auth (cookies) + API tokens",
        "When to use Policy vs Gate: Policy for model CRUD, Gate for arbitrary actions",
    ]),
    ("authorization-deep", "Authorization — Deep Dive", [
        "Policy methods: viewAny, view, create, update, delete, restore, forceDelete",
        "Policy filters: `before()` method for superadmins",
        "Resource controllers auto-detect policies",
        "`->withoutMiddleware()` to skip auth on specific routes",
        "Blade: `@can`, `@cannot`, `@canany`",
        "Inline: `Gate::allows()`, `Gate::denies()`, `Gate::any()`",
        "Custom response messages from policies",
    ]),
    ("notifications", "Notifications", [
        "`php artisan make:notification InvoicePaid`",
        "Channels: mail, database, broadcast, Slack, SMS (Vonage)",
        "`via()` method — choose channels per notifiable",
        "Database notifications: `notifications` table, `unreadNotifications`",
        "Queueing: implement `ShouldQueue`",
        "On-demand notifications (no notifiable model): `Notification::route()`",
        "When to use: user-facing alerts (email, in-app, push)",
    ]),
    ("broadcasting", "Broadcasting & WebSockets", [
        "Drivers: Pusher, Ably, Laravel Reverb (self-hosted)",
        "Public vs private vs presence channels",
        "Broadcasting events: implement `ShouldBroadcast`",
        "`broadcastOn()`, `broadcastAs()`, `broadcastWith()`",
        "Client side: Echo.js + listen()",
        "When to use: real-time UI updates (chat, live dashboards, notifications)",
    ]),
    ("file-storage", "File Storage", [
        "Disks: local, public, s3 — configured in filesystems.php",
        "`Storage::put()`, `get()`, `exists()`, `delete()`, `url()`",
        "`Storage::disk('s3')->put()`",
        "Public disk symlink: `php artisan storage:link`",
        "File uploads: `$request->file('photo')->store('avatars')`",
        "Fake storage in tests: `Storage::fake('avatars')`",
        "Visibility: public vs private files",
    ]),
    ("artisan-commands", "Artisan Commands", [
        "`php artisan make:command SendEmails`",
        "`handle()` method, `$signature`, `$description`",
        "Arguments & options in signature: `{user}`, `{--queue}`",
        "Scheduling commands in routes/console.php (Laravel 11)",
        "`$schedule->command()->daily()->at('08:00')`",
        "Programmatic dispatch: `Artisan::call('command')`",
        "When to use: batch jobs, maintenance tasks, data migrations",
    ]),
    ("testing", "Testing in Laravel", [
        "PHPUnit + Laravel TestCase, `php artisan make:test`",
        "Feature vs Unit tests",
        "HTTP tests: `$this->get()`, `->post()`, `->assertStatus()`",
        "Database: `RefreshDatabase`, `DatabaseTransactions` traits",
        "Factories: `User::factory()->create()`, states, sequences",
        "Mocking: `Mail::fake()`, `Event::fake()`, `Queue::fake()`",
        "Faking time: `Carbon::setTestNow()`",
        "Pest PHP as alternative to PHPUnit",
    ]),
    ("packages-ecosystem", "Laravel Ecosystem & Packages", [
        "Telescope: debug/profile local dev",
        "Horizon: Redis queue monitoring",
        "Reverb: self-hosted WebSocket server",
        "Sanctum: lightweight API auth",
        "Passport: full OAuth2 server",
        "Cashier: Stripe/Paddle billing",
        "Scout: full-text search (Algolia, Meilisearch)",
        "Octane: Swoole/RoadRunner for high performance",
        "Folio: file-based routing",
        "Volt: single-file Livewire components",
    ]),
]

def get_topic_for_date(date: datetime.date) -> dict:
    """Return the topic for a given date by cycling through the list."""
    index = (date - datetime.date(2026, 6, 26)).days % len(TOPICS)
    slug, name, concepts = TOPICS[index]
    return {"index": index, "slug": slug, "name": name, "concepts": concepts, "total": len(TOPICS)}

def generate_digest(date: datetime.date) -> str:
    topic = get_topic_for_date(date)
    day_num = (date - datetime.date(2026, 6, 26)).days + 1

    lines = [
        f"# Laravel Daily Digest — {date.strftime('%B %d, %Y')}",
        f"",
        f"> **Topic {topic['index'] + 1}/{topic['total']}:** {topic['name']}",
        f"> Day {day_num} of your Laravel mastery journey.",
        f"",
        f"---",
        f"",
        f"## Key Concepts",
        f"",
    ]

    for concept in topic["concepts"]:
        lines.append(f"- {concept}")

    lines += [
        f"",
        f"---",
        f"",
        f"## Quick Mental Model",
        f"",
    ]

    # Add mental models per topic
    mental_models = {
        "installation": "Think of the service container as Laravel's brain — everything flows through it. Config is loaded once, cached, and served fast.",
        "routing": "Routes are contracts. Name every route — never hardcode URLs. Use route model binding to keep controllers clean.",
        "middleware": "Middleware = pipeline. Request flows in, gets checked/transformed, response flows back out. Keep each middleware single-purpose.",
        "controllers": "Controllers = traffic directors. They receive a request, hand off to a service/action, and return a response. No business logic here.",
        "requests": "Form Requests are your gatekeepers. Validation + authorization in one place, before the controller even runs.",
        "responses": "API = JSON Resources. Web = Blade. Never mix. JsonResource transforms your model for output — use it always for APIs.",
        "eloquent-basics": "Eloquent is your data layer. Keep queries in scopes. Keep business logic OUT of models. Fat models → refactor to services.",
        "eloquent-relationships": "N+1 is the enemy. Always eager load with `with()`. Use `withCount()` instead of loading full relationships just to count.",
        "eloquent-advanced": "Observers watch model lifecycle. Use them for side effects (cache busting, audit logs). Don't put business logic in observers.",
        "collections": "`collect()` turns anything into a fluent pipeline. Prefer collection methods over loops. Use lazy collections for 10k+ records.",
        "service-container": "The container resolves dependencies. You only need to bind explicitly when you want a specific implementation or singleton.",
        "service-providers": "`register()` = bind. `boot()` = use. Never use bindings in `register()`. Think of providers as your app's wiring.",
        "facades": "Facades are syntactic sugar over the container. Use them for convenience, inject interfaces in testable code.",
        "events": "Events = 'something happened'. Listeners = 'here's what to do about it'. Decouples your core logic from side effects perfectly.",
        "queues": "If it takes > 200ms, queue it. Jobs should be small, idempotent, and retriable. Chain for sequential, batch for parallel.",
        "cache": "`remember()` is your best friend — fetch if missing, store, return. Always set TTL. Cache at the boundary (controller/repository).",
        "repositories": "Repository hides WHERE data comes from. Controller doesn't care if it's MySQL, Redis, or an API. Bind interface → implementation.",
        "actions-services": "One action = one thing. `CreateUser`, `SendWelcomeEmail`, `ChargeCard`. Composable, testable, readable. Keep them tiny.",
        "auth": "Sanctum for SPAs and simple APIs. Passport only if you're building an OAuth2 *server*. Policies for model-level access control.",
        "authorization-deep": "Policy `before()` is for superadmins. `viewAny` is list page. `view` is show page. Always define all 7 methods.",
        "notifications": "Notification = a message to a user via one or more channels. Database channel = in-app notification bell. Always queue them.",
        "broadcasting": "Broadcast events when the UI needs to update without a page refresh. Private channels require auth. Reverb = free, self-hosted.",
        "file-storage": "Always use `Storage` facade, never `file_get_contents`. S3-compatible storage = just change the driver. Fake it in tests.",
        "artisan-commands": "Commands for operations, not logic. The command calls a service/action. Schedule in console.php, not crontab (mostly).",
        "testing": "Feature tests > unit tests for Laravel. Fake everything external (mail, queues, storage). Factories for data, RefreshDatabase for clean state.",
        "packages-ecosystem": "Know when to reach for a package vs build it. Telescope first for debugging. Sanctum for auth. Scout for search.",
    }

    model = mental_models.get(topic["slug"], "Understand the why behind this feature, not just the how.")
    lines.append(f"**{model}**")
    lines += [
        f"",
        f"---",
        f"",
        f"## When To Use This",
        f"",
    ]

    # When-to-use guidance (practical decision making)
    when_to_use = {
        "observers": "Use Observers when you need to react to model lifecycle events (created, updated, deleted) and the logic doesn't belong in the controller. Good for: cache invalidation, audit logging, syncing related records. Bad for: complex business logic that should be explicit.",
        "repositories": "Use repositories when your app is large enough that you'd benefit from swapping data sources, or when you need complex query logic centralized. Skip them for simple CRUD apps — the abstraction isn't worth it.",
        "events": "Use events when an action triggers multiple unrelated side effects. E.g., UserRegistered → send email + create profile + notify Slack. This keeps each concern separate and testable.",
        "service-container": "You rarely interact with the container directly. Let auto-resolution handle it. Only bind explicitly when you have interfaces, singletons, or need contextual resolution.",
        "actions-services": "Use Action classes for single operations that are reused across controllers, jobs, and commands. Use Service classes when multiple related actions share dependencies or state.",
    }

    lines.append(f"*Topic:* `{topic['slug']}`")
    lines.append(f"")

    # Add relevant when-to-use if applicable
    if topic["slug"] in when_to_use:
        lines.append(when_to_use[topic["slug"]])
    elif topic["slug"] == "eloquent-advanced":
        lines.append(when_to_use["observers"])
    elif topic["slug"] == "repositories":
        lines.append(when_to_use["repositories"])
    else:
        lines.append(f"Re-read the key concepts above and think: *where in my current project could I apply this?*")

    lines += [
        f"",
        f"---",
        f"",
        f"*Generated automatically. Next topic tomorrow.*",
    ]

    return "\n".join(lines)

if __name__ == "__main__":
    today = datetime.date.today()
    digest = generate_digest(today)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "laravel-digest")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{today.isoformat()}.md")

    with open(output_path, "w") as f:
        f.write(digest)

    print(f"Digest written to {output_path}")
    print(f"Topic: {get_topic_for_date(today)['name']}")
