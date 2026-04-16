# Map Feature: Google Maps Migration

**Branch:** `map-feature`
**Date:** 2026-04-16

## Overview

Replace the existing Leaflet/OpenStreetMap map on the Find Housing page with Google Maps JavaScript API. Add a radius dropdown filter to the existing filter bar. Pins link directly to property detail pages.

## Approach

Option A — pure frontend swap with backend radius filtering. No new pages or URL patterns. Fits existing split-pane layout.

## Backend Changes

### `perch/settings.py`
Add:
```python
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
```

### `student/views.py` — `FindHousingView.get()`
- Accept `radius` GET param (float, default `1.0`), choices: `0.5`, `1`, `2`, `5` miles
- Filter queryset: `qs = qs.filter(distance_miles__lte=radius)`
- Add `url` field to each entry in `map_pins`: `reverse('listings:property', args=[l.pk])`
- Pass `radius` and `GOOGLE_MAPS_API_KEY` into template context

## Frontend Changes

### `student/templates/student/find_housing.html`

**Filter bar:** Add radius dropdown between existing filters:
```
Price | Beds | Type | Radius | Apply | Clear
```
Radius options: 0.5 mi, 1 mi, 2 mi, 5 mi. Default 1 mi.

**Map panel:** Replace Leaflet with Google Maps JS API:
- Remove Leaflet CSS/JS imports
- Load Google Maps via `<script src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_api_key }}"></script>` in `{% block extra_head %}`
- `new google.maps.Map(el, { center: {lat: 42.3355, lng: -71.1685}, zoom: 14 })`
- Per pin: `new google.maps.Marker(...)` — click → `window.location.href = p.url` (direct, no delay)
- `new google.maps.Circle(...)` centered on BC, radius = selected miles × 1609.34 meters, light fill + border
- Card↔pin sync: clicking a card pans map (`map.panTo`) and opens `InfoWindow` with title + price
- InfoWindow content links to `p.url`

## Data Flow

```
GET /student/find-housing/?radius=2&min_price=...
  → FindHousingView filters qs by distance_miles <= 2
  → builds map_pins JSON with lat, lng, title, price, url, pk
  → renders template with map_pins + google_maps_api_key + radius
  → Google Maps renders pins, circle drawn at 2mi radius around BC
  → pin click → window.location.href to property page
```

## Constants

- BC campus center: `lat=42.3355, lng=-71.1685`
- Miles to meters: `× 1609.34`
- Radius choices: `0.5, 1, 2, 5`
- Default radius: `1`

## Out of Scope

- Switching geocoding from Nominatim to Google Geocoding API (not needed, lat/lng already stored)
- Any changes to the property detail page
- Mobile-specific map controls
