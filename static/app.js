/* ═══════════════════════════════════════════════════════════════════════
   URBAN MOOD INDEX — app.js
   Connects to Flask API and drives every live element on the page.
   ═══════════════════════════════════════════════════════════════════════ */

const API = '';   // empty = same origin (Flask serves both API + HTML)
// If running Flask on a different port during dev, set e.g.:
// const API = 'http://localhost:5050';

const CITY_CFG = {
  Chennai:   { accent: '#00ff88', glow: '0 0 30px rgba(0,255,136,0.3)',  code: 'MDS', dotColor: '#00ff88' },
  Mumbai:    { accent: '#ffcc00', glow: '0 0 30px rgba(255,204,0,0.3)',   code: 'BOM', dotColor: '#ffcc00' },
  Bangalore: { accent: '#ff3344', glow: '0 0 30px rgba(255,51,68,0.3)',  code: 'BLR', dotColor: '#ff3344' },
};

const CITY_STATIC = {
  Chennai:   { temp: null },
  Mumbai:    { temp: null },
  Bangalore: { temp: null },
};

// traffic + weather populated from API
let latestTraffic = {};
let latestWeather = {};

/* ────────────────────────────────────────────────────────────
   CURSOR
   ──────────────────────────────────────────────────────────── */
(function initCursor() {
  const dot   = document.getElementById('cursor');
  const trail = document.getElementById('cursor-trail');
  let mouseX = 0, mouseY = 0;
  let trailX = 0, trailY = 0;

  document.addEventListener('mousemove', e => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    dot.style.left = mouseX + 'px';
    dot.style.top  = mouseY + 'px';
  });

  function animateTrail() {
    trailX += (mouseX - trailX) * 0.18;
    trailY += (mouseY - trailY) * 0.18;
    trail.style.left = trailX + 'px';
    trail.style.top  = trailY + 'px';
    requestAnimationFrame(animateTrail);
  }
  animateTrail();
})();

/* ────────────────────────────────────────────────────────────
   CLOCK
   ──────────────────────────────────────────────────────────── */
function tickClock() {
  const t = new Date().toLocaleTimeString('en-US', { hour12: false });
  document.getElementById('navTime').textContent = t;
}
setInterval(tickClock, 1000);
tickClock();

/* ────────────────────────────────────────────────────────────
   SCROLL REVEAL
   ──────────────────────────────────────────────────────────── */
const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in-view'); });
}, { threshold: 0.1 });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* ────────────────────────────────────────────────────────────
   TICKER  (populated once, then updates with live data)
   ──────────────────────────────────────────────────────────── */
function buildTicker(cityData) {
  const tickerEl = document.getElementById('ticker');

  const baseItems = [
    { label: 'KAFKA STREAM',  val: 'ACTIVE',              cls: '' },
    { label: 'SPARK JOBS',    val: '3 RUNNING',           cls: '' },
    { label: 'POSTGRESQL',    val: 'CONNECTED',           cls: '' },
    { label: 'SOURCES',       val: 'REDDIT · NEWS · WEATHER · TRAFFIC', cls: '' },
    { label: 'WINDOW',        val: '30 SEC',              cls: '' },
  ];

  const cityItems = (cityData || []).map(c => {
    const sign = c.mood_score >= 0 ? '+' : '';
    const cls  = c.status === 'positive' ? '' : (c.status === 'negative' ? 'red' : 'yellow');
    return { label: c.city.toUpperCase(), val: sign + c.mood_score.toFixed(3), cls };
  });

  const allItems = [...cityItems, ...baseItems];
  // Duplicate for seamless loop
  const doubled  = [...allItems, ...allItems];

  tickerEl.innerHTML = doubled.map(item =>
    `<span class="ticker-item">${item.label} <span class="ticker-val ${item.cls}">${item.val}</span></span>`
  ).join('');
}

// init with placeholder while data loads
buildTicker([
  { city: 'Chennai',   mood_score: 0,    status: 'neutral' },
  { city: 'Mumbai',    mood_score: 0,    status: 'neutral' },
  { city: 'Bangalore', mood_score: 0,    status: 'neutral' },
]);

/* ────────────────────────────────────────────────────────────
   CITY CARDS
   ──────────────────────────────────────────────────────────── */
function renderCityCards(cities) {
  const grid = document.getElementById('cityGrid');
  if (!cities || cities.length === 0) {
    grid.innerHTML = '<div class="api-error">No city data available yet. Waiting for stream…</div>';
    return;
  }

  grid.innerHTML = cities.map(c => {
    const cfg    = CITY_CFG[c.city] || { accent: '#00ff88', code: '???', dotColor: '#00ff88' };
    const sign   = c.mood_score >= 0 ? '+' : '';
    const barPct = Math.round(((c.mood_score + 1) / 2) * 100);

    const traffic = latestTraffic[c.city];
    const weather = latestWeather[c.city];
    const trafficLabel = traffic ? traffic.congestion_level : '—';
    const trafficColor = trafficLabel === 'Heavy' ? '#ff3344' : (trafficLabel === 'Moderate' ? '#ffcc00' : '#00ff88');
    const tempLabel    = weather ? Math.round(weather.temperature) + '°C' : '—';

    return `
      <div class="city-card" style="--card-accent:${cfg.accent}">
        <div class="city-name">${c.city}</div>
        <div class="city-score" style="color:${cfg.accent}">${sign}${c.mood_score.toFixed(3)}</div>
        <div class="city-status ${c.status}">
          <div class="live-dot" style="width:6px;height:6px;background:${cfg.dotColor};box-shadow:${cfg.glow};"></div>
          ${c.status.charAt(0).toUpperCase() + c.status.slice(1)}
        </div>
        <div class="city-bar-wrap">
          <div class="city-bar" style="background:${cfg.accent};width:${barPct}%"></div>
        </div>
        <div class="city-meta">
          <div class="city-meta-item">
            <span class="city-meta-val" style="color:${trafficColor}">${trafficLabel}</span>
            <span class="city-meta-key">Traffic</span>
          </div>
          <div class="city-meta-item">
            <span class="city-meta-val">${tempLabel}</span>
            <span class="city-meta-key">Temp</span>
          </div>
          <div class="city-meta-item">
            <span class="city-meta-val">${c.stress_score.toFixed(2)}</span>
            <span class="city-meta-key">Stress</span>
          </div>
        </div>
        <div class="city-bignum">${cfg.code}</div>
      </div>`;
  }).join('');
}

/* ────────────────────────────────────────────────────────────
   CHART.JS MOOD TREND
   ──────────────────────────────────────────────────────────── */
let moodChart = null;

function initChart() {
  const ctx = document.getElementById('moodChart').getContext('2d');
  moodChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        { label: 'Chennai',   data: [], borderColor: '#00ff88', backgroundColor: 'rgba(0,255,136,0.04)',  borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#00ff88', tension: 0.4, fill: true },
        { label: 'Mumbai',    data: [], borderColor: '#ffcc00', backgroundColor: 'rgba(255,204,0,0.04)',   borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#ffcc00', tension: 0.4, fill: true },
        { label: 'Bangalore', data: [], borderColor: '#ff3344', backgroundColor: 'rgba(255,51,68,0.04)',  borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#ff3344', tension: 0.4, fill: true },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      animation: { duration: 400 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0d0d14',
          borderColor: 'rgba(255,255,255,0.08)', borderWidth: 1,
          titleColor: '#555570', bodyColor: '#e8e8f0',
          titleFont: { family: 'Space Mono', size: 10 },
          bodyFont:  { family: 'Space Mono', size: 11 },
          padding: 12,
        }
      },
      scales: {
        x: {
          grid:   { color: 'rgba(255,255,255,0.04)' },
          ticks:  { color: '#555570', font: { family: 'Space Mono', size: 9 }, maxTicksLimit: 6 },
          border: { color: 'rgba(255,255,255,0.06)' }
        },
        y: {
          min: -1, max: 1,
          grid:   { color: 'rgba(255,255,255,0.04)' },
          ticks:  { color: '#555570', font: { family: 'Space Mono', size: 9 }, callback: v => (v > 0 ? '+' : '') + v.toFixed(1) },
          border: { color: 'rgba(255,255,255,0.06)' }
        }
      }
    }
  });
}

function updateChart(series) {
  if (!moodChart || !series) return;

  // Build a unified label list from whichever city has the most data
  const allLabels = Object.values(series).reduce((best, cur) =>
    cur.labels.length > best.length ? cur.labels : best, []);

  moodChart.data.labels = allLabels;

  const cityOrder = ['Chennai', 'Mumbai', 'Bangalore'];
  cityOrder.forEach((city, i) => {
    moodChart.data.datasets[i].data = series[city] ? series[city].values : [];
  });

  moodChart.update('none');
}

/* ────────────────────────────────────────────────────────────
   STRESS GAUGES
   ──────────────────────────────────────────────────────────── */
function stressLabel(score) {
  if (score >= 0.7) return 'HIGH STRESS';
  if (score >= 0.5) return 'MODERATE';
  return 'STABLE';
}

function directionArrow(dir) {
  return dir === 'increase' ? '↑' : (dir === 'decrease' ? '↓' : '→');
}

function gaugeOffset(value) {
  // semicircle arc length ≈ 172; offset controls filled portion
  return (172 - 172 * Math.max(0, Math.min(1, value))).toFixed(1);
}

function renderGauges(forecasts) {
  const grid = document.getElementById('stressGrid');
  if (!forecasts || forecasts.length === 0) {
    grid.innerHTML = '<div class="api-error" style="grid-column:1/-1">Waiting for forecast data…</div>';
    return;
  }

  grid.innerHTML = forecasts.map(f => {
    const cfg    = CITY_CFG[f.city] || { accent: '#00ff88' };
    const offset = gaugeOffset(f.current_stress);
    const arrow  = directionArrow(f.direction);
    const label  = stressLabel(f.current_stress);

    return `
      <div class="stress-card">
        <div class="gauge-wrap">
          <svg viewBox="0 0 140 80" width="140" height="80" style="overflow:visible">
            <path class="gauge-track" d="M 15 75 A 55 55 0 0 1 125 75"/>
            <path class="gauge-fill" d="M 15 75 A 55 55 0 0 1 125 75"
              stroke="${cfg.accent}"
              stroke-dasharray="172"
              stroke-dashoffset="${offset}"/>
            <text x="70" y="68" text-anchor="middle"
              font-family="'Bebas Neue'" font-size="22" fill="${cfg.accent}">
              ${f.current_stress.toFixed(2)}
            </text>
          </svg>
        </div>
        <div class="gauge-city">${f.city}</div>
        <div class="gauge-label" style="color:${cfg.accent}">${label}</div>
        <div class="gauge-forecast">
          FORECAST → <span style="color:${cfg.accent}">${f.predicted_stress.toFixed(2)} ${arrow}</span>
        </div>
      </div>`;
  }).join('');
}

/* ────────────────────────────────────────────────────────────
   ALERTS
   ──────────────────────────────────────────────────────────── */
