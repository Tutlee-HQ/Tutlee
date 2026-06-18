/**
 * Tutlee API Client — inlined static copy
 */
const TutleeAPI = (function() {

  var BASE = 'https://tutlee-backend.onrender.com';
  var _access = null, _refresh = null, _user = null, _onAuthChange = null;

  function APIError(message, status, body) {
    this.name = 'APIError'; this.message = message; this.status = status; this.body = body;
  }
  APIError.prototype = Object.create(Error.prototype);

  async function _req(method, path, body, opts) {
    opts = opts || {};
    var headers = { 'Content-Type': 'application/json' };
    if (_access && !opts.noAuth) headers['Authorization'] = 'Bearer ' + _access;
    var resp = await fetch(BASE + path, { method: method, headers: headers, body: body ? JSON.stringify(body) : undefined });
    if (resp.status === 401 && _refresh && !opts.noRefresh) {
      var ok = await _silentRefresh();
      if (ok) {
        headers['Authorization'] = 'Bearer ' + _access;
        resp = await fetch(BASE + path, { method: method, headers: headers, body: body ? JSON.stringify(body) : undefined });
      }
    }
    if (!resp.ok) {
      var eb; try { eb = await resp.json(); } catch(e) { eb = { detail: resp.statusText }; }
      throw new APIError(eb.detail || JSON.stringify(eb), resp.status, eb);
    }
    if (resp.status === 204) return null;
    return resp.json();
  }

  async function _silentRefresh() {
    try {
      var data = await _req('POST', '/api/auth/refresh/', { refresh: _refresh }, { noAuth: true, noRefresh: true });
      _access = data.access;
      if (data.refresh) _refresh = data.refresh;
      return true;
    } catch(e) {
      _access = _refresh = _user = null;
      if (_onAuthChange) _onAuthChange(null);
      return false;
    }
  }

  function g(p, o)    { return _req('GET',    p, null, o); }
  function po(p, b, o){ return _req('POST',   p, b,    o); }
  function pa(p, b, o){ return _req('PATCH',  p, b,    o); }
  function d(p, o)    { return _req('DELETE', p, null, o); }

  async function _upload(method, path, formData) {
    var headers = {};
    if (_access) headers['Authorization'] = 'Bearer ' + _access;
    var resp = await fetch(BASE + path, { method: method, headers: headers, body: formData });
    if (!resp.ok) { var eb = await resp.json().catch(function(){ return { detail: resp.statusText }; }); throw new APIError(eb.detail || 'Upload failed', resp.status, eb); }
    return resp.json();
  }

  var Auth = {
    login: async function(email, password) {
      var data = await po('/api/auth/login/', { email: email, password: password }, { noAuth: true });
      _access = data.access; _refresh = data.refresh; _user = data.user;
      if (_onAuthChange) _onAuthChange(_user);
      return data;
    },
    register: async function(payload) {
      var data = await po('/api/accounts/register/', payload, { noAuth: true });
      _access = data.access; _refresh = data.refresh; _user = data.user;
      if (_onAuthChange) _onAuthChange(_user);
      return data;
    },
    logout:      function() { _access = _refresh = _user = null; if (_onAuthChange) _onAuthChange(null); },
    currentUser: function() { return _user; },
    isLoggedIn:  function() { return !!_access; },
    isAdmin:     function() { return _user && (_user.role === 'admin' || _user.is_staff); },
    onAuthChange: function(cb) { _onAuthChange = cb; },
    refreshMe: async function() { _user = await g('/api/accounts/me/'); return _user; },
  };

  var Users = {
    me:           function()    { return g('/api/accounts/me/'); },
    updateMe:     function(b)   { return pa('/api/accounts/me/', b); },
    list:         function(p)   { return g('/api/accounts/users/' + (p||'')); },
    detail:       function(id)  { return g('/api/accounts/users/' + id + '/'); },
    suspend:      function(id)  { return po('/api/accounts/users/' + id + '/suspend/'); },
    delete:       function(id)  { return d('/api/accounts/users/' + id + '/'); },
    adminStats:   function()    { return g('/api/accounts/stats/'); },
    updateTutorProfile:   function(b) { return pa('/api/accounts/me/tutor-profile/', b); },
    updateLearnerProfile: function(b) { return pa('/api/accounts/me/learner-profile/', b); },
    matchTutors: function(subject, weakAreas) {
      var p = new URLSearchParams({ subject: subject || '' });
      (weakAreas || []).forEach(function(a){ p.append('weak_areas', a); });
      return g('/api/accounts/tutors/match/?' + p.toString());
    },
  };

  var Sessions = {
    list:   function(p)    { return g('/api/sessions/' + (p||'')); },
    book:   function(b)    { return po('/api/sessions/book/', b); },
    detail: function(id)   { return g('/api/sessions/' + id + '/'); },
    update: function(id,b) { return pa('/api/sessions/' + id + '/', b); },
    start:  function(id)   { return po('/api/sessions/' + id + '/start/'); },
    end:    function(id)   { return po('/api/sessions/' + id + '/end/'); },
    rate:   function(id,b) { return po('/api/sessions/' + id + '/rate/', b); },
  };

  var Assessments = {
    list:   function()     { return g('/api/assessments/'); },
    detail: function(id)   { return g('/api/assessments/' + id + '/'); },
    submit: function(id,b) { return po('/api/assessments/' + id + '/submit/', b); },
    stats:  function()     { return g('/api/assessments/stats/'); },
  };

  var KYT = {
    submit:  function(fd)    { return _upload('POST', '/api/kyt/submit/', fd); },
    myApp:   function()      { return g('/api/kyt/me/'); },
    list:    function(s)     { return g('/api/kyt/' + (s ? '?status=' + s : '')); },
    approve: function(id)    { return po('/api/kyt/' + id + '/approve/'); },
    reject:  function(id,b)  { return po('/api/kyt/' + id + '/reject/', b); },
  };

  var Rings = {
    list:    function(s)    { return g('/api/rings/' + (s ? '?subject=' + encodeURIComponent(s) : '')); },
    detail:  function(id)   { return g('/api/rings/' + id + '/'); },
    create:  function(b)    { return po('/api/rings/', b); },
    update:  function(id,b) { return pa('/api/rings/' + id + '/', b); },
    delete:  function(id)   { return d('/api/rings/' + id + '/'); },
    join:    function(id)   { return po('/api/rings/' + id + '/join/'); },
    leave:   function(id)   { return po('/api/rings/' + id + '/leave/'); },
    feature: function(id)   { return po('/api/rings/' + id + '/feature/'); },
    posts:   function(id)   { return g('/api/rings/' + id + '/posts/'); },
    addPost: function(id,b) { return po('/api/rings/' + id + '/posts/', b); },
  };

  var Reports = {
    file:   function(b)      { return po('/api/reports/', b); },
    list:   function(t, s)   { var p = new URLSearchParams(); if (t) p.set('type',t); if (s) p.set('status',s); return g('/api/reports/all/?' + p); },
    action: function(id,b)   { return po('/api/reports/' + id + '/action/', b); },
  };

  var Payments = {
    transactions:  function()   { return g('/api/payments/transactions/'); },
    requestPayout: function()   { return po('/api/payments/request-payout/'); },
    payouts:       function(s)  { return g('/api/payments/payouts/' + (s ? '?status=' + s : '')); },
    approvePayout: function(id) { return po('/api/payments/payouts/' + id + '/approve/'); },
    declinePayout: function(id) { return po('/api/payments/payouts/' + id + '/decline/'); },
    revenueStats:  function()   { return g('/api/payments/stats/'); },
  };

  async function ping() {
    try { var r = await fetch(BASE + '/api/accounts/me/', { method: 'GET' }); return r.status !== 0; }
    catch(e) { return false; }
  }

  return { Auth: Auth, Users: Users, Sessions: Sessions, Assessments: Assessments, KYT: KYT, Rings: Rings, Reports: Reports, Payments: Payments, ping: ping, APIError: APIError };

})();

window.API = TutleeAPI;
