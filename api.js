/**
 * Tutlee API Client
 * Shared by index.html (learner/tutor app) and admin.html (admin panel).
 * Uses JWT Bearer tokens. Tokens are held in memory only (no localStorage).
 */

const TutleeAPI = (() => {

  // ── CONFIG ──────────────────────────────────────────────────────────────────
  const BASE = 'https://tutlee-backend.onrender.com';

  let _access  = null;
  let _refresh = null;
  let _user    = null;
  let _onAuthChange = null;   // callback when login/logout happens

  // ── INTERNAL HTTP HELPERS ────────────────────────────────────────────────────
  async function _req(method, path, body, opts = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (_access && !opts.noAuth) headers['Authorization'] = `Bearer ${_access}`;

    let resp = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    // Try silent token refresh on 401
    if (resp.status === 401 && _refresh && !opts.noRefresh) {
      const refreshed = await _silentRefresh();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${_access}`;
        resp = await fetch(`${BASE}${path}`, {
          method, headers,
          body: body ? JSON.stringify(body) : undefined,
        });
      }
    }

    if (!resp.ok) {
      let errBody;
      try { errBody = await resp.json(); } catch { errBody = { detail: resp.statusText }; }
      const msg = errBody.detail || errBody.non_field_errors?.[0] || JSON.stringify(errBody);
      throw new APIError(msg, resp.status, errBody);
    }

    if (resp.status === 204) return null;
    return resp.json();
  }

  async function _silentRefresh() {
    try {
      const data = await _req('POST', '/api/auth/refresh/', { refresh: _refresh }, { noAuth: true, noRefresh: true });
      _access  = data.access;
      if (data.refresh) _refresh = data.refresh;
      return true;
    } catch {
      _access = _refresh = _user = null;
      if (_onAuthChange) _onAuthChange(null);
      return false;
    }
  }

  const get  = (path, opts)        => _req('GET',    path, null, opts);
  const post = (path, body, opts)  => _req('POST',   path, body, opts);
  const put  = (path, body, opts)  => _req('PUT',    path, body, opts);
  const patch = (path, body, opts) => _req('PATCH',  path, body, opts);
  const del  = (path, opts)        => _req('DELETE', path, null, opts);

  // ── MULTIPART UPLOAD (for KYT files) ────────────────────────────────────────
  async function _upload(method, path, formData) {
    const headers = {};
    if (_access) headers['Authorization'] = `Bearer ${_access}`;
    const resp = await fetch(`${BASE}${path}`, { method, headers, body: formData });
    if (!resp.ok) {
      const errBody = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new APIError(errBody.detail || 'Upload failed', resp.status, errBody);
    }
    return resp.json();
  }

  // ── ERROR CLASS ──────────────────────────────────────────────────────────────
  class APIError extends Error {
    constructor(message, status, body) {
      super(message);
      this.status = status;
      this.body   = body;
    }
  }

  // ── AUTH ─────────────────────────────────────────────────────────────────────
  const Auth = {
    async login(email, password) {
      const data = await post('/api/auth/login/', { email, password }, { noAuth: true });
      _access  = data.access;
      _refresh = data.refresh;
      _user    = data.user;
      if (_onAuthChange) _onAuthChange(_user);
      try { sessionStorage.setItem('_t_a', data.access); sessionStorage.setItem('_t_r', data.refresh); sessionStorage.setItem('_t_u', JSON.stringify(data.user)); } catch(e){}
      return data;
    },

    async register(payload) {
      const data = await post('/api/accounts/register/', payload, { noAuth: true });
      _access  = data.access;
      _refresh = data.refresh;
      _user    = data.user;
      if (_onAuthChange) _onAuthChange(_user);
      try { sessionStorage.setItem('_t_a', data.access); sessionStorage.setItem('_t_r', data.refresh); sessionStorage.setItem('_t_u', JSON.stringify(data.user)); } catch(e){}
      return data;
    },

    logout() {
      _access = _refresh = _user = null;
      if (_onAuthChange) _onAuthChange(null);
      try { sessionStorage.removeItem('_t_a'); sessionStorage.removeItem('_t_r'); sessionStorage.removeItem('_t_u'); } catch(e){}
    },

    restoreSession() {
      try {
        var a = sessionStorage.getItem('_t_a');
        var r = sessionStorage.getItem('_t_r');
        var u = sessionStorage.getItem('_t_u');
        if (a && u) {
          _access  = a;
          _refresh = r || null;
          _user    = JSON.parse(u);
          if (_onAuthChange) _onAuthChange(_user);
          return _user;
        }
      } catch(e) {}
      return null;
    },

    currentUser() { return _user; },
    isLoggedIn()  { return !!_access; },
    isAdmin()     { return _user?.role === 'admin' || _user?.is_staff; },

    onAuthChange(cb) { _onAuthChange = cb; },

    async refreshMe() {
      _user = await get('/api/accounts/me/');
      return _user;
    },

    async verifyOTP(email, code) {
      const data = await post('/api/accounts/otp/verify/', { email, code }, { noAuth: true });
      _access  = data.access;
      _refresh = data.refresh;
      _user    = data.user;
      if (_onAuthChange) _onAuthChange(_user);
      try { sessionStorage.setItem('_t_a', data.access); sessionStorage.setItem('_t_r', data.refresh); sessionStorage.setItem('_t_u', JSON.stringify(data.user)); } catch(e){}
      return data;
    },

    async sendOTP(email) {
      return post('/api/accounts/otp/send/', { email }, { noAuth: true });
    },
  };

  // ── USERS ────────────────────────────────────────────────────────────────────
  const Users = {
    me:           ()          => get('/api/accounts/me/'),
    updateMe:     (data)      => patch('/api/accounts/me/', data),
    list:         (params='') => get(`/api/accounts/users/${params}`),
    detail:       (id)        => get(`/api/accounts/users/${id}/`),
    suspend:      (id)        => post(`/api/accounts/users/${id}/suspend/`),
    delete:       (id)        => del(`/api/accounts/users/${id}/`),
    adminStats:   ()          => get('/api/accounts/stats/'),
    updateTutorProfile:   (data) => patch('/api/accounts/me/tutor-profile/', data),
    updateLearnerProfile: (data) => patch('/api/accounts/me/learner-profile/', data),
    matchTutors:  (subject, weakAreas=[]) => {
      const params = new URLSearchParams({ subject });
      weakAreas.forEach(a => params.append('weak_areas', a));
      return get(`/api/accounts/tutors/match/?${params}`);
    },
  };

  // ── SESSIONS ─────────────────────────────────────────────────────────────────
  const Sessions = {
    list:    (params='') => get(`/api/sessions/${params}`),
    book:    (data)      => post('/api/sessions/book/', data),
    detail:  (id)        => get(`/api/sessions/${id}/`),
    update:  (id, data)  => patch(`/api/sessions/${id}/`, data),
    start:   (id)        => post(`/api/sessions/${id}/start/`),
    end:     (id)        => post(`/api/sessions/${id}/end/`),
    rate:    (id, data)  => post(`/api/sessions/${id}/rate/`, data),
  };

  // ── ASSESSMENTS ──────────────────────────────────────────────────────────────
  const Assessments = {
    list:    ()          => get('/api/assessments/'),
    detail:  (id)        => get(`/api/assessments/${id}/`),
    submit:  (id, data)  => post(`/api/assessments/${id}/submit/`, data),
    stats:   ()          => get('/api/assessments/stats/'),
  };

  // ── KYT ──────────────────────────────────────────────────────────────────────
  const KYT = {
    submit:   (formData) => _upload('POST', '/api/kyt/submit/', formData),
    myApp:    ()         => get('/api/kyt/me/'),
    list:     (status='')=> get(`/api/kyt/${status ? '?status='+status : ''}`),
    approve:  (id)       => post(`/api/kyt/${id}/approve/`),
    reject:   (id, data) => post(`/api/kyt/${id}/reject/`, data),
  };

  // ── STUDY RINGS ───────────────────────────────────────────────────────────────
  const Rings = {
    list:    (subject='') => get(`/api/rings/${subject ? '?subject='+encodeURIComponent(subject) : ''}`),
    detail:  (id)         => get(`/api/rings/${id}/`),
    create:  (data)       => post('/api/rings/', data),
    update:  (id, data)   => patch(`/api/rings/${id}/`, data),
    delete:  (id)         => del(`/api/rings/${id}/`),
    join:    (id)         => post(`/api/rings/${id}/join/`),
    leave:   (id)         => post(`/api/rings/${id}/leave/`),
    feature: (id)         => post(`/api/rings/${id}/feature/`),
    posts:   (id)         => get(`/api/rings/${id}/posts/`),
    addPost: (id, data)   => post(`/api/rings/${id}/posts/`, data),
  };

  // ── REPORTS ───────────────────────────────────────────────────────────────────
  const Reports = {
    file:    (data)       => post('/api/reports/', data),
    list:    (type='',status='') => {
      const p = new URLSearchParams();
      if (type)   p.set('type', type);
      if (status) p.set('status', status);
      return get(`/api/reports/all/?${p}`);
    },
    action:  (id, data)   => post(`/api/reports/${id}/action/`, data),
  };

  // ── PAYMENTS ──────────────────────────────────────────────────────────────────
  const Payments = {
    transactions:   ()       => get('/api/payments/transactions/'),
    requestPayout:  ()       => post('/api/payments/request-payout/'),
    payouts:        (status='')=> get(`/api/payments/payouts/${status ? '?status='+status : ''}`),
    approvePayout:  (id)     => post(`/api/payments/payouts/${id}/approve/`),
    declinePayout:  (id)     => post(`/api/payments/payouts/${id}/decline/`),
    revenueStats:   ()       => get('/api/paym