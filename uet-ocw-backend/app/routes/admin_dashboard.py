from flask import Blueprint, redirect, render_template_string, url_for


admin_dashboard_bp = Blueprint("admin_dashboard", __name__)


@admin_dashboard_bp.route("/admin", methods=["GET"])
def admin_index():
    return redirect(url_for("admin_dashboard.admin_login"))


@admin_dashboard_bp.route("/admin/login", methods=["GET"])
def admin_login():
    return render_template_string(ADMIN_LOGIN_HTML)


@admin_dashboard_bp.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    return render_template_string(ADMIN_DASHBOARD_HTML)


ADMIN_LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>UET OCW Admin Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root {
      --bg: #eef3f7;
      --panel: #ffffff;
      --ink: #18212f;
      --muted: #647184;
      --line: #d7e0ea;
      --brand: #0d6efd;
      --brand-dark: #0b5ed7;
      --accent: #f59f00;
      --danger: #b42318;
      --ok: #087443;
      --radius: 16px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      display: grid;
      place-items: center;
      background: var(--bg);
      color: var(--ink);
      padding: 20px;
    }
    button, input { font: inherit; }
    .screen { width: min(980px, 100%); display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: stretch; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 28px;
      box-shadow: 0 18px 42px rgba(22, 38, 60, .1);
    }
    h1, h2 { margin: 0; letter-spacing: 0; }
    h1 { font-size: 28px; line-height: 1.15; }
    h2 { font-size: 18px; }
    p { color: var(--muted); line-height: 1.55; }
    form { display: grid; gap: 12px; margin-top: 18px; }
    label { display: grid; gap: 7px; color: #405168; font-size: 13px; font-weight: 650; }
    input {
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 11px;
      color: var(--ink);
    }
    input:focus { outline: none; border-color: #86b7fe; box-shadow: 0 0 0 .22rem rgba(13,110,253,.14); }
    .btn {
      min-height: 42px;
      border: 1px solid var(--brand);
      background: var(--brand);
      color: white;
      border-radius: 10px;
      padding: 10px 13px;
      font-weight: 700;
      cursor: pointer;
    }
    .btn:hover { background: var(--brand-dark); transform: translateY(-1px); }
    .btn.secondary { background: white; color: var(--ink); border-color: var(--line); }
    .btn.warn { background: var(--accent); border-color: var(--accent); }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .notice { min-height: 24px; margin-top: 12px; color: var(--muted); font-size: 14px; white-space: pre-wrap; }
    .notice.ok { color: var(--ok); }
    .notice.err { color: var(--danger); }
    @media (max-width: 780px) {
      .screen { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="screen">
    <section class="panel">
      <h1>UET OCW Admin</h1>
      <p>Login with an admin account to manage courses, faculties, departments, resources, and approvals.</p>
      <form id="loginForm">
        <label>Email or username<input name="email" required autocomplete="username" /></label>
        <label>Password<input name="password" type="password" required autocomplete="current-password" /></label>
        <div class="actions">
          <button class="btn" type="submit">Login</button>
          <button class="btn secondary" type="button" onclick="clearToken()">Clear saved login</button>
        </div>
      </form>
      <div id="loginNotice" class="notice"></div>
    </section>
    <section class="panel">
      <h2>First admin setup</h2>
      <p>Create the first admin account here. After one admin exists, only a logged-in admin can create more admin accounts.</p>
      <form id="setupForm">
        <label>Username<input name="username" required autocomplete="off" /></label>
        <label>Email<input name="email" type="email" required autocomplete="off" /></label>
        <label>Full name<input name="full_name" /></label>
        <label>Password<input name="password" type="password" required autocomplete="new-password" /></label>
        <button class="btn warn" type="submit">Create first admin</button>
      </form>
      <div id="setupNotice" class="notice"></div>
    </section>
  </main>

  <script>
    const tokenKey = "ocw_admin_token";
    const $ = (id) => document.getElementById(id);

    $("loginForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = formToObject(event.currentTarget);
      setNotice("loginNotice", "Logging in...");
      try {
        const response = await api("/api/auth/login", { method: "POST", body: JSON.stringify(payload) });
        if ((response.data?.role?.name || "").toUpperCase() !== "ADMIN") {
          throw new Error("Only ADMIN users can open the admin dashboard");
        }
        localStorage.setItem(tokenKey, response.access_token);
        window.location.href = "/admin/dashboard";
      } catch (error) {
        setNotice("loginNotice", error.message, false);
      }
    });

    $("setupForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = { ...formToObject(event.currentTarget), role: "ADMIN" };
      setNotice("setupNotice", "Creating admin...");
      try {
        await api("/api/roles/seed", { method: "POST", body: "{}" });
        const response = await api("/api/auth/register", { method: "POST", body: JSON.stringify(payload) });
        localStorage.setItem(tokenKey, response.access_token);
        window.location.href = "/admin/dashboard";
      } catch (error) {
        setNotice("setupNotice", error.message, false);
      }
    });

    async function api(path, options = {}) {
      const response = await fetch(path, {
        ...options,
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      });
      const text = await response.text();
      const data = parseResponse(text);
      if (!response.ok) throw new Error(data.message || response.statusText || "Request failed");
      return data;
    }

    function formToObject(form) {
      const payload = {};
      new FormData(form).forEach((value, key) => {
        if (value !== "") payload[key] = value;
      });
      return payload;
    }

    function setNotice(id, message, ok = null) {
      const notice = $(id);
      notice.textContent = message;
      notice.className = "notice" + (ok === true ? " ok" : ok === false ? " err" : "");
    }

    function parseResponse(text) {
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch (error) {
        return { message: text.replace(/<[^>]*>/g, " ").replace(/\\s+/g, " ").trim() || "Request failed" };
      }
    }

    function clearToken() {
      localStorage.removeItem(tokenKey);
      setNotice("loginNotice", "Saved login cleared", true);
    }
  </script>
</body>
</html>
"""


ADMIN_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>UET OCW Admin</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root {
      --bg: #eef3f7;
      --panel: #ffffff;
      --ink: #18212f;
      --muted: #647184;
      --line: #d7e0ea;
      --brand: #0d6efd;
      --brand-dark: #0b5ed7;
      --accent: #f59f00;
      --danger: #b42318;
      --ok: #087443;
      --radius: 14px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); }
    button, input, select, textarea { font: inherit; }
    button { cursor: pointer; }

    .shell { min-height: 100vh; display: grid; grid-template-columns: 260px minmax(0, 1fr); }
    .sidebar {
      background: #0b1f3a;
      color: #f8fafc;
      padding: 24px 18px;
      position: sticky;
      top: 0;
      height: 100vh;
      box-shadow: 10px 0 30px rgba(13, 31, 58, .16);
    }
    .brand { font-size: 22px; font-weight: 750; letter-spacing: 0; margin: 0 0 4px; }
    .sub { color: rgba(255,255,255,.72); margin: 0 0 24px; font-size: 13px; }
    .nav { display: grid; gap: 8px; }
    .nav button {
      width: 100%;
      border: 1px solid transparent;
      background: transparent;
      color: rgba(255,255,255,.82);
      text-align: left;
      padding: 11px 13px;
      border-radius: 10px;
      font-weight: 650;
      transition: all .18s ease;
    }
    .nav button.active, .nav button:hover { background: rgba(255,255,255,.14); border-color: rgba(255,255,255,.18); color: white; transform: translateX(2px); }
    .main { min-width: 0; }
    .topbar {
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 28px;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,.92);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 5;
      box-shadow: 0 6px 22px rgba(22, 38, 60, .06);
    }
    h1 { margin: 0; font-size: 22px; line-height: 1.2; letter-spacing: 0; }
    .session-bar { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 14px; flex-wrap: wrap; justify-content: flex-end; }
    .content { padding: 28px; display: grid; gap: 22px; }
    .stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
    .stat, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: 0 16px 38px rgba(22, 38, 60, .08);
    }
    .stat { padding: 18px; border-left: 5px solid var(--brand); }
    .stat span { color: var(--muted); font-size: 13px; }
    .stat strong { display: block; margin-top: 8px; font-size: 28px; color: #0b1f3a; }
    .panel { padding: 20px; }
    .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eef2f6; }
    .panel-head .actions { margin-top: 0; }
    h2 { margin: 0; font-size: 17px; line-height: 1.3; letter-spacing: 0; }
    .grid { display: grid; grid-template-columns: 1fr; gap: 18px; }
    .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    label { display: grid; gap: 7px; color: #405168; font-size: 13px; font-weight: 650; }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      background: white;
      color: var(--ink);
      min-height: 42px;
      transition: border-color .18s ease, box-shadow .18s ease;
    }
    input:focus, select:focus, textarea:focus { outline: none; border-color: #86b7fe; box-shadow: 0 0 0 .22rem rgba(13,110,253,.14); }
    textarea { min-height: 86px; resize: vertical; }
    .full { grid-column: 1 / -1; }
    .actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px; flex-wrap: wrap; }
    .btn {
      border: 1px solid var(--brand);
      background: var(--brand);
      color: white;
      border-radius: 10px;
      min-height: 38px;
      padding: 9px 13px;
      font-weight: 650;
      box-shadow: 0 8px 16px rgba(13,110,253,.14);
      transition: all .18s ease;
    }
    .btn:hover { background: var(--brand-dark); border-color: var(--brand-dark); transform: translateY(-1px); }
    .btn.secondary { background: white; color: var(--ink); border-color: var(--line); box-shadow: none; }
    .btn.warn { background: var(--accent); border-color: var(--accent); }
    .btn.danger { background: var(--danger); border-color: var(--danger); }
    .btn.mini { min-height: 32px; padding: 6px 9px; font-size: 12px; }
    .thumb { width: 76px; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 6px; border: 1px solid var(--line); background: #f9fafb; }
    .table-wrap { overflow: auto; border: 1px solid var(--line); border-radius: var(--radius); box-shadow: inset 0 1px 0 rgba(255,255,255,.75); }
    table { width: 100%; border-collapse: collapse; min-width: 720px; background: white; }
    th, td { padding: 12px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; font-size: 14px; }
    th { color: #526173; font-size: 12px; text-transform: uppercase; background: #f8fafc; letter-spacing: .04em; }
    tbody tr:hover { background: #f8fbff; }
    tr:last-child td { border-bottom: 0; }
    .badge { display: inline-flex; align-items: center; min-height: 24px; padding: 3px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .PENDING { color: #8a4b00; background: #fff4d8; }
    .APPROVED { color: var(--ok); background: #dcfce7; }
    .REJECTED { color: var(--danger); background: #fee4e2; }
    .notice { min-height: 24px; color: var(--muted); font-size: 14px; }
    .notice.ok { color: var(--ok); }
    .notice.err { color: var(--danger); }
    .section { display: none; }
    .section.active { display: grid; gap: 18px; }
    .add-panel { display: none; }
    .add-panel.open {
      display: block;
      position: fixed;
      top: 50%;
      left: calc(260px + (100vw - 260px) / 2);
      transform: translate(-50%, -50%);
      width: min(920px, calc(100vw - 320px));
      max-height: calc(100vh - 48px);
      overflow: auto;
      z-index: 60;
      box-shadow: 0 24px 72px rgba(11, 31, 58, .28);
    }
    .form-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, .46);
      z-index: 50;
    }
    .form-backdrop.open { display: block; }
    body.modal-open { overflow: hidden; }

    @media (max-width: 920px) {
      .shell { grid-template-columns: 1fr; }
      .sidebar { position: static; height: auto; }
      .nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .stats, .grid, .form-grid { grid-template-columns: 1fr; }
      .topbar { align-items: flex-start; flex-direction: column; }
      .content { padding: 16px; }
      .full { grid-column: auto; }
      .add-panel.open {
        left: 50%;
        width: calc(100vw - 28px);
        max-height: calc(100vh - 28px);
      }
    }
  </style>
</head>
<body>
  <div class="form-backdrop" id="formBackdrop"></div>
  <div class="shell">
    <aside class="sidebar">
      <p class="brand">UET OCW Admin</p>
      <p class="sub">Courses, resources and approvals</p>
      <nav class="nav">
        <button class="active" data-tab="overview">Overview</button>
        <button data-tab="credentials">Credentials</button>
        <button data-tab="faculties">Faculties</button>
        <button data-tab="departments">Departments</button>
        <button data-tab="courses">Courses</button>
        <button data-tab="internships">Internships</button>
        <button data-tab="research">Research Papers</button>
        <button data-tab="resources">Lectures & Resources</button>
        <button data-tab="internshipResources">Internship Resources</button>
        <button data-tab="teachers">Teacher Approvals</button>
        <button data-tab="students">Student Approvals</button>
      </nav>
    </aside>

    <main class="main">
      <header class="topbar">
        <h1 id="pageTitle">Overview</h1>
        <div class="session-bar">
          <span id="currentUserLabel">Not logged in</span>
          <button class="btn secondary" id="logoutBtn">Logout</button>
          <button class="btn secondary" id="refreshBtn">Refresh</button>
        </div>
      </header>

      <div class="content">
        <section class="section active" id="overview">
          <div class="stats">
            <div class="stat"><span>Faculties</span><strong id="facultyCount">0</strong></div>
            <div class="stat"><span>Departments</span><strong id="departmentCount">0</strong></div>
            <div class="stat"><span>Courses</span><strong id="courseCount">0</strong></div>
            <div class="stat"><span>Internships</span><strong id="internshipCount">0</strong></div>
            <div class="stat"><span>Research papers</span><strong id="researchCount">0</strong></div>
            <div class="stat"><span>Teacher requests</span><strong id="teacherCount">0</strong></div>
            <div class="stat"><span>Student requests</span><strong id="studentCount">0</strong></div>
          </div>
          <div class="panel">
            <div class="panel-head">
              <h2>System status</h2>
              <div class="actions">
                <button class="btn secondary" onclick="seedRoles()">Seed roles</button>
                <button class="btn" type="button" data-add-form="adminSetupForm" onclick="openAddForm('adminSetupForm')">Add admin</button>
              </div>
            </div>
            <div id="statusNotice" class="notice">Ready</div>
          </div>
          <form class="panel add-panel" id="adminSetupForm">
            <div class="panel-head">
              <h2>Create admin account</h2>
              <button class="btn secondary mini" type="button" onclick="hideAddForm('adminSetupForm')">Close</button>
            </div>
            <div class="form-grid">
              <label>Username<input name="username" required autocomplete="username" /></label>
              <label>Email<input name="email" type="email" required autocomplete="email" /></label>
              <label>Full name<input name="full_name" /></label>
              <label>Password<input name="password" type="password" required autocomplete="new-password" /></label>
            </div>
            <div class="actions"><button class="btn warn" type="submit">Create admin</button></div>
          </form>
        </section>

        <section class="section" id="credentials">
          <div class="grid">
            <form class="panel add-panel" id="credentialForm">
              <div class="panel-head">
                <h2>Generate user credentials</h2>
                <button class="btn secondary mini" type="button" onclick="hideAddForm('credentialForm')">Close</button>
              </div>
              <div class="form-grid">
                <label>Role
                  <select name="role" required>
                    <option value="TEACHER">TEACHER</option>
                    <option value="STUDENT">STUDENT</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </label>
                <label>Full name<input name="full_name" /></label>
                <label>Username<input name="username" required autocomplete="off" /></label>
                <label>Email<input name="email" type="email" required autocomplete="off" /></label>
                <label class="full">Password<input name="password" placeholder="Leave empty to auto-generate" autocomplete="new-password" /></label>
              </div>
              <div class="actions">
                <button class="btn" type="submit">Create credentials</button>
                <button class="btn secondary" type="button" onclick="fillGeneratedPassword()">Generate only</button>
              </div>
              <pre id="credentialResult" class="notice"></pre>
            </form>
            <div class="panel">
              <div class="panel-head">
                <h2>Users</h2>
                <button class="btn" type="button" data-add-form="credentialForm" onclick="openAddForm('credentialForm')">Add credentials</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Active</th></tr></thead><tbody id="usersBody"></tbody></table></div>
            </div>
          </div>
        </section>

        <section class="section" id="faculties">
          <div class="grid">
            <form class="panel add-panel" id="facultyForm">
              <div class="panel-head">
                <h2 id="facultyFormTitle">Add faculty</h2>
                <div class="actions">
                  <button class="btn secondary mini" type="button" onclick="resetEntityForm('facultyForm', 'facultyFormTitle', 'Add faculty')">Clear</button>
                  <button class="btn secondary mini" type="button" onclick="hideAddForm('facultyForm')">Close</button>
                </div>
              </div>
              <div class="form-grid">
                <label>Name<input name="name" required /></label>
                <label>Short name<input name="short_name" placeholder="FCS" /></label>
                <label>Logo URL<input name="logo" /></label>
                <label>Website URL<input name="website_url" /></label>
                <label>Display order<input name="display_order" type="number" value="0" /></label>
                <label>Active<select name="is_active"><option value="true">true</option><option value="false">false</option></select></label>
                <label class="full">Description<textarea name="description"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save faculty</button></div>
            </form>
            <div class="panel">
              <div class="panel-head">
                <h2>Faculties</h2>
                <button class="btn" type="button" data-add-form="facultyForm" data-title-id="facultyFormTitle" data-title-text="Add faculty" onclick="openAddForm('facultyForm', 'facultyFormTitle', 'Add faculty')">Add faculty</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Short</th><th>Order</th><th>Active</th><th>Actions</th></tr></thead><tbody id="facultiesBody"></tbody></table></div>
            </div>
          </div>
        </section>

        <section class="section" id="departments">
          <div class="grid">
            <form class="panel add-panel" id="departmentForm">
              <div class="panel-head">
                <h2 id="departmentFormTitle">Add department</h2>
                <div class="actions">
                  <button class="btn secondary mini" type="button" onclick="resetEntityForm('departmentForm', 'departmentFormTitle', 'Add department')">Clear</button>
                  <button class="btn secondary mini" type="button" onclick="hideAddForm('departmentForm')">Close</button>
                </div>
              </div>
              <div class="form-grid">
                <label>Faculty<select name="faculty_id" data-options="faculties"></select></label>
                <label>Type
                  <select name="department_type">
                    <option value="DEPARTMENT">DEPARTMENT</option>
                    <option value="INSTITUTE">INSTITUTE</option>
                    <option value="CENTER">CENTER</option>
                    <option value="LAB">LAB</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </label>
                <label>Name<input name="name" required /></label>
                <label>Short name<input name="short_name" placeholder="CS" /></label>
                <label>Logo URL<input name="logo" /></label>
                <label>Website URL<input name="website_url" /></label>
                <label>Display order<input name="display_order" type="number" value="0" /></label>
                <label>Active<select name="is_active"><option value="true">true</option><option value="false">false</option></select></label>
                <label class="full">Description<textarea name="description"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save department</button></div>
            </form>
            <div class="panel">
              <div class="panel-head">
                <h2>Departments</h2>
                <button class="btn" type="button" data-add-form="departmentForm" data-title-id="departmentFormTitle" data-title-text="Add department" onclick="openAddForm('departmentForm', 'departmentFormTitle', 'Add department')">Add department</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Faculty</th><th>Type</th><th>Active</th><th>Actions</th></tr></thead><tbody id="departmentsBody"></tbody></table></div>
            </div>
          </div>
        </section>

        <section class="section" id="courses">
          <div class="grid">
            <form class="panel add-panel" id="courseForm">
              <div class="panel-head">
                <h2 id="courseFormTitle">Add course</h2>
                <div class="actions">
                  <button class="btn secondary mini" type="button" onclick="resetEntityForm('courseForm', 'courseFormTitle', 'Add course')">Clear</button>
                  <button class="btn secondary mini" type="button" onclick="hideAddForm('courseForm')">Close</button>
                </div>
              </div>
              <div class="form-grid">
                <label>Department<select name="department_id" data-options="departments" required></select></label>
                <label>Course code<input name="course_code" placeholder="CS101" /></label>
                <label class="full">Title<input name="title" required /></label>
                <label>Slug<input name="slug" required /></label>
                <label>Level
                  <select name="level">
                    <option value="UNDERGRADUATE">UNDERGRADUATE</option>
                    <option value="GRADUATE">GRADUATE</option>
                    <option value="BEGINNER">BEGINNER</option>
                    <option value="INTERMEDIATE">INTERMEDIATE</option>
                    <option value="ADVANCED">ADVANCED</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </label>
                <label>Status
                  <select name="status">
                    <option value="DRAFT">DRAFT</option>
                    <option value="PUBLISHED">PUBLISHED</option>
                    <option value="ARCHIVED">ARCHIVED</option>
                  </select>
                </label>
                <label>Semester<input name="semester" placeholder="Spring 2026" /></label>
                <label>Thumbnail image<input name="thumbnail_file" type="file" accept="image/*" /></label>
                <label>Thumbnail URL<input name="thumbnail" placeholder="/uploads/courses/thumbnails/course.jpg" /></label>
                <label class="full">Description<textarea name="description"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save course</button></div>
            </form>
            <div class="panel">
              <div class="panel-head">
                <h2>Courses</h2>
                <button class="btn" type="button" data-add-form="courseForm" data-title-id="courseFormTitle" data-title-text="Add course" onclick="openAddForm('courseForm', 'courseFormTitle', 'Add course')">Add course</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Image</th><th>Title</th><th>Department</th><th>Status</th><th>Actions</th></tr></thead><tbody id="coursesBody"></tbody></table></div>
            </div>
          </div>
        </section>

        <section class="section" id="internships">
          <div class="grid">
            <form class="panel add-panel" id="internshipForm">
              <div class="panel-head">
                <h2 id="internshipFormTitle">Add internship</h2>
                <div class="actions">
                  <button class="btn secondary mini" type="button" onclick="resetEntityForm('internshipForm', 'internshipFormTitle', 'Add internship')">Clear</button>
                  <button class="btn secondary mini" type="button" onclick="hideAddForm('internshipForm')">Close</button>
                </div>
              </div>
              <div class="form-grid">
                <label>Department<select name="department_id" data-options="departments" required></select></label>
                <label>Category<input name="category" placeholder="Industry" /></label>
                <label class="full">Title<input name="title" required /></label>
                <label>Slug<input name="slug" required /></label>
                <label>Duration<input name="duration" placeholder="8 weeks" /></label>
                <label>Status
                  <select name="status">
                    <option value="DRAFT">DRAFT</option>
                    <option value="OPEN">OPEN</option>
                    <option value="CLOSED">CLOSED</option>
                    <option value="ARCHIVED">ARCHIVED</option>
                  </select>
                </label>
                <label>Start date<input name="start_date" type="date" /></label>
                <label>End date<input name="end_date" type="date" /></label>
                <label>Thumbnail image<input name="thumbnail_file" type="file" accept="image/*" /></label>
                <label>Thumbnail URL<input name="thumbnail" placeholder="/uploads/internships/thumbnails/internship.jpg" /></label>
                <label class="full">Description<textarea name="description"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save internship</button></div>
            </form>
            <div class="panel">
              <div class="panel-head">
                <h2>Internships</h2>
                <button class="btn" type="button" data-add-form="internshipForm" data-title-id="internshipFormTitle" data-title-text="Add internship" onclick="openAddForm('internshipForm', 'internshipFormTitle', 'Add internship')">Add internship</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Image</th><th>Title</th><th>Department</th><th>Status</th><th>Actions</th></tr></thead><tbody id="internshipsBody"></tbody></table></div>
            </div>
          </div>
        </section>

        <section class="section" id="research">
          <div class="grid">
            <form class="panel add-panel" id="researchForm">
              <div class="panel-head">
                <h2 id="researchFormTitle">Add research paper</h2>
                <div class="actions">
                  <button class="btn secondary mini" type="button" onclick="resetEntityForm('researchForm', 'researchFormTitle', 'Add research paper')">Clear</button>
                  <button class="btn secondary mini" type="button" onclick="hideAddForm('researchForm')">Close</button>
                </div>
              </div>
              <div class="form-grid">
                <label>Department<select name="department_id" data-options="departments" required></select></label>
                <label>Publication date<input name="publication_date" type="date" /></label>
                <label class="full">Title of paper<input name="title" required /></label>
                <label>Journal or conference
                  <select name="publication_type">
                    <option value="Journal">Journal</option>
                    <option value="Conference">Conference</option>
                  </select>
                </label>
                <label>Status
                  <select name="status">
                    <option value="PUBLISHED">PUBLISHED</option>
                    <option value="DRAFT">DRAFT</option>
                    <option value="ARCHIVED">ARCHIVED</option>
                  </select>
                </label>
                <label>Upload PDF<input name="pdf_file" type="file" accept="application/pdf,.pdf" /></label>
                <label>Link<input name="paper_url" placeholder="https://example.com/paper" /></label>
                <label class="full">Authors name<input name="authors" placeholder="Separate more than one author by comma" /></label>
                <label>DOI<input name="doi" /></label>
                <label>Journal or conference title<input name="publication_title" /></label>
                <label class="full">Keywords<input name="keywords" /></label>
                <label class="full">Abstract HTML<textarea name="abstract" placeholder="<p>Write abstract here...</p>"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save research paper</button></div>
              <pre id="researchResult" class="notice"></pre>
            </form>
            <div class="panel">
              <div class="panel-head">
                <h2>Research papers</h2>
                <button class="btn" type="button" data-add-form="researchForm" data-title-id="researchFormTitle" data-title-text="Add research paper" onclick="openAddForm('researchForm', 'researchFormTitle', 'Add research paper')">Add research paper</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Title</th><th>Department</th><th>Date</th><th>Paper</th><th>Status</th><th>Actions</th></tr></thead><tbody id="researchBody"></tbody></table></div>
            </div>
          </div>
        </section>

        <section class="section" id="resources">
          <div class="grid">
            <div class="panel full">
              <div class="panel-head">
                <h2>Lectures & course resources</h2>
                <div class="actions">
                  <button class="btn" type="button" data-add-form="lectureForm" onclick="openAddForm('lectureForm')">Add lecture</button>
                  <button class="btn" type="button" data-add-form="resourceForm" data-title-id="resourceFormTitle" data-title-text="Add course resource" onclick="openAddForm('resourceForm', 'resourceFormTitle', 'Add course resource')">Add resource</button>
                  <button class="btn secondary" type="button" data-add-form="uploadForm" onclick="openAddForm('uploadForm')">Upload file</button>
                </div>
              </div>
              <div class="notice">Saved course resources are listed in the table below.</div>
            </div>
            <form class="panel add-panel" id="lectureForm">
              <div class="panel-head">
                <h2>Add lecture</h2>
                <button class="btn secondary mini" type="button" onclick="hideAddForm('lectureForm')">Close</button>
              </div>
              <div class="form-grid">
                <label>Course<select name="course_id" data-options="courses" required></select></label>
                <label>Lecture number<input name="lecture_number" type="number" min="1" required /></label>
                <label class="full">Title<input name="title" required /></label>
                <label>Video URL<input name="video_url" /></label>
                <label>Presentation URL<input name="presentation_url" /></label>
                <label>Notes URL<input name="notes_url" /></label>
                <label>Published<select name="is_published"><option value="true">true</option><option value="false">false</option></select></label>
                <label class="full">Description<textarea name="description"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save lecture</button></div>
            </form>
            <form class="panel add-panel" id="resourceForm">
              <div class="panel-head">
                <h2 id="resourceFormTitle">Add course resource</h2>
                <div class="actions">
                  <button class="btn secondary mini" type="button" onclick="resetCourseResourceForm()">Clear</button>
                  <button class="btn secondary mini" type="button" onclick="hideAddForm('resourceForm')">Close</button>
                </div>
              </div>
              <div class="form-grid">
                <label>Course<select name="course_id" data-options="courses" required></select></label>
                <label>Type
                  <select name="resource_type">
                    <option value="PDF">PDF</option>
                    <option value="POWERPOINT">POWERPOINT</option>
                    <option value="VIDEO">VIDEO</option>
                    <option value="BOOK">BOOK</option>
                    <option value="DOCUMENT">DOCUMENT</option>
                    <option value="LINK">LINK</option>
                    <option value="AUDIO">AUDIO</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </label>
                <label class="full">Title<input name="title" required /></label>
                <label>Upload file<input name="resource_file" type="file" /></label>
                <label>File URL<input name="file_url" /></label>
                <label>External URL<input name="external_url" /></label>
                <label>Lecture number<input name="lecture_number" type="number" /></label>
                <label class="full">Description<textarea name="description"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save resource</button></div>
              <pre id="courseResourceResult" class="notice"></pre>
            </form>
            <div class="panel full">
              <div class="panel-head">
                <h2>Course resources</h2>
                <button class="btn" type="button" data-add-form="resourceForm" data-title-id="resourceFormTitle" data-title-text="Add course resource" onclick="openAddForm('resourceForm', 'resourceFormTitle', 'Add course resource')">Add resource</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Course</th><th>Title</th><th>Type</th><th>File</th><th>Actions</th></tr></thead><tbody id="courseResourcesBody"></tbody></table></div>
            </div>
            <form class="panel full add-panel" id="uploadForm">
              <div class="panel-head">
                <h2>Upload resource file</h2>
                <button class="btn secondary mini" type="button" onclick="hideAddForm('uploadForm')">Close</button>
              </div>
              <div class="form-grid">
                <label>File<input name="file" type="file" required /></label>
                <label>Folder<input name="folder" value="courses/resources" /></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Upload file</button></div>
              <pre id="uploadResult" class="notice"></pre>
            </form>
          </div>
        </section>

        <section class="section" id="internshipResources">
          <div class="grid">
            <form class="panel add-panel" id="internshipResourceForm" enctype="multipart/form-data">
              <div class="panel-head">
                <h2 id="internshipResourceFormTitle">Add internship resource</h2>
                <div class="actions">
                  <button class="btn secondary mini" type="button" onclick="resetInternshipResourceForm()">Clear</button>
                  <button class="btn secondary mini" type="button" onclick="hideAddForm('internshipResourceForm')">Close</button>
                </div>
              </div>
              <div class="form-grid">
                <label>Internship<select name="internship_id" data-options="internships" required></select></label>
                <label>Type
                  <select name="resource_type">
                    <option value="PDF">PDF</option>
                    <option value="DOCUMENT">DOCUMENT</option>
                    <option value="VIDEO">VIDEO</option>
                    <option value="LINK">LINK</option>
                    <option value="IMAGE">IMAGE</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </label>
                <label class="full">Title<input name="title" required /></label>
                <label>File<input name="file" type="file" /></label>
                <label>External URL<input name="external_url" /></label>
                <label>Display order<input name="display_order" type="number" value="0" /></label>
                <label>Active<select name="is_active"><option value="true">true</option><option value="false">false</option></select></label>
                <label class="full">Description<textarea name="description"></textarea></label>
              </div>
              <div class="actions"><button class="btn" type="submit">Save internship resource</button></div>
              <pre id="internshipResourceResult" class="notice"></pre>
            </form>
            <div class="panel">
              <div class="panel-head">
                <h2>Internship resources</h2>
                <button class="btn" type="button" data-add-form="internshipResourceForm" data-title-id="internshipResourceFormTitle" data-title-text="Add internship resource" onclick="openAddForm('internshipResourceForm', 'internshipResourceFormTitle', 'Add internship resource')">Add resource</button>
              </div>
              <div class="table-wrap"><table><thead><tr><th>ID</th><th>Internship</th><th>Title</th><th>Type</th><th>File</th><th>Active</th><th>Actions</th></tr></thead><tbody id="internshipResourcesBody"></tbody></table></div>
            </div>
          </div>
        </section>

        <section class="section" id="teachers">
          <div class="panel">
            <div class="panel-head"><h2>Teacher course applications</h2></div>
            <div class="table-wrap"><table><thead><tr><th>ID</th><th>Teacher</th><th>Course</th><th>Status</th><th>Actions</th></tr></thead><tbody id="teachersBody"></tbody></table></div>
          </div>
        </section>

        <section class="section" id="students">
          <div class="panel">
            <div class="panel-head"><h2>Student course applications</h2></div>
            <div class="table-wrap"><table><thead><tr><th>ID</th><th>Student</th><th>Course</th><th>Status</th><th>Actions</th></tr></thead><tbody id="studentsBody"></tbody></table></div>
          </div>
        </section>
      </div>
    </main>
  </div>

  <script>
    const state = { courses: [], courseResources: [], departments: [], faculties: [], internships: [], internshipResources: [], researchPapers: [], teacherApps: [], studentApps: [], users: [], user: null };
    const $ = (id) => document.getElementById(id);
    const token = () => localStorage.getItem("ocw_admin_token") || "";
    const adminHeaders = () => {
      const headers = { "Content-Type": "application/json" };
      if (token()) headers.Authorization = `Bearer ${token()}`;
      return headers;
    };

    document.querySelectorAll(".nav button").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".nav button").forEach((item) => item.classList.remove("active"));
        document.querySelectorAll(".section").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        $(button.dataset.tab).classList.add("active");
        $("pageTitle").textContent = button.textContent;
      });
    });

    document.addEventListener("click", (event) => {
      const button = event.target.closest("[data-add-form]");
      if (!button) return;
      event.preventDefault();
      openAddForm(button.dataset.addForm, button.dataset.titleId || "", button.dataset.titleText || "");
    });

    $("formBackdrop").addEventListener("click", closeOpenForm);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeOpenForm();
    });

    $("refreshBtn").addEventListener("click", loadAll);
    $("logoutBtn").addEventListener("click", logout);
    $("adminSetupForm").addEventListener("submit", createAdminAccount);
    $("credentialForm").addEventListener("submit", createCredentials);
    $("facultyForm").addEventListener("submit", (event) => submitEntity(event, "/api/faculties", "facultyFormTitle", "Add faculty"));
    $("departmentForm").addEventListener("submit", (event) => submitEntity(event, "/api/departments", "departmentFormTitle", "Add department"));
    $("courseForm").addEventListener("submit", (event) => submitJsonWithThumbnail(event, "/api/courses", "courses/thumbnails", "courseFormTitle", "Add course"));
    $("internshipForm").addEventListener("submit", (event) => submitJsonWithThumbnail(event, "/api/internships", "internships/thumbnails", "internshipFormTitle", "Add internship"));
    $("researchForm").addEventListener("submit", submitResearchPaper);
    $("lectureForm").addEventListener("submit", (event) => submitJson(event, "/api/lectures"));
    $("resourceForm").addEventListener("submit", submitCourseResource);
    $("uploadForm").addEventListener("submit", uploadFile);
    $("internshipResourceForm").addEventListener("submit", submitInternshipResource);

    async function api(path, options = {}) {
      const response = await fetch(path, { ...options, headers: { ...adminHeaders(), ...(options.headers || {}) } });
      const text = await response.text();
      const data = parseResponse(text);
      if (!response.ok) throw new Error(data.message || response.statusText || "Request failed");
      return data;
    }

    async function loadAll() {
      setNotice("Loading...");
      try {
        await loadMe();
        if (!state.user) {
          window.location.href = "/admin/login";
          return;
        }
        if ((state.user.role?.name || "").toUpperCase() !== "ADMIN") {
          localStorage.removeItem("ocw_admin_token");
          window.location.href = "/admin/login";
          return;
        }
        const [faculties, courses, courseResources, departments, internships, internshipResources, researchPapers] = await Promise.all([
          api("/api/faculties"),
          api("/api/courses"),
          api("/api/course-resources"),
          api("/api/departments"),
          api("/api/internships"),
          api("/api/internship-resources"),
          api("/api/research-papers"),
        ]);
        state.faculties = faculties.data || [];
        state.courses = courses.data || [];
        state.courseResources = courseResources.data || [];
        state.departments = departments.data || [];
        state.internships = internships.data || [];
        state.internshipResources = internshipResources.data || [];
        state.researchPapers = researchPapers.data || [];
        let partialError = null;

        try {
          const [teacherApps, studentApps, users] = await Promise.all([
            api("/api/course-teaching-applications"),
            api("/api/course-enrollments"),
            api("/api/users"),
          ]);
          state.teacherApps = teacherApps.data || [];
          state.studentApps = studentApps.data || [];
          state.users = users.data || [];
        } catch (error) {
          state.teacherApps = [];
          state.studentApps = [];
          state.users = [];
          partialError = error;
        }

        render();
        if (partialError) setNotice(`Main data loaded. Approval/user data failed: ${partialError.message}`, false);
        else setNotice("Dashboard loaded", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    async function loadMe() {
      if (!token()) {
        state.user = null;
        renderUser();
        return;
      }
      try {
        const me = await api("/api/auth/me");
        state.user = me.data;
      } catch (error) {
        state.user = null;
        localStorage.removeItem("ocw_admin_token");
      }
      renderUser();
    }

    function logout() {
      localStorage.removeItem("ocw_admin_token");
      state.user = null;
      renderUser();
      window.location.href = "/admin/login";
    }

    async function seedRoles() {
      try {
        await api("/api/roles/seed", { method: "POST", body: "{}" });
        setNotice("Roles seeded", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    async function createAdminAccount(event) {
      event.preventDefault();
      const form = event.currentTarget;
      const payload = { ...formToObject(form), role: "ADMIN" };
      try {
        await api("/api/roles/seed", { method: "POST", body: "{}" });
        const response = await api("/api/auth/register", { method: "POST", body: JSON.stringify(payload) });
        localStorage.setItem("ocw_admin_token", response.access_token);
        form.reset();
        hideAddForm("adminSetupForm");
        await loadAll();
        setNotice("Admin account created and logged in", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    async function createCredentials(event) {
      event.preventDefault();
      const form = event.currentTarget;
      if (!token() || !state.user) {
        $("credentialResult").textContent = "Login as admin first, then create teacher/student credentials.";
        setNotice("Login as admin first", false);
        return;
      }
      if ((state.user.role?.name || "").toUpperCase() !== "ADMIN") {
        $("credentialResult").textContent = "Only ADMIN users can create credentials.";
        setNotice("Only ADMIN users can create credentials", false);
        return;
      }

      const payload = formToObject(form);
      if (!payload.password) payload.generate_password = true;
      $("credentialResult").textContent = "Creating credentials...";

      try {
        await api("/api/roles/seed", { method: "POST", body: "{}" });
        const response = await api("/api/users", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        $("credentialResult").textContent = JSON.stringify({
          username: response.data.username,
          email: response.data.email,
          role: response.data.role?.name,
          temporary_password: response.temporary_password || payload.password,
        }, null, 2);
        form.reset();
        hideAddForm("credentialForm");
        await loadAll();
        setNotice("Credentials created", true);
      } catch (error) {
        $("credentialResult").textContent = error.message;
        setNotice(error.message, false);
      }
    }

    function fillGeneratedPassword() {
      $("credentialForm").elements.password.value = randomPassword();
    }

    function randomPassword() {
      const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
      return Array.from({ length: 12 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
    }

    async function submitJson(event, path) {
      event.preventDefault();
      const form = event.currentTarget;
      const payload = formToObject(form);
      try {
        await api(path, { method: "POST", body: JSON.stringify(payload) });
        form.reset();
        hideAddForm(form.id);
        await loadAll();
        setNotice("Saved successfully", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    async function submitCourseResource(event) {
      event.preventDefault();
      const form = event.currentTarget;
      const payload = formToObject(form);
      const file = form.elements.resource_file?.files?.[0];
      const editId = form.dataset.editId;

      try {
        if (file) {
          const courseId = payload.course_id || "general";
          const uploaded = await uploadAdminFile(file, `courses/${courseId}/resources`);
          payload.file_url = uploaded.local_url || uploaded.public_url || payload.file_url;
          payload.file_size = uploaded.size;
          payload.mime_type = uploaded.mime_type;
        }
        await api(editId ? `/api/course-resources/${editId}` : "/api/course-resources", {
          method: editId ? "PUT" : "POST",
          body: JSON.stringify(payload),
        });
        resetCourseResourceForm();
        await loadAll();
        setNotice("Course resource saved", true);
      } catch (error) {
        $("courseResourceResult").textContent = error.message;
        setNotice(error.message, false);
      }
    }

    async function submitResearchPaper(event) {
      event.preventDefault();
      const form = event.currentTarget;
      const body = new FormData(form);
      const editId = form.dataset.editId;
      const headers = {};
      if (token()) headers.Authorization = `Bearer ${token()}`;

      try {
        const response = await fetch(editId ? `/api/research-papers/${editId}` : "/api/research-papers", {
          method: editId ? "PUT" : "POST",
          headers,
          body,
        });
        const data = parseResponse(await response.text());
        if (!response.ok) throw new Error(data.message || response.statusText || "Request failed");
        resetEntityForm("researchForm", "researchFormTitle", "Add research paper");
        $("researchResult").textContent = "";
        await loadAll();
        setNotice("Research paper saved", true);
      } catch (error) {
        $("researchResult").textContent = error.message;
        setNotice(error.message, false);
      }
    }

    async function submitJsonWithThumbnail(event, path, folder, titleId, addTitle) {
      event.preventDefault();
      const form = event.currentTarget;
      const payload = formToObject(form);
      const file = form.elements.thumbnail_file?.files?.[0];
      const editId = form.dataset.editId;

      try {
        if (file) {
          const uploaded = await uploadAdminFile(file, folder);
          payload.thumbnail = uploaded.local_url || uploaded.public_url || payload.thumbnail;
        }
        await api(editId ? `${path}/${editId}` : path, {
          method: editId ? "PUT" : "POST",
          body: JSON.stringify(payload),
        });
        resetEntityForm(form.id, titleId, addTitle);
        await loadAll();
        setNotice("Saved successfully", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    async function submitEntity(event, path, titleId, addTitle) {
      event.preventDefault();
      const form = event.currentTarget;
      const payload = formToObject(form);
      const editId = form.dataset.editId;
      try {
        await api(editId ? `${path}/${editId}` : path, {
          method: editId ? "PUT" : "POST",
          body: JSON.stringify(payload),
        });
        resetEntityForm(form.id, titleId, addTitle);
        await loadAll();
        setNotice("Saved successfully", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    async function uploadFile(event) {
      event.preventDefault();
      const form = event.currentTarget;
      const body = new FormData(form);
      const headers = {};
      if (token()) headers.Authorization = `Bearer ${token()}`;

      try {
        const response = await fetch("/api/uploads", { method: "POST", headers, body });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || response.statusText);
        $("uploadResult").textContent = JSON.stringify({
          media_id: data.media_id,
          local_url: data.local_url,
          public_url: data.public_url,
          absolute_path: data.absolute_path,
          relative_path: data.relative_path,
        }, null, 2);
        form.reset();
        hideAddForm("uploadForm");
        setNotice("File uploaded", true);
      } catch (error) {
        $("uploadResult").textContent = error.message;
        setNotice(error.message, false);
      }
    }

    async function uploadAdminFile(file, folder) {
      const body = new FormData();
      body.append("file", file);
      body.append("folder", folder);
      const headers = {};
      if (token()) headers.Authorization = `Bearer ${token()}`;
      const response = await fetch("/api/uploads", { method: "POST", headers, body });
      const data = parseResponse(await response.text());
      if (!response.ok) throw new Error(data.message || response.statusText || "Upload failed");
      return data;
    }

    async function submitInternshipResource(event) {
      event.preventDefault();
      const form = event.currentTarget;
      const editId = form.dataset.editId;
      const body = new FormData(form);
      const headers = {};
      if (token()) headers.Authorization = `Bearer ${token()}`;

      try {
        const response = await fetch(editId ? `/api/internship-resources/${editId}` : "/api/internship-resources", {
          method: editId ? "PATCH" : "POST",
          headers,
          body,
        });
        const data = parseResponse(await response.text());
        if (!response.ok) throw new Error(data.message || response.statusText || "Request failed");
        resetInternshipResourceForm();
        $("internshipResourceResult").textContent = JSON.stringify(data.data || data, null, 2);
        await loadAll();
        setNotice("Internship resource saved", true);
      } catch (error) {
        $("internshipResourceResult").textContent = error.message;
        setNotice(error.message, false);
      }
    }

    async function review(path) {
      try {
        await api(path, { method: "PATCH", body: "{}" });
        await loadAll();
        setNotice("Review saved", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    async function deleteEntity(path) {
      if (!confirm("Delete this record?")) return;
      try {
        await api(path, { method: "DELETE" });
        await loadAll();
        setNotice("Deleted successfully", true);
      } catch (error) {
        setNotice(error.message, false);
      }
    }

    function formToObject(form) {
      const payload = {};
      new FormData(form).forEach((value, key) => {
        if (value === "") return;
        if (value instanceof File) return;
        const field = form.elements[key];
        if ((field && field.type === "number") || key.endsWith("_id") || key === "course_id" || key === "department_id") payload[key] = Number(value);
        else if (value === "true" || value === "false") payload[key] = value === "true";
        else payload[key] = value;
      });
      return payload;
    }

    function render() {
      renderUser();
      renderSelects();
      $("facultyCount").textContent = state.faculties.length;
      $("departmentCount").textContent = state.departments.length;
      $("courseCount").textContent = state.courses.length;
      $("internshipCount").textContent = state.internships.length;
      $("researchCount").textContent = state.researchPapers.length;
      $("teacherCount").textContent = state.teacherApps.filter((item) => item.status === "PENDING").length;
      $("studentCount").textContent = state.studentApps.filter((item) => item.status === "PENDING").length;

      $("usersBody").innerHTML = rows(state.users, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.full_name || item.username)}</td>
          <td>${escapeHtml(item.email)}</td>
          <td>${escapeHtml(item.role?.name || "")}</td>
          <td>${item.is_active ? "Yes" : "No"}</td>
        </tr>
      `);

      $("facultiesBody").innerHTML = rows(state.faculties, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.name)}</td>
          <td>${escapeHtml(item.short_name || "")}</td>
          <td>${item.display_order ?? 0}</td>
          <td>${item.is_active ? "Yes" : "No"}</td>
          <td>
            <button class="btn secondary mini" onclick="editFaculty(${item.id})">Edit</button>
            <button class="btn danger mini" onclick="deleteEntity('/api/faculties/${item.id}')">Delete</button>
          </td>
        </tr>
      `);
      $("departmentsBody").innerHTML = rows(state.departments, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.name)}</td>
          <td>${escapeHtml(item.faculty?.name || item.faculty_id || "")}</td>
          <td>${escapeHtml(item.department_type || "")}</td>
          <td>${item.is_active ? "Yes" : "No"}</td>
          <td>
            <button class="btn secondary mini" onclick="editDepartment(${item.id})">Edit</button>
            <button class="btn danger mini" onclick="deleteEntity('/api/departments/${item.id}')">Delete</button>
          </td>
        </tr>
      `);
      $("coursesBody").innerHTML = rows(state.courses, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${thumbnailPreview(item.thumbnail)}</td>
          <td>${escapeHtml(item.title)}</td>
          <td>${item.department_id || ""}</td>
          <td>${badge(item.status)}</td>
          <td>
            <button class="btn secondary mini" onclick="editCourse(${item.id})">Edit</button>
            <button class="btn danger mini" onclick="deleteEntity('/api/courses/${item.id}')">Delete</button>
          </td>
        </tr>
      `);
      $("internshipsBody").innerHTML = rows(state.internships, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${thumbnailPreview(item.thumbnail)}</td>
          <td>${escapeHtml(item.title)}</td>
          <td>${item.department_id || ""}</td>
          <td>${badge(item.status)}</td>
          <td>
            <button class="btn secondary mini" onclick="editInternship(${item.id})">Edit</button>
            <button class="btn danger mini" onclick="deleteEntity('/api/internships/${item.id}')">Delete</button>
          </td>
        </tr>
      `);
      $("courseResourcesBody").innerHTML = rows(state.courseResources, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.course?.title || item.course_id)}</td>
          <td>${escapeHtml(item.title)}</td>
          <td>${escapeHtml(item.resource_type || "")}</td>
          <td>${resourceLink(item)}</td>
          <td>
            <button class="btn secondary mini" onclick="editCourseResource(${item.id})">Edit</button>
            <button class="btn danger mini" onclick="deleteEntity('/api/course-resources/${item.id}')">Delete</button>
          </td>
        </tr>
      `);
      $("researchBody").innerHTML = rows(state.researchPapers, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.title)}</td>
          <td>${item.department_id || ""}</td>
          <td>${item.publication_date || item.publication_year || ""}</td>
          <td>${paperLink(item)}</td>
          <td>${badge(item.status)}</td>
          <td>
            <button class="btn secondary mini" onclick="editResearchPaper(${item.id})">Edit</button>
            <button class="btn danger mini" onclick="deleteEntity('/api/research-papers/${item.id}')">Delete</button>
          </td>
        </tr>
      `);
      $("internshipResourcesBody").innerHTML = rows(state.internshipResources, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.internship?.title || item.internship_id)}</td>
          <td>${escapeHtml(item.title)}</td>
          <td>${escapeHtml(item.resource_type || "")}</td>
          <td>${resourceLink(item)}</td>
          <td>${item.is_active ? "Yes" : "No"}</td>
          <td>
            <button class="btn secondary mini" onclick="editInternshipResource(${item.id})">Edit</button>
            <button class="btn danger mini" onclick="deleteEntity('/api/internship-resources/${item.id}')">Delete</button>
          </td>
        </tr>
      `);
      $("teachersBody").innerHTML = rows(state.teacherApps, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.teacher?.full_name || item.teacher?.username || item.teacher_id)}</td>
          <td>${escapeHtml(item.course?.title || item.course_id)}</td>
          <td>${badge(item.status)}</td>
          <td>${reviewButtons(`/api/course-teaching-applications/${item.id}`)}</td>
        </tr>
      `);
      $("studentsBody").innerHTML = rows(state.studentApps, (item) => `
        <tr>
          <td>${item.id}</td>
          <td>${escapeHtml(item.student?.full_name || item.student?.username || item.student_id)}</td>
          <td>${escapeHtml(item.course?.title || item.course_id)}</td>
          <td>${badge(item.status)}</td>
          <td>${reviewButtons(`/api/course-enrollments/${item.id}`)}</td>
        </tr>
      `);
    }

    function renderSelects() {
      document.querySelectorAll('select[data-options="faculties"]').forEach((select) => {
        const current = select.value;
        select.innerHTML = `<option value="">Select faculty</option>` + state.faculties.map((item) => (
          `<option value="${item.id}">${escapeHtml(item.name)} (${item.id})</option>`
        )).join("");
        select.value = current;
      });
      document.querySelectorAll('select[data-options="departments"]').forEach((select) => {
        const current = select.value;
        select.innerHTML = `<option value="">Select department</option>` + state.departments.map((item) => (
          `<option value="${item.id}">${escapeHtml(item.name)} (${item.id})</option>`
        )).join("");
        select.value = current;
      });
      document.querySelectorAll('select[data-options="courses"]').forEach((select) => {
        const current = select.value;
        select.innerHTML = `<option value="">Select course</option>` + state.courses.map((item) => (
          `<option value="${item.id}">${escapeHtml(item.title)} (${item.id})</option>`
        )).join("");
        select.value = current;
      });
      document.querySelectorAll('select[data-options="internships"]').forEach((select) => {
        const current = select.value;
        select.innerHTML = `<option value="">Select internship</option>` + state.internships.map((item) => (
          `<option value="${item.id}">${escapeHtml(item.title)} (${item.id})</option>`
        )).join("");
        select.value = current;
      });
    }

    function renderUser() {
      if (state.user) {
        $("currentUserLabel").textContent = `${state.user.full_name || state.user.username} (${state.user.role?.name || "USER"})`;
      } else {
        $("currentUserLabel").textContent = "Not logged in";
      }
    }

    function editFaculty(id) {
      const item = state.faculties.find((faculty) => faculty.id === id);
      if (!item) return;
      fillForm("facultyForm", item, ["name", "short_name", "description", "logo", "website_url", "display_order", "is_active"]);
      $("facultyForm").dataset.editId = id;
      $("facultyFormTitle").textContent = `Edit faculty #${id}`;
      openTab("faculties");
      showAddForm("facultyForm");
    }

    function editDepartment(id) {
      const item = state.departments.find((department) => department.id === id);
      if (!item) return;
      fillForm("departmentForm", item, ["faculty_id", "name", "short_name", "department_type", "description", "logo", "website_url", "display_order", "is_active"]);
      $("departmentForm").dataset.editId = id;
      $("departmentFormTitle").textContent = `Edit department #${id}`;
      openTab("departments");
      showAddForm("departmentForm");
    }

    function editCourse(id) {
      const item = state.courses.find((course) => course.id === id);
      if (!item) return;
      fillForm("courseForm", item, [
        "department_id",
        "course_code",
        "title",
        "slug",
        "level",
        "status",
        "semester",
        "thumbnail",
        "description",
      ]);
      $("courseForm").dataset.editId = id;
      $("courseFormTitle").textContent = `Edit course #${id}`;
      openTab("courses");
      showAddForm("courseForm");
    }

    function editInternship(id) {
      const item = state.internships.find((internship) => internship.id === id);
      if (!item) return;
      fillForm("internshipForm", item, [
        "department_id",
        "category",
        "title",
        "slug",
        "duration",
        "status",
        "start_date",
        "end_date",
        "thumbnail",
        "description",
      ]);
      $("internshipForm").dataset.editId = id;
      $("internshipFormTitle").textContent = `Edit internship #${id}`;
      openTab("internships");
      showAddForm("internshipForm");
    }

    function editCourseResource(id) {
      const item = state.courseResources.find((resource) => resource.id === id);
      if (!item) return;
      const form = $("resourceForm");
      fillForm("resourceForm", item, ["course_id", "title", "resource_type", "file_url", "external_url", "lecture_number", "description"]);
      form.dataset.editId = id;
      $("resourceFormTitle").textContent = `Edit course resource #${id}`;
      $("courseResourceResult").textContent = item.file_url ? `Current file: ${item.file_url}` : "";
      openTab("resources");
      showAddForm("resourceForm");
    }

    function editResearchPaper(id) {
      const item = state.researchPapers.find((paper) => paper.id === id);
      if (!item) return;
      const form = $("researchForm");
      fillForm("researchForm", item, [
        "department_id",
        "publication_date",
        "title",
        "publication_type",
        "status",
        "paper_url",
        "authors",
        "doi",
        "keywords",
        "abstract",
      ]);
      form.elements.publication_type.value = normalizePublicationType(item.publication_type);
      form.elements.publication_title.value = item.conference_name || item.journal_name || "";
      form.dataset.editId = id;
      $("researchFormTitle").textContent = `Edit research paper #${id}`;
      $("researchResult").textContent = item.pdf_url ? `Current file: ${item.pdf_url}` : "";
      openTab("research");
      showAddForm("researchForm");
    }

    function editInternshipResource(id) {
      const item = state.internshipResources.find((resource) => resource.id === id);
      if (!item) return;
      const form = $("internshipResourceForm");
      fillForm("internshipResourceForm", item, ["internship_id", "title", "resource_type", "external_url", "display_order", "is_active", "description"]);
      form.dataset.editId = id;
      $("internshipResourceFormTitle").textContent = `Edit internship resource #${id}`;
      $("internshipResourceResult").textContent = item.file_url ? `Current file: ${item.file_url}` : "";
      openTab("internshipResources");
      showAddForm("internshipResourceForm");
    }

    function fillForm(formId, item, fields) {
      const form = $(formId);
      fields.forEach((field) => {
        if (!form.elements[field]) return;
        form.elements[field].value = item[field] ?? "";
      });
    }

    function resetEntityForm(formId, titleId, title) {
      const form = $(formId);
      form.reset();
      delete form.dataset.editId;
      $(titleId).textContent = title;
      renderSelects();
      hideAddForm(formId);
    }

    function resetInternshipResourceForm() {
      const form = $("internshipResourceForm");
      form.reset();
      delete form.dataset.editId;
      $("internshipResourceFormTitle").textContent = "Add internship resource";
      $("internshipResourceResult").textContent = "";
      renderSelects();
      hideAddForm("internshipResourceForm");
    }

    function resetCourseResourceForm() {
      const form = $("resourceForm");
      form.reset();
      delete form.dataset.editId;
      $("resourceFormTitle").textContent = "Add course resource";
      $("courseResourceResult").textContent = "";
      renderSelects();
      hideAddForm("resourceForm");
    }

    function openTab(tab) {
      document.querySelector(`.nav button[data-tab="${tab}"]`)?.click();
    }

    function showAddForm(formId) {
      const form = $(formId);
      if (!form) return;
      document.querySelectorAll(".add-panel.open").forEach((panel) => panel.classList.remove("open"));
      form.classList.add("open");
      $("formBackdrop").classList.add("open");
      document.body.classList.add("modal-open");
      renderSelects();
      form.querySelector("input, select, textarea")?.focus({ preventScroll: true });
    }

    function openAddForm(formId, titleId = "", title = "") {
      const form = $(formId);
      if (!form) return;
      form.reset();
      delete form.dataset.editId;
      if (titleId && $(titleId)) $(titleId).textContent = title;
      if (formId === "resourceForm") $("courseResourceResult").textContent = "";
      if (formId === "researchForm") $("researchResult").textContent = "";
      if (formId === "internshipResourceForm") $("internshipResourceResult").textContent = "";
      if (formId === "uploadForm") $("uploadResult").textContent = "";
      if (formId === "credentialForm") $("credentialResult").textContent = "";
      showAddForm(formId);
    }

    function hideAddForm(formId) {
      const form = $(formId);
      if (!form) return;
      form.classList.remove("open");
      if (!document.querySelector(".add-panel.open")) {
        $("formBackdrop").classList.remove("open");
        document.body.classList.remove("modal-open");
      }
    }

    function closeOpenForm() {
      document.querySelectorAll(".add-panel.open").forEach((panel) => panel.classList.remove("open"));
      $("formBackdrop").classList.remove("open");
      document.body.classList.remove("modal-open");
    }

    window.showAddForm = showAddForm;
    window.openAddForm = openAddForm;
    window.hideAddForm = hideAddForm;
    window.closeOpenForm = closeOpenForm;

    function rows(items, template) {
      return items.length ? items.map(template).join("") : `<tr><td colspan="5">No records found</td></tr>`;
    }

    function reviewButtons(basePath) {
      return `
        <button class="btn" onclick="review('${basePath}/approve')">Approve</button>
        <button class="btn danger" onclick="review('${basePath}/reject')">Reject</button>
      `;
    }

    function badge(status) {
      const safe = escapeHtml(status || "UNKNOWN");
      return `<span class="badge ${safe}">${safe}</span>`;
    }

    function resourceLink(item) {
      const href = item.file_url || item.external_url || "";
      if (!href) return "";
      return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener">Open</a>`;
    }

    function paperLink(item) {
      const href = item.pdf_url || item.paper_url || "";
      if (!href) return "";
      return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener">Open</a>`;
    }

    function normalizePublicationType(value) {
      return String(value || "").toLowerCase() === "conference" ? "Conference" : "Journal";
    }

    function thumbnailPreview(url) {
      if (!url) return "";
      return `<img class="thumb" src="${escapeHtml(url)}" alt="" />`;
    }

    function setNotice(message, ok = null) {
      const notice = $("statusNotice");
      notice.textContent = message;
      notice.className = "notice" + (ok === true ? " ok" : ok === false ? " err" : "");
    }

    function parseResponse(text) {
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch (error) {
        return { message: text.replace(/<[^>]*>/g, " ").replace(/\\s+/g, " ").trim() || "Request failed" };
      }
    }

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      }[char]));
    }

    loadAll();
  </script>
</body>
</html>
"""