function renderAlerts(cities, forecasts) {
  const list = document.getElementById('alertsList');
  const now  = new Date();
  const timeStr = now.toLocaleTimeString('en-US', { hour12: false });

  const entries = (cities || []).map(c => {
    const forecast = (forecasts || []).find(f => f.city === c.city);
    let level, icon, badge, msg;

    if (c.stress_score >= 0.7) {
      level = 'high'; icon = '🔴'; badge = 'CRITICAL';
      msg = `Experiencing HIGH stress levels — ${latestTraffic[c.city]?.congestion_level || 'elevated'} traffic combined with negative sentiment spike`;
    } else if (c.stress_score >= 0.5) {
      level = 'moderate'; icon = '🟡'; badge = 'MODERATE';
      msg = `Under moderate stress — traffic index elevated, mood score at ${c.mood_score.toFixed(3)}`;
    } else {
      level = 'stable'; icon = '🟢'; badge = 'STABLE';
      msg = `Stress levels stable — sentiment positive across news and social streams`;
    }

    const forecastNote = forecast
      ? ` · Forecast: ${forecast.predicted_stress.toFixed(2)} ${directionArrow(forecast.direction)}`
      : '';

    return `
      <div class="alert-item ${level}">
        <div class="alert-icon">${icon}</div>
        <div class="alert-body">
          <div class="alert-city">${c.city}</div>
          <div class="alert-msg">${msg}</div>
          <div class="alert-time">${timeStr} · Stress: ${c.stress_score.toFixed(2)}${forecastNote}</div>
        </div>
        <div class="alert-badge ${level}">${badge}</div>
      </div>`;
  }).sort((a, b) => {
    // Sort: high first, stable last
    const order = { high: 0, moderate: 1, stable: 2 };
    const la = a.includes('alert-item high') ? 'high' : (a.includes('moderate') ? 'moderate' : 'stable');
    const lb = b.includes('alert-item high') ? 'high' : (b.includes('moderate') ? 'moderate' : 'stable');
    return order[la] - order[lb];
  });

  list.innerHTML = entries.join('') || '<div class="api-error">No alert data yet.</div>';
}

/* ────────────────────────────────────────────────────────────
   FOOTER STATUS
   ──────────────────────────────────────────────────────────── */
function updateFooter(updated) {
  const el = document.getElementById('footerTime');
  if (el && updated) {
    el.textContent = new Date(updated).toLocaleTimeString('en-US', { hour12: false });
  }
}

/* ────────────────────────────────────────────────────────────
   API FETCH HELPERS
   ──────────────────────────────────────────────────────────── */
async function fetchJSON(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}

/* ────────────────────────────────────────────────────────────
   MAIN DATA REFRESH
   Polls all endpoints every 5 seconds.
   ──────────────────────────────────────────────────────────── */
async function refreshAll() {
  try {
    // Fire all requests in parallel
    const [moodData, trendData, forecastData, weatherData, trafficData] = await Promise.allSettled([
      fetchJSON('/api/mood'),
      fetchJSON('/api/trend'),
      fetchJSON('/api/forecast'),
      fetchJSON('/api/weather'),
      fetchJSON('/api/traffic'),
    ]);

    // Traffic lookup map
    if (trafficData.status === 'fulfilled' && trafficData.value.traffic) {
      latestTraffic = {};
      trafficData.value.traffic.forEach(t => { latestTraffic[t.city] = t; });
    }

    // Weather lookup map
    if (weatherData.status === 'fulfilled' && weatherData.value.weather) {
      latestWeather = {};
      weatherData.value.weather.forEach(w => { latestWeather[w.city] = w; });
    }

    // City cards
    if (moodData.status === 'fulfilled') {
      const cities = moodData.value.cities || [];
      renderCityCards(cities);
      buildTicker(cities);
      updateFooter(moodData.value.updated);

      // Alerts need mood + forecast
      const forecasts = forecastData.status === 'fulfilled' ? forecastData.value.forecasts : [];
      renderAlerts(cities, forecasts);
    }

    // Chart
    if (trendData.status === 'fulfilled') {
      updateChart(trendData.value.series);
    }

    // Gauges
    if (forecastData.status === 'fulfilled') {
      renderGauges(forecastData.value.forecasts);
    }

  } catch (err) {
    console.error('Refresh error:', err);
  }
}

/* ────────────────────────────────────────────────────────────
   BOOT
   ──────────────────────────────────────────────────────────── */
initChart();
refreshAll();                           // immediate first load
setInterval(refreshAll, 5000);          // then every 5 seconds
