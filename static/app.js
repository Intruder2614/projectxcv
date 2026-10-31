const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const state = {
  page: "overview", overview: null, students: [], assignments: [], notes: [], projects: [], versions: [],
  selectedNoteId: null, currentProjectId: null, currentFile: "main.py", currentLanguage: "Python",
  studentFilter: "all", studentSearch: "", noteFilter: "all", assignmentFilter: "all", editorTimer: null,
  currentStudent: null, pageLoading: false,
  arenaTab: "console", hasGui: false, latestRun: null,
  consoleOutput: "Ready. Run the current program to inspect output and errors.",
  stdinValue: "", arenaTemplates: [],
  turtleState: { speed: 2, currentStep: 0, animId: null, isPlaying: false, showGrid: false },
  pygameState: { animId: null, isPlaying: false, frame: 0, keys: {}, ball: null, paddle: null },
  tkinterState: { count: 0, greeting: "", logs: [] }
};
const pageNames = {overview:"Overview",learners:"Learner intelligence",insights:"Class insights",collaboration:"Teacher collaboration",assignments:"Assignments",workspace:"Coding arena",versions:"Version history"};
const starterFiles = {
  "Python": {"main.py": '# A small change can be a big learning moment.\nname = "Coder"\nprint(f"Hello, {name}!")\nprint("Welcome to Codingal Code Studio.")\n'},
  "Java": {"Main.java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, Codingal!");\n        System.out.println("One step at a time.");\n    }\n}\n'},
  "C++": {"main.cpp": '#include <iostream>\nint main() {\n    std::cout << "Hello, Codingal!\\n";\n    return 0;\n}\n'},
  "HTML/CSS/JS": {"index.html": '<!doctype html>\n<html>\n<head><meta charset="utf-8"><title>My project</title>\n<style>body{font-family:Arial,sans-serif;padding:2rem}h1{color:#f45b4f}</style></head>\n<body><h1>Hello, Codingal!</h1><p>Build something great.</p>\n<button onclick="document.querySelector(\'p\').textContent=\'You made it interactive!\'">Try me</button>\n</body></html>\n'}
};
async function api(path, options = {}) {
  const opts = {...options, headers:{"Content-Type":"application/json", ...(options.headers||{})}};
  if (opts.body && typeof opts.body !== "string") opts.body = JSON.stringify(opts.body);
  const response = await fetch(path, opts);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("json") ? await response.json() : await response.text();
  if (!response.ok) throw new Error((data && data.detail) || data.message || `Request failed (${response.status})`);
  return data;
}
function esc(value) { return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function initials(name) { return String(name||"?").trim().split(/\s+/).slice(0,2).map(x=>x[0]||"").join("").toUpperCase(); }
function avatarClass(name) { const n=String(name||"").charCodeAt(0)%5; return ["coral","blue","purple","green","amber"][n]; }
function prettyDate(value) { if(!value)return "No date"; const d=new Date(value); if(Number.isNaN(d.getTime()))return value; return d.toLocaleDateString(undefined,{month:"short",day:"numeric"}); }
function relativeDate(value) { if(!value)return "No activity recorded"; const days=Math.floor((Date.now()-new Date(value).getTime())/86400000); if(days<=0)return "Active today"; if(days===1)return "Active yesterday"; return `Active ${days} days ago`; }
function percent(value) { return `${Math.round(Number(value)||0)}%`; }
function iconForLanguage(lang) { return ({Python:"🐍",Java:"☕","C++":"⚙","HTML/CSS/JS":"◈"})[lang] || "⌘"; }
function riskTag(risk) { const map={high:['Needs support','red'],watch:['Watch','amber'],on_track:['On track','green']};const x=map[risk]||map.watch;return `<span class="tag ${x[1]}">${x[0]}</span>`; }
function priorityTag(priority) { const map={urgent:['Urgent','red'],high:['High','red'],medium:['Medium','amber'],low:['Low','blue']};const x=map[priority]||map.medium;return `<span class="tag ${x[1]}">${x[0]}</span>`; }
function statusTag(status) { const map={open:['Open','amber'],in_progress:['In progress','blue'],resolved:['Resolved','green'],submitted:['Submitted','blue'],reviewed:['Reviewed','green'],active:['Active','green'],review:['Review','amber'],archived:['Archived','']};const x=map[status]||[status,''];return `<span class="tag ${x[1]}">${esc(x[0])}</span>`; }
function toast(message, type="") { const root=$("#toastRoot");const el=document.createElement("div");el.className=`toast ${type}`;el.textContent=message;root.appendChild(el);setTimeout(()=>{el.style.opacity="0";el.style.transform="translateY(5px)";setTimeout(()=>el.remove(),200)},3300); }
function heading(title, subtitle, actions="") { return `<div class="page-heading"><div><div class="eyebrow">Codingal · Learning Intelligence</div><h1>${title}</h1><p class="page-subtitle">${subtitle}</p></div><div class="heading-actions">${actions}</div></div>`; }
function metricCard(label,value,foot,icon,color="",extra="") { return `<section class="card metric-card"><div class="metric-top"><span class="metric-label">${label}</span><span class="metric-icon ${color}">${icon}</span></div><div class="metric-value">${value}</div><div class="metric-foot">${extra}<span>${foot}</span></div></section>`; }
function conceptRows(concepts) { if(!concepts?.length)return `<div class="empty-state"><div class="empty-icon">⌁</div><h3>No concept signals yet</h3><p>Concept scores will appear once assessment and coding events are connected.</p></div>`; return `<div class="concept-list">${concepts.map(c=>`<div class="concept-row"><span class="concept-name">${esc(c.name)}</span><div class="progress-track"><div class="progress-fill ${c.score>=80?'good':c.score<65?'warn':''}" style="width:${Math.max(2,Math.min(100,c.score))}%"></div></div><strong class="concept-score">${c.score}%</strong></div>`).join("")}</div>`; }
function chartBars(items) { if(!items?.length)return `<div class="empty-state"><p>Activity will appear here.</p></div>`;const max=Math.max(...items.map(x=>x.value||0),1);return `<div class="chart-wrap"><div class="chart-y"><span>${max}</span><span>${Math.round(max*.66)}</span><span>${Math.round(max*.33)}</span><span>0</span></div><div class="chart-area"><div class="chart-gridlines"><span></span><span></span><span></span><span></span></div><div class="bar-chart">${items.map((x,i)=>`<div class="bar-group"><div class="bar-stack" title="${esc(x.label)}: ${x.value}"><div class="chart-bar ${i===items.length-1?'strong':''}" style="--bar-height:${Math.max(3,(x.value/max)*100)}%"></div></div><div class="bar-x">${esc(x.label)}</div></div>`).join("")}</div></div></div>`; }
function studentRow(s) { return `<tr><td><div class="student-cell"><div class="person-avatar ${avatarClass(s.name)}">${initials(s.name)}</div><div><strong>${esc(s.name)}</strong><small>${esc(s.grade)} · ${esc(s.class_name)}</small></div></div></td><td><div class="mini-progress"><div class="progress-track"><div class="progress-fill ${s.mastery>=80?'good':s.mastery<65?'warn':''}" style="width:${s.mastery}%"></div></div><strong>${s.mastery}%</strong></div></td><td><span class="${s.mastery_delta>=0?'risk-copy':'risk-copy'}" style="color:${s.mastery_delta>=0?'var(--green)':'var(--red)'}">${s.mastery_delta>0?'+':''}${s.mastery_delta} pts</span></td><td><div class="mini-progress"><div class="progress-track"><div class="progress-fill good" style="width:${s.completion}%"></div></div><strong>${s.completion}%</strong></div></td><td>${riskTag(s.risk)}</td><td><span class="soft-label">${relativeDate(s.last_active)}</span></td><td><button class="table-link" data-action="student-detail" data-id="${s.id}">View profile →</button></td></tr>`; }
function recentSubmissionRows(rows) { if(!rows?.length)return `<div class="empty-state"><div class="empty-icon">☷</div><h3>No submissions yet</h3><p>Submissions appear here as students turn in work.</p></div>`;return `<div class="data-list">${rows.map(s=>`<div class="data-row"><div class="person-avatar ${avatarClass(s.student)}">${initials(s.student)}</div><div class="row-copy"><strong>${esc(s.student)}</strong><small>${esc(s.assignment)} · ${prettyDate(s.submitted_at)}</small></div><div class="row-end"><span class="tag ${s.status==='reviewed'?'green':'blue'}">${s.status==='reviewed'?'Reviewed':'Submitted'}</span><span class="row-value">${Math.round(s.score)}%</span></div></div>`).join("")}</div>`; }
function recommendationItems(items) { if(!items?.length)return `<div class="empty-state"><div class="empty-icon">✓</div><h3>No priority actions</h3><p>There are no suggested follow-ups based on the current demo signals.</p></div>`;return `<div>${items.map((r,i)=>`<div class="action-item"><div class="action-symbol ${r.priority==='high'?'red':i%2?'blue':''}">${r.type==='concept'?'↗':r.type==='collaboration'?'▤':'♧'}</div><div class="action-copy"><strong>${esc(r.title)}</strong><p>${esc(r.detail)}</p><span class="tag ${r.priority==='high'?'red':'amber'}">${r.priority==='high'?'Priority action':'Suggested action'}</span></div></div>`).join("")}</div>`; }
function metricDateFoot(count,label) { return `<span class="up">${count}</span><span>${label}</span>`; }

async function navigate(page) {
  state.page=page;state.currentStudent=null;
  $$(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.page===page));
  $("#currentBreadcrumb").textContent=pageNames[page]||"Overview";
  $("#sidebar").classList.remove("mobile-open");
  $("#app").innerHTML=`<div class="loading-state"><div class="spinner"></div><span>Loading ${esc(pageNames[page]||'workspace').toLowerCase()}…</span></div>`;
  try {
    if(page==="overview"){state.overview=await api("/api/overview");renderOverview();}
    else if(page==="learners"){const d=await api(`/api/students?risk=${encodeURIComponent(state.studentFilter)}&search=${encodeURIComponent(state.studentSearch)}`);state.students=d.items;renderLearners();}
    else if(page==="insights"){state.overview=await api("/api/overview");state.students=(await api("/api/students")).items;state.notes=(await api("/api/notes")).items;renderInsights();}
    else if(page==="collaboration"){state.notes=(await api(`/api/notes?status=${encodeURIComponent(state.noteFilter)}`)).items;if(!state.selectedNoteId||!state.notes.some(n=>n.id===state.selectedNoteId))state.selectedNoteId=state.notes[0]?.id||null;renderCollaboration();}
    else if(page==="assignments"){state.assignments=(await api("/api/assignments")).items;renderAssignments();}
    else if(page==="workspace"){await loadWorkspace();renderWorkspace();}
    else if(page==="versions"){await loadWorkspace();await renderVersions();}
    else {navigate("overview");return;}
  } catch(e) { $("#app").innerHTML=`${heading("Something went wrong","The local service returned an error.")}<section class="card card-pad"><h3>Could not load this view</h3><p class="page-subtitle" style="margin-top:8px">${esc(e.message)}</p><button class="btn btn-primary" style="margin-top:15px" data-action="retry">Retry</button></section>`; }
}

function renderOverview(){const d=state.overview,m=d.metrics;const support=d.learners_to_support||[];const assignments=d.assignments||[];const conceptLowest=d.concepts?.[0];$("#learnerNavCount").textContent=m.learners_to_support;$("#notesNavCount").textContent=m.open_followups;$("#app").innerHTML=`
${heading("See the learning behind the code.","A class-wide view of learner mastery, momentum, and the next best teaching action.",`<button class="btn" data-action="new-note">＋ Team follow-up</button><button class="btn btn-primary" data-page="learners">Explore learners <span>→</span></button>`)}
<div class="overview-banner"><div class="banner-left"><div class="banner-symbol">✦</div><div><h2>Make the next lesson more targeted.</h2><p>${m.learners_to_support} learners may need attention · ${m.open_followups} teacher follow-ups remain open.</p></div></div><div class="banner-actions"><button class="btn btn-soft" data-page="insights">View class insights →</button></div></div>
<div class="metric-grid">
${metricCard("Learners in view",m.students,"Across demo classes","♧","blue",`<span class="tag blue">Roster</span>`)}
${metricCard("Average concept mastery",percent(m.average_mastery),"Average of learner concept scores","⌁","",`<span class="up">Learning signal</span>`)}
${metricCard("Assignment completion",percent(m.average_completion),"Average learner completion","✓","green",`<span class="up">Progress</span>`)}
${metricCard("Need a closer look",m.learners_to_support,"Watch or high-support signals","↗","purple",`<span class="${m.learners_to_support?'down':'up'}">${m.learners_to_support?'Action suggested':'On track'}</span>`)}
</div>
<div class="content-grid">
<section class="card card-pad"><div class="card-heading"><div><h3>Concept mastery map</h3><p>Which topics are landing — and which may need a different explanation?</p></div><span class="tag coral">Class signal</span></div>${conceptRows(d.concepts)}<div class="insight-summary"><span class="bulb">✳</span><div><strong>${conceptLowest?`${esc(conceptLowest.name)} is the best reteaching opportunity`:"Insights will appear here"}</strong><p>${conceptLowest?`Current average is ${conceptLowest.score}%. Try a worked example, then a short low-stakes practice activity.`:"Add assessment data to surface concept-level recommendations."}</p></div></div></section>
<section class="card card-pad"><div class="card-heading"><div><h3>Priority learner queue</h3><p>Signals to guide a supportive check-in, not a student label.</p></div><button class="btn-text" data-page="learners">All learners →</button></div>${support.length?`<div class="data-list">${support.slice(0,5).map(s=>`<div class="data-row support-row" data-action="student-detail" data-id="${s.id}"><div class="person-avatar ${avatarClass(s.name)}">${initials(s.name)}</div><div class="row-copy"><strong>${esc(s.name)}</strong><small>${esc(s.class_name)} · ${s.mastery_delta>0?'+':''}${s.mastery_delta} pts mastery change</small></div><div class="row-end">${riskTag(s.risk)}<span class="row-arrow">›</span></div></div>`).join("")}</div>`:`<div class="empty-state"><div class="empty-icon">✓</div><h3>Everyone is on track</h3><p>No learners currently meet the support thresholds.</p></div>`}</section>
</div>
<div class="content-grid">
<section class="card card-pad"><div class="card-heading"><div><h3>Teaching action plan</h3><p>Turn data into a practical next step.</p></div><button class="btn-text" data-page="insights">All insights →</button></div>${recommendationItems(d.recommendations)}</section>
<section class="card card-pad"><div class="card-heading"><div><h3>Recent student work</h3><p>Latest demo submissions and review status.</p></div><button class="btn-text" data-page="assignments">Assignments →</button></div>${recentSubmissionRows(d.recent_submissions)}</section>
</div><p class="data-footnote">All learner names, scores, submissions and collaboration items in this standalone pilot are fictional sample data. The support queue uses transparent demo rules based on mastery, recent mastery movement and inactivity; it is a prompt for teacher review, not an automated judgement.</p>`;}

function renderLearners(){const items=state.students;$("#app").innerHTML=`${heading("Learner intelligence","Understand the learner behind the score: concept mastery, progress momentum, completion, and the next teaching move.",`<button class="btn" data-action="export-learners">↓ Export view</button>`)}
<section class="card card-pad"><div class="table-toolbar"><label class="searchbox"><span>⌕</span><input id="studentSearch" type="search" value="${esc(state.studentSearch)}" placeholder="Search learner or class…"></label><div class="filter-group">${[["all","All learners"],["high","Needs support"],["watch","Watch"],["on_track","On track"]].map(([key,label])=>`<button class="filter-button ${state.studentFilter===key?'active':''}" data-action="student-filter" data-value="${key}">${label}</button>`).join("")}</div></div>
<div class="table-wrap"><table class="data-table"><thead><tr><th>Learner</th><th>Mastery</th><th>Change</th><th>Completion</th><th>Support signal</th><th>Recent activity</th><th></th></tr></thead><tbody>${items.map(studentRow).join("")||`<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">⌕</div><h3>No learners match</h3><p>Try a different name or filter.</p></div></td></tr>`}</tbody></table></div><div class="data-footnote">Support signal is a review aid based on demo thresholds. It is not a diagnosis or a permanent label.</div></section>`;
const input=$("#studentSearch");let timer;input?.addEventListener("input",()=>{clearTimeout(timer);timer=setTimeout(async()=>{state.studentSearch=input.value;const d=await api(`/api/students?risk=${encodeURIComponent(state.studentFilter)}&search=${encodeURIComponent(state.studentSearch)}`);state.students=d.items;renderLearners();const again=$("#studentSearch");if(again){again.focus();again.setSelectionRange(again.value.length,again.value.length);}},180)});}

function renderInsights(){const d=state.overview;const trend=(state.students||[]).slice().sort((a,b)=>a.mastery-b.mastery);const moves=[...state.students].sort((a,b)=>a.mastery_delta-b.mastery_delta).slice(0,5);const notes=state.notes.filter(n=>n.status!="resolved");$("#app").innerHTML=`${heading("Turn learning signals into teaching moves.","A decision-support view for lesson planning, differentiated practice, and teacher handoffs.",`<button class="btn btn-primary" data-action="new-note">＋ Create action</button>`)}
<div class="metric-grid">${metricCard("Concepts below 70%",d.concepts.filter(x=>x.score<70).length,"Possible reteaching opportunities","⌁","purple",`<span>Concept view</span>`)}${metricCard("Learners trending down",state.students.filter(x=>x.mastery_delta<0).length,"Mastery movement in sample profile","↘","",`<span class="down">Review context</span>`)}${metricCard("Open follow-ups",notes.length,"Shared teacher actions","▤","blue",`<span>Collaboration</span>`)}${metricCard("Recent submissions",d.metrics.submissions_7d,"Last 7 days in sample data","✓","green",`<span>Engagement signal</span>`)}</div>
<div class="content-grid equal"><section class="card card-pad"><div class="card-heading"><div><h3>Concepts to reinforce</h3><p>Lower average concept scores appear first.</p></div><span class="tag amber">Teaching opportunities</span></div>${conceptRows(d.concepts)}<div class="insight-summary"><span class="bulb">✳</span><div><strong>Try a targeted intervention</strong><p>Use a short worked example, a misconception check, and one independent retry. Compare performance on a subsequent task to see whether the adjustment helped.</p></div></div></section>
<section class="card card-pad"><div class="card-heading"><div><h3>Mastery movement to review</h3><p>Movement is a clue to investigate, not a causal explanation.</p></div><span class="tag coral">Teacher review</span></div><div class="data-list">${moves.map(s=>`<div class="data-row"><div class="person-avatar ${avatarClass(s.name)}">${initials(s.name)}</div><div class="row-copy"><strong>${esc(s.name)}</strong><small>${esc(s.class_name)} · ${s.mastery}% mastery</small></div><div class="row-end"><strong style="color:${s.mastery_delta<0?'var(--red)':'var(--green)'}">${s.mastery_delta>0?'+':''}${s.mastery_delta}</strong><button class="table-link" data-action="student-detail" data-id="${s.id}">Review</button></div></div>`).join("")}</div></section></div>
<div class="content-grid equal"><section class="card card-pad"><div class="card-heading"><div><h3>Suggested next moves</h3><p>Actions are intentionally small enough to try next class.</p></div></div>${recommendationItems(d.recommendations)}</section><section class="card card-pad"><div class="card-heading"><div><h3>Teacher handoffs</h3><p>Keep cross-teacher follow-ups explicit and owned.</p></div><button class="btn-text" data-page="collaboration">Open hub →</button></div>${notes.length?`<div class="data-list">${notes.slice(0,5).map(n=>`<div class="data-row"><div class="action-symbol">▤</div><div class="row-copy"><strong>${esc(n.title)}</strong><small>Owner: ${esc(n.owner)} · Due ${esc(n.due_date||'not set')}</small></div>${statusTag(n.status)}</div>`).join("")}</div>`:`<div class="empty-state"><div class="empty-icon">✓</div><h3>No open handoffs</h3><p>Create a shared action if a learner needs coordinated support.</p></div>`}</section></div>
<p class="data-footnote">The recommendation rules are transparent and deliberately simple. Production use should validate measures against curriculum rubrics and teacher judgement; do not use these signals alone for high-stakes decisions.</p>`;}

function renderCollaboration(){const notes=state.notes;const selected=notes.find(n=>n.id===state.selectedNoteId);$("#notesNavCount").textContent=notes.filter(n=>n.status!=="resolved").length;$("#app").innerHTML=`${heading("A shared place to follow through.","Make instructional handoffs visible: what was noticed, who owns the next step, and what happened after.",`<button class="btn btn-primary" data-action="new-note">＋ New follow-up</button>`)}
<div class="collab-layout"><section><div class="table-toolbar"><div class="filter-group">${[["all","All"],["open","Open"],["in_progress","In progress"],["resolved","Resolved"]].map(([v,label])=>`<button class="filter-button ${state.noteFilter===v?'active':''}" data-action="note-filter" data-value="${v}">${label}</button>`).join("")}</div><span class="soft-label">${notes.length} items</span></div><div class="followup-list">${notes.map(n=>`<button class="followup-card ${n.id===state.selectedNoteId?'active':''}" data-action="select-note" data-id="${n.id}"><div class="followup-top"><h3>${esc(n.title)}</h3>${priorityTag(n.priority)}</div><p>${esc(n.body)}</p><div class="followup-meta"><span>${esc(n.owner)} · Due ${esc(n.due_date||'not set')}</span>${statusTag(n.status)}</div></button>`).join("")||`<section class="card empty-state"><div class="empty-icon">▤</div><h3>No follow-ups in this view</h3><p>Change the filter or create a new teacher action.</p></section>`}</div></section>
<section class="card card-pad note-detail">${selected?noteDetail(selected):`<div class="empty-state"><div class="empty-icon">▤</div><h3>Select a follow-up</h3><p>Pick an item to review its context, add a comment, or update the owner and status.</p><button class="btn btn-primary" data-action="new-note">Create follow-up</button></div>`}</section></div>
<p class="data-footnote">Collaboration items persist in the local database. Because this standalone version has no authentication or network sharing, they are not shared with other teachers on other machines yet.</p>`;}
function noteDetail(n){const student=state.students.find(s=>s.id===n.student_id);return `<div class="note-detail-head"><div class="followup-top"><div class="eyebrow">Teacher follow-up #${n.id}</div><div style="display:flex;gap:6px">${priorityTag(n.priority)}${statusTag(n.status)}</div></div><h2>${esc(n.title)}</h2><p>${student?`Learner: ${esc(student.name)} · `:''}${esc(n.class_name)} · Created ${prettyDate(n.created_at)} by ${esc(n.author)}</p></div><div class="note-body">${esc(n.body||'No context supplied.').replace(/\n/g,'<br>')}</div>
<div class="note-meta-grid"><div><small>Assigned owner</small><strong>${esc(n.owner)}</strong></div><div><small>Due date</small><strong>${esc(n.due_date||'Not set')}</strong></div><div><small>Next step</small><strong>${n.status==='resolved'?'Documented as resolved':n.status==='in_progress'?'In progress':'Needs follow-through'}</strong></div></div>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:13px"><button class="btn btn-sm" data-action="edit-note" data-id="${n.id}">Edit details</button>${n.status!=='in_progress'?`<button class="btn btn-sm" data-action="note-status" data-id="${n.id}" data-status="in_progress">Mark in progress</button>`:''}${n.status!=='resolved'?`<button class="btn btn-sm btn-primary" data-action="note-status" data-id="${n.id}" data-status="resolved">Mark resolved ✓</button>`:`<button class="btn btn-sm" data-action="note-status" data-id="${n.id}" data-status="open">Reopen</button>`}</div>
<div class="comments-section"><div class="card-heading"><div><h3>Teacher discussion</h3><p>Keep decisions and context alongside the action.</p></div><span class="tag">${n.comments?.length||0} comments</span></div>${(n.comments||[]).map(c=>`<div class="comment-row"><div class="person-avatar ${avatarClass(c.author)}">${initials(c.author)}</div><div class="comment-body"><strong>${esc(c.author)}</strong><small>${prettyDate(c.created_at)}</small><p>${esc(c.body)}</p></div></div>`).join('')||`<p class="soft-label">No discussion yet. Add the first handoff note below.</p>`}<form class="comment-form" id="commentForm" data-note-id="${n.id}"><input name="body" placeholder="Add an update or teacher comment…" required maxlength="3000"><button class="btn btn-primary btn-sm" type="submit">Post</button></form></div>`;}

function renderAssignments(){const items=state.assignments.filter(a=>state.assignmentFilter==='all'||a.status===state.assignmentFilter);$("#app").innerHTML=`${heading("Assignments with learning evidence.","Create structured practice and review completion, scores, and patterns that can inform the next lesson.",`<button class="btn btn-primary" data-action="new-assignment">＋ Create assignment</button>`)}
<div class="table-toolbar"><div class="filter-group">${[["all","All assignments"],["active","Active"],["review","Needs review"],["archived","Archived"]].map(([v,label])=>`<button class="filter-button ${state.assignmentFilter===v?'active':''}" data-action="assignment-filter" data-value="${v}">${label}</button>`).join("")}</div><span class="soft-label">${items.length} assignments</span></div>
<div class="assignment-grid">${items.map(a=>`<section class="card assignment-card"><div class="assignment-card-top"><div class="assignment-icon">${iconForLanguage(a.language)}</div><div style="flex:1;min-width:0"><h3>${esc(a.title)}</h3><p>${esc(a.description||'No instructions added.')}</p></div>${statusTag(a.status)}</div><div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px"><span class="tag">${esc(a.language)}</span><span class="tag">${esc(a.class_name)}</span><span class="tag">Due ${esc(a.due_date||'not set')}</span></div><div class="assignment-progress"><div class="assignment-progress-label"><strong>${a.completion}% submitted</strong><span>${a.submission_count} of ${a.student_count} learners</span></div><div class="progress-track"><div class="progress-fill ${a.completion>=80?'good':''}" style="width:${a.completion}%"></div></div></div><div class="assignment-card-footer"><small>${a.average_score===null?'No scored submissions':`Average score ${a.average_score}%`} · Created ${prettyDate(a.created_at)}</small><div style="display:flex;gap:5px">${a.status==='active'?`<button class="btn btn-sm" data-action="assignment-status" data-id="${a.id}" data-status="review">Review</button>`:''}${a.status!=='archived'?`<button class="btn btn-sm" data-action="assignment-status" data-id="${a.id}" data-status="archived">Archive</button>`:`<button class="btn btn-sm" data-action="assignment-status" data-id="${a.id}" data-status="active">Restore</button>`}</div></div>${a.submissions?.length?`<details style="margin-top:12px"><summary style="font-size:10px;color:#d34d42;cursor:pointer;font-weight:700">Review submissions (${a.submissions.length})</summary><div class="table-wrap" style="margin-top:10px"><table class="data-table" style="min-width:350px"><thead><tr><th>Learner</th><th>Score</th><th>Status</th></tr></thead><tbody>${a.submissions.map(s=>`<tr><td>${esc(s.student)}</td><td>${s.score}%</td><td>${statusTag(s.status)}</td></tr>`).join('')}</tbody></table></div></details>`:''}</section>`).join('')||`<section class="card empty-state" style="grid-column:1/-1"><div class="empty-icon">☷</div><h3>No assignments in this filter</h3><p>Create a task or select a different status filter.</p><button class="btn btn-primary" data-action="new-assignment">Create assignment</button></section>`}</div>
<p class="data-footnote">Assignment records and submission summaries are persisted in the local database. Live student submission capture and rubric-based grading need a production identity and classroom integration.</p>`;}

async function loadWorkspace(){
  state.projects=(await api('/api/projects')).items;
  if(!state.projects.length){
    const p=await api('/api/projects',{method:'POST',body:{title:'Loops & Patterns Lab',language:'Python',class_name:'Python Foundations'}});
    state.projects=[p];
  }
  if(!state.currentProjectId||!state.projects.some(p=>p.id===state.currentProjectId)) state.currentProjectId=state.projects[0].id;
  const proj=state.projects.find(p=>p.id===state.currentProjectId);
  state.currentLanguage=proj.language;
  const files=(await api(`/api/projects/${proj.id}/files`)).items;
  if(!files.some(f=>f.name===state.currentFile)) state.currentFile=files[0]?.name||Object.keys(starterFiles[state.currentLanguage]||{})[0];
  state.projectFiles=files;
  if(!state.arenaTemplates?.length){
    try{
      const tmpl = await api('/api/arena/templates');
      state.arenaTemplates = tmpl.items || [];
    }catch(e){ state.arenaTemplates = []; }
  }
}

async function loadEditorFile(name){
  state.currentFile=name;
  const data=await api(`/api/projects/${state.currentProjectId}/files/${encodeURIComponent(name)}`);
  const e=$("#codeEditor");
  if(e)e.value=data.content;
  const status=$("#saveStatus");
  if(status)status.textContent='Saved to local project';
  $$('.editor-tab').forEach(b=>b.classList.toggle('active',b.dataset.file===name));
  $$('.file-row').forEach(b=>b.classList.toggle('active',b.dataset.file===name));
  const fname=$("#editorFilename");
  if(fname)fname.textContent=name;
}

function stopActiveAnimations(){
  if(state.turtleState.animId){ cancelAnimationFrame(state.turtleState.animId); state.turtleState.animId=null; }
  state.turtleState.isPlaying=false;
  if(state.pygameState.animId){ cancelAnimationFrame(state.pygameState.animId); state.pygameState.animId=null; }
  state.pygameState.isPlaying=false;
  if(state.pygameKeyHandler){
    window.removeEventListener('keydown', state.pygameKeyHandler);
    window.removeEventListener('keyup', state.pygameKeyUpHandler);
    state.pygameKeyHandler = null;
    state.pygameKeyUpHandler = null;
  }
}

function renderArenaTabContent(){
  if(state.arenaTab==='console'){
    return `
      <div class="stdin-bar">
        <span class="stdin-label">STDIN ▸</span>
        <input id="stdinInput" value="${esc(state.stdinValue||'')}" placeholder="Type input for program (e.g. for input())...">
        <button class="btn btn-sm" type="button" data-action="send-stdin">Send & Run</button>
      </div>
      <div id="runOutput" style="white-space:pre-wrap;font-family:'SFMono-Regular',Consolas,monospace;padding:14px 16px;color:#d5d9e2;font-size:12px;line-height:1.6;overflow-y:auto;max-height:360px">${esc(state.consoleOutput||'Ready. Run the current program to inspect output and errors.')}</div>
    `;
  } else {
    return `<div id="guiViewportRoot" class="gui-viewport">${renderGuiViewportContent()}</div>`;
  }
}

function renderGuiViewportContent(){
  const run = state.latestRun;
  const payload = run?.gui_payload;
  if(!payload){
    return `
      <div class="empty-state" style="padding:48px 16px;background:#12141a;color:#858b95">
        <div class="empty-icon" style="background:#1e222c;color:#f45b4f">❖</div>
        <h3 style="color:#f0f2f6">No visual output generated yet</h3>
        <p style="color:#9298a4">Run code using <strong>Turtle</strong>, <strong>Tkinter</strong>, or <strong>Pygame</strong>, or select a starter template from the dropdown above to view live graphics here.</p>
        <button class="btn btn-primary" data-action="load-template-sample">Load Turtle Spiral Star</button>
      </div>
    `;
  }

  if(payload.type==='turtle'){
    const w = payload.width || 600;
    const h = payload.height || 420;
    return `
      <div class="gui-toolbar">
        <div class="gui-toolbar-left">
          <span class="gui-badge">🐢 Turtle Canvas</span>
          <button class="btn btn-sm" id="btnTurtlePlay" data-action="turtle-toggle">${state.turtleState.isPlaying?'⏸ Pause':'▶ Play'}</button>
          <button class="btn btn-sm" data-action="turtle-instant">Instant view</button>
          <select id="turtleSpeed" class="pill-select" style="padding:4px 7px;font-size:10px">
            <option value="1" ${state.turtleState.speed===1?'selected':''}>Speed: 0.5x</option>
            <option value="2" ${state.turtleState.speed===2?'selected':''}>Speed: 1x</option>
            <option value="5" ${state.turtleState.speed===5?'selected':''}>Speed: 2x</option>
            <option value="15" ${state.turtleState.speed===15?'selected':''}>Speed: 5x</option>
            <option value="999" ${state.turtleState.speed===999?'selected':''}>Instant</option>
          </select>
          <button class="btn btn-sm" data-action="turtle-grid">${state.turtleState.showGrid?'Hide grid':'Show grid'}</button>
        </div>
        <div class="gui-toolbar-right">
          <span class="soft-label" id="turtleStepLabel">${(payload.actions||[]).length} steps</span>
          <button class="btn btn-sm" data-action="turtle-reset">↺ Reset</button>
          <button class="btn btn-sm" data-action="turtle-export">📥 PNG</button>
        </div>
      </div>
      <div class="gui-canvas-container">
        <canvas id="turtleCanvas" class="arena-canvas" width="${w}" height="${h}"></canvas>
      </div>
    `;
  }

  if(payload.type==='tkinter'){
    const title = payload.title || "Tkinter Application";
    const w = Math.min(payload.width || 380, 480);
    const h = payload.height || 280;
    return `
      <div class="gui-toolbar">
        <div class="gui-toolbar-left">
          <span class="gui-badge">🪟 Tkinter Desktop GUI</span>
          <span class="soft-label">${(payload.widgets||[]).length} widgets · Reactive state</span>
        </div>
        <div class="gui-toolbar-right">
          <button class="btn btn-sm" data-action="tkinter-reset">↺ Reset app</button>
        </div>
      </div>
      <div class="gui-canvas-container" style="padding:28px 16px">
        <div class="tkinter-window" style="max-width:${w}px">
          <div class="tkinter-head">
            <div class="tkinter-dots"><span class="tkinter-dot red"></span><span class="tkinter-dot yellow"></span><span class="tkinter-dot green"></span></div>
            <span class="tkinter-title">${esc(title)}</span>
          </div>
          <div class="tkinter-body" id="tkinterBody">
            ${renderTkinterWidgets(payload.widgets||[])}
            <div class="tkinter-log" id="tkinterLog">
              <div>[Tkinter Ready] Window initialized (${w}x${h})</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  if(payload.type==='pygame'){
    const w = payload.width || 480;
    const h = payload.height || 320;
    return `
      <div class="gui-toolbar">
        <div class="gui-toolbar-left">
          <span class="gui-badge">🎮 Pygame 2D Engine</span>
          <button class="btn btn-sm" id="btnPygamePlay" data-action="pygame-toggle">${state.pygameState.isPlaying?'⏸ Pause':'▶ Play'}</button>
          <button class="btn btn-sm" data-action="pygame-restart">↺ Restart</button>
          <span class="soft-label" style="color:#3cb775">● 60 FPS</span>
        </div>
        <div class="gui-toolbar-right">
          <span class="soft-label">⌨ Controls: ← → / A D or Space</span>
        </div>
      </div>
      <div class="gui-canvas-container">
        <canvas id="pygameCanvas" class="arena-canvas" width="${w}" height="${h}"></canvas>
      </div>
    `;
  }

  if(payload.type==='web'){
    return `
      <div class="gui-toolbar">
        <div class="gui-toolbar-left"><span class="gui-badge">🌐 Sandboxed Web Preview</span></div>
      </div>
      <div style="padding:14px;background:#12141a">
        <iframe class="preview-frame" sandbox="allow-scripts" title="Web Sandbox" srcdoc="${esc(payload.html||'')}"></iframe>
      </div>
    `;
  }

  return `<div class="empty-state"><p>Unknown visual GUI format.</p></div>`;
}

function renderTkinterWidgets(widgets){
  if(!widgets.length) return `<p class="muted">No widgets created in this window.</p>`;
  return widgets.map(w => {
    const p = w.props || {};
    if(w.type === 'label'){
      const isHeader = (p.font && String(p.font).includes('bold')) || (p.font && String(p.font).includes('16'));
      return `<div class="tkinter-widget tkinter-label" id="${w.id}" style="color:${esc(p.fg||'#222')};${isHeader?'font-size:16px;font-weight:bold;':''}">${esc(p.text||'')}</div>`;
    }
    if(w.type === 'button'){
      return `<button class="tkinter-btn" id="${w.id}" data-action="tkinter-btn-click" data-cmd="${esc(p.command_name||'')}" style="${p.bg?`background:${esc(p.bg)};`:''}${p.fg?`color:${esc(p.fg)};`:''}">${esc(p.text||'Button')}</button>`;
    }
    if(w.type === 'entry'){
      return `<input class="tkinter-entry" id="${w.id}" placeholder="${esc(p.placeholder||'Type here...')}" value="${esc(p.text||'')}">`;
    }
    if(w.type === 'frame'){
      return `<div class="tkinter-widget" id="${w.id}" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"></div>`;
    }
    if(w.type === 'canvas'){
      return `<canvas id="${w.id}" width="${p.width||300}" height="${p.height||150}" style="background:${esc(p.bg||'#f0f2f5')};border-radius:6px"></canvas>`;
    }
    return `<div class="tkinter-widget" id="${w.id}">${esc(p.text||w.type)}</div>`;
  }).join('');
}

function setupTurtlePlayback(payload){
  const canvas = $('#turtleCanvas');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  const actions = payload.actions || [];
  const w = canvas.width, h = canvas.height;
  const cx = w / 2, cy = h / 2;

  state.turtleState.currentStep = 0;
  state.turtleState.isPlaying = true;

  function toX(x){ return cx + x; }
  function toY(y){ return cy - y; }

  function renderFrame(){
    // Draw background
    ctx.fillStyle = payload.bg_color || '#ffffff';
    ctx.fillRect(0, 0, w, h);

    // Draw Grid if enabled
    if(state.turtleState.showGrid){
      ctx.strokeStyle = payload.bg_color && payload.bg_color.startsWith('#1') ? '#2e3444' : '#e6e9ef';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, cy); ctx.lineTo(w, cy);
      ctx.moveTo(cx, 0); ctx.lineTo(cx, h);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    let headX = 0, headY = 0, headAngle = 0, headColor = '#f45b4f', headVisible = true;

    // Draw executed actions
    const max = Math.min(state.turtleState.currentStep, actions.length);
    for(let i=0; i<max; i++){
      const act = actions[i];
      if(act.cmd === 'line'){
        ctx.strokeStyle = act.color || '#f45b4f';
        ctx.lineWidth = act.width || 2;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(toX(act.from[0]), toY(act.from[1]));
        ctx.lineTo(toX(act.to[0]), toY(act.to[1]));
        ctx.stroke();
        headX = act.to[0]; headY = act.to[1];
        headColor = act.color || headColor;
      } else if(act.cmd === 'fill_poly' && act.points){
        ctx.fillStyle = act.fillcolor || '#f45b4f';
        ctx.beginPath();
        act.points.forEach((pt, idx) => {
          if(idx===0) ctx.moveTo(toX(pt[0]), toY(pt[1]));
          else ctx.lineTo(toX(pt[0]), toY(pt[1]));
        });
        ctx.closePath();
        ctx.fill();
        if(act.width){
          ctx.strokeStyle = act.pencolor || '#f45b4f';
          ctx.lineWidth = act.width;
          ctx.stroke();
        }
      } else if(act.cmd === 'dot'){
        ctx.fillStyle = act.color || '#f45b4f';
        ctx.beginPath();
        ctx.arc(toX(act.x), toY(act.y), act.radius || 3, 0, Math.PI*2);
        ctx.fill();
        headX = act.x; headY = act.y;
      } else if(act.cmd === 'write'){
        ctx.fillStyle = act.color || '#f45b4f';
        ctx.font = act.font || '12px Arial';
        ctx.fillText(act.text, toX(act.x), toY(act.y));
      } else if(act.cmd === 'heading'){
        headAngle = act.angle;
      }
    }

    // Draw Turtle Cursor
    if(headVisible){
      ctx.save();
      ctx.translate(toX(headX), toY(headY));
      ctx.rotate(-headAngle * Math.PI / 180);
      ctx.fillStyle = headColor;
      ctx.beginPath();
      ctx.moveTo(9, 0);
      ctx.lineTo(-6, -6);
      ctx.lineTo(-3, 0);
      ctx.lineTo(-6, 6);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    const stepLabel = $('#turtleStepLabel');
    if(stepLabel) stepLabel.textContent = `${max} / ${actions.length} steps`;

    if(state.turtleState.isPlaying && state.turtleState.currentStep < actions.length){
      state.turtleState.currentStep = Math.min(actions.length, state.turtleState.currentStep + (state.turtleState.speed || 2));
      state.turtleState.animId = requestAnimationFrame(renderFrame);
    } else {
      state.turtleState.isPlaying = false;
      const btn = $('#btnTurtlePlay');
      if(btn) btn.textContent = '▶ Replay';
    }
  }

  stopActiveAnimations();
  state.turtleState.animId = requestAnimationFrame(renderFrame);

  $('#turtleSpeed')?.addEventListener('change', e => {
    state.turtleState.speed = Number(e.target.value);
    if(!state.turtleState.isPlaying && state.turtleState.currentStep < actions.length){
      state.turtleState.isPlaying = true;
      state.turtleState.animId = requestAnimationFrame(renderFrame);
    }
  });
}

function setupTkinterInteractivity(payload){
  state.tkinterState = { count: 0, greeting: "", logs: [] };
  const logEl = $('#tkinterLog');
  const countLabel = $$('.tkinter-label').find(el => el.textContent.includes('Points:') || el.textContent.includes('Score:'));
  const statusLabel = $$('.tkinter-label').find(el => el.textContent === '');
  const nameInput = $('.tkinter-entry');

  $$('.tkinter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.textContent.trim();
      let logMsg = `Clicked '${text}'`;

      if(text.includes('Add') || text.includes('Increment')){
        state.tkinterState.count++;
        if(countLabel) countLabel.textContent = `Points: ${state.tkinterState.count}`;
        logMsg = `[Event] Button '${text}' clicked -> Points: ${state.tkinterState.count}`;
      } else if(text.includes('Reset')){
        state.tkinterState.count = 0;
        if(countLabel) countLabel.textContent = `Points: 0`;
        logMsg = `[Event] Button '${text}' clicked -> Points reset to 0`;
      } else if(text.includes('Submit') || text.includes('Hello') || text.includes('Greet')){
        const val = nameInput?.value || "Learner";
        const msg = `Awesome coding, ${val}!`;
        if(statusLabel) statusLabel.textContent = msg;
        logMsg = `[Event] Greeting submitted -> '${msg}'`;
      }

      if(logEl){
        const row = document.createElement('div');
        row.textContent = `[${new Date().toLocaleTimeString()}] ${logMsg}`;
        logEl.appendChild(row);
        logEl.scrollTop = logEl.scrollHeight;
      }
      state.consoleOutput += `\n${logMsg}`;
    });
  });
}

function setupPygameEngine(payload){
  const canvas = $('#pygameCanvas');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;

  // Initialize Game State
  const stateGame = {
    paddleX: w / 2 - 45,
    paddleY: h - 30,
    paddleW: 90,
    paddleH: 12,
    ballX: w / 2,
    ballY: 80,
    dx: 3.5,
    dy: 3.0,
    radius: 12,
    score: 0,
    keys: {}
  };

  stopActiveAnimations();
  state.pygameState.isPlaying = true;

  state.pygameKeyHandler = e => {
    if(['ArrowLeft','ArrowRight','KeyA','KeyD','Space'].includes(e.code)) e.preventDefault();
    stateGame.keys[e.code] = true;
  };
  state.pygameKeyUpHandler = e => { stateGame.keys[e.code] = false; };
  window.addEventListener('keydown', state.pygameKeyHandler);
  window.addEventListener('keyup', state.pygameKeyUpHandler);

  function gameLoop(){
    // Controls update
    if(stateGame.keys['ArrowLeft'] || stateGame.keys['KeyA']) stateGame.paddleX = Math.max(10, stateGame.paddleX - 6);
    if(stateGame.keys['ArrowRight'] || stateGame.keys['KeyD']) stateGame.paddleX = Math.min(w - stateGame.paddleW - 10, stateGame.paddleX + 6);

    // Ball physics
    stateGame.ballX += stateGame.dx;
    stateGame.ballY += stateGame.dy;

    // Boundary bounces
    if(stateGame.ballX <= stateGame.radius + 10 || stateGame.ballX >= w - stateGame.radius - 10) stateGame.dx = -stateGame.dx;
    if(stateGame.ballY <= stateGame.radius + 10) stateGame.dy = -stateGame.dy;

    // Paddle bounce
    if(stateGame.ballY >= stateGame.paddleY - stateGame.radius &&
       stateGame.ballX >= stateGame.paddleX - 4 &&
       stateGame.ballX <= stateGame.paddleX + stateGame.paddleW + 4 &&
       stateGame.dy > 0){
      stateGame.dy = -stateGame.dy;
      stateGame.score++;
    } else if(stateGame.ballY >= h - stateGame.radius){
      // Reset ball
      stateGame.ballX = w / 2;
      stateGame.ballY = 80;
      stateGame.dy = Math.abs(stateGame.dy);
    }

    // Render 60 FPS
    ctx.fillStyle = '#171a22';
    ctx.fillRect(0, 0, w, h);

    // Border
    ctx.strokeStyle = '#3c74c9';
    ctx.lineWidth = 2;
    ctx.strokeRect(10, 10, w - 20, h - 20);

    // Paddle
    ctx.fillStyle = '#29945b';
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(stateGame.paddleX, stateGame.paddleY, stateGame.paddleW, stateGame.paddleH, 4) : ctx.rect(stateGame.paddleX, stateGame.paddleY, stateGame.paddleW, stateGame.paddleH);
    ctx.fill();

    // Ball
    ctx.fillStyle = '#f45b4f';
    ctx.beginPath();
    ctx.arc(stateGame.ballX, stateGame.ballY, stateGame.radius, 0, Math.PI*2);
    ctx.fill();

    // Score HUD
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText(`Score: ${stateGame.score}`, 24, 32);
    ctx.font = '10px sans-serif';
    ctx.fillStyle = '#8e96a4';
    ctx.fillText('Move paddle: [← / →] or [A / D]', w - 180, 32);

    if(state.pygameState.isPlaying){
      state.pygameState.animId = requestAnimationFrame(gameLoop);
    }
  }

  state.pygameState.animId = requestAnimationFrame(gameLoop);
}

function attachArenaOutputHandlers(){
  const run = state.latestRun;
  if(state.arenaTab === 'gui' && run?.gui_payload){
    if(run.gui_payload.type === 'turtle') setupTurtlePlayback(run.gui_payload);
    else if(run.gui_payload.type === 'tkinter') setupTkinterInteractivity(run.gui_payload);
    else if(run.gui_payload.type === 'pygame') setupPygameEngine(run.gui_payload);
  }
}

function renderWorkspaceOutput(){
  const container = $('#arenaOutputContainer');
  if(!container) return;
  container.innerHTML = renderArenaTabContent();
  attachArenaOutputHandlers();
  $$('.output-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === state.arenaTab));
  const dot = $('.gui-dot');
  if(dot) dot.classList.toggle('active', state.hasGui);
}

function showEditorsModal(){
  openModal('Standalone Sandboxed Editors & Runtimes','Evaluation and architecture guide for Codingal Code Studio',`
    <div style="display:grid;gap:12px">
      <div class="editor-card">
        <h4><span>1. CodeMirror 6</span><span class="editor-badge" style="background:#e6f8ee;color:#1e7e48">Top Pick for K-12</span></h4>
        <p><strong>Why it fits Codingal:</strong> Ultra-lightweight (&lt;120 KB), loads in milliseconds on low-end school Chromebooks and weak Wi-Fi. Native touch handling makes it unbeatable for elementary and middle school students coding on iPads and tablets.</p>
        <p><strong>Sandboxing:</strong> Minimal attack surface, pure functional state/dispatch architecture with zero external binary dependencies.</p>
      </div>

      <div class="editor-card">
        <h4><span>2. Monaco Editor (VS Code Engine)</span><span class="editor-badge">Top Pick for Secondary & Pro</span></h4>
        <p><strong>Why it fits Codingal:</strong> The exact same editor engine that powers VS Code. Provides built-in IntelliSense, AST inspection, syntax tree, minimap, and multi-file diffing.</p>
        <p><strong>Sandboxing:</strong> Tokenization and language services run inside isolated Web Workers, preventing editor freeze during large script parsing.</p>
      </div>

      <div class="editor-card">
        <h4><span>3. In-Browser Sandboxed Runtimes (Pyodide & Skulpt)</span><span class="editor-badge" style="background:#fff4e5;color:#9b5e14">Zero Server Cost</span></h4>
        <p><strong>Pyodide (WebAssembly CPython):</strong> Runs standard CPython 3, NumPy, and Pygame-CE 100% inside the browser Web Worker. Eliminates backend container costs and latency.</p>
        <p><strong>Skulpt:</strong> The educational gold-standard (powers Trinket, Repl.it, Runestone) for Python Turtle graphics and canvas animations.</p>
      </div>

      <div class="editor-card">
        <h4><span>4. Production Backend Sandboxes (Judge0 & Piston)</span><span class="editor-badge" style="background:#f2edff;color:#6b46c1">Backend Fleet</span></h4>
        <p><strong>Judge0 / Piston:</strong> Battle-tested multi-language execution engines with Linux cgroups, seccomp filters, dropped capabilities, and strict CPU/memory timeouts. Ideal backend when students run native Java, C++, and Go.</p>
        <p><strong>gVisor (runsc) / Firecracker:</strong> Production hypervisor and syscall isolation layers for untrusted multi-tenant code execution.</p>
      </div>
    </div>
    <div class="callout" style="margin-top:10px">
      <span>ⓘ</span>
      <div><strong>Current Architecture:</strong> This pilot uses a hybrid model: lightweight client-side 60 FPS Turtle, Tkinter, Pygame, and Web preview canvases, backed by isolated subprocess / Docker runners on the server.</div>
    </div>
  `,`<button class="btn btn-primary" data-action="close-modal">Got it</button>`);
}

async function renderWorkspace(){
  const projects=state.projects||[];
  const current=projects.find(p=>p.id===state.currentProjectId)||projects[0];
  const fileData=await api(`/api/projects/${current.id}/files/${encodeURIComponent(state.currentFile)}`).catch(async()=>{
    const f=state.projectFiles?.[0];
    if(f){state.currentFile=f.name;return api(`/api/projects/${current.id}/files/${encodeURIComponent(f.name)}`)}
    return {name:'main.py',content:''};
  });
  state.currentFile=fileData.name;
  const templates=state.arenaTemplates||[];

  $("#app").innerHTML=`${heading("The Coding Arena.","Write, debug, and run console programs or rich visual graphics (Turtle, Tkinter, Pygame, Canvas).",`
    <button class="btn" data-action="show-editors">✦ Standalone Editors</button>
    <button class="btn" data-action="new-project">＋ New project</button>
    <button class="btn btn-primary" data-action="commit">⎇ Save version</button>
  `)}
  <div class="integration-notice" style="margin-bottom:13px">
    <strong>Coding Arena:</strong> Interactive graphics (Turtle, Tkinter, Pygame) and standard Console execute in isolated sandboxes. Native Java and C++ use the optional Docker runner.
  </div>
  <div class="workspace-layout">
    <section class="editor-shell">
      <div class="editor-toolbar">
        <div class="editor-toolbar-left">
          <select id="projectSelect" aria-label="Choose project">
            ${projects.map(p=>`<option value="${p.id}" ${p.id===current.id?'selected':''}>${esc(p.title)}</option>`).join('')}
          </select>
          <select id="languageSelect" aria-label="Choose language">
            ${['Python','Java','C++','HTML/CSS/JS'].map(l=>`<option ${l===state.currentLanguage?'selected':''}>${l}</option>`).join('')}
          </select>
          <select id="arenaTemplateSelect" class="pill-select" aria-label="Load starter template">
            <option value="">✦ Starter templates…</option>
            ${templates.map(t=>`<option value="${t.id}">${t.icon} ${esc(t.title)}</option>`).join('')}
          </select>
        </div>
        <div class="editor-toolbar-right">
          <button class="btn" data-action="save-file">Save file</button>
          <button class="btn btn-primary" data-action="run-code">▶ Run</button>
        </div>
      </div>
      <div class="editor-tabs" id="editorTabs">
        ${(state.projectFiles||[]).map(f=>`<button class="editor-tab ${f.name===state.currentFile?'active':''}" data-action="open-file" data-file="${esc(f.name)}">${esc(f.name)}</button>`).join('')}
        <button class="editor-tab" data-action="new-file">＋ File</button>
      </div>
      <textarea class="code-editor" id="codeEditor" aria-label="Code editor" spellcheck="false">${esc(fileData.content)}</textarea>
      <div class="editor-footer">
        <span id="saveStatus">Saved to local project</span>
        <span>${esc(state.currentLanguage)} · UTF-8 · Spaces: 4</span>
        <span>Git-backed</span>
      </div>
      <section class="output-panel">
        <div class="output-head">
          <div class="output-head-tabs">
            <button class="output-tab ${state.arenaTab==='console'?'active':''}" data-action="switch-tab" data-tab="console">▤ Console</button>
            <button class="output-tab ${state.arenaTab==='gui'?'active':''}" data-action="switch-tab" data-tab="gui">
              ❖ GUI / Graphics <span class="gui-dot ${state.hasGui?'active':''}"></span>
            </button>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span id="runDuration" class="soft-label" style="color:#a0a7b2">${state.latestRun?.duration_ms ? `${state.latestRun.duration_ms} ms` : ''}</span>
            <button class="btn btn-sm" data-action="clear-output">Clear</button>
          </div>
        </div>
        <div class="output-body" id="arenaOutputContainer">
          ${renderArenaTabContent()}
        </div>
      </section>
    </section>
    <aside class="workspace-side">
      <section class="card side-card">
        <div class="card-heading"><h3>Project files</h3><span class="tag">${(state.projectFiles||[]).length} files</span></div>
        <div class="file-list">
          ${(state.projectFiles||[]).map(f=>`<button class="file-row ${f.name===state.currentFile?'active':''}" data-action="open-file" data-file="${esc(f.name)}"><span>${f.name.endsWith('.py')?'🐍':f.name.endsWith('.java')?'☕':f.name.endsWith('.cpp')?'⚙':f.name.endsWith('.html')?'◈':'▤'}</span>${esc(f.name)}<span>${f.size} B</span></button>`).join('')}
          <button class="file-row" data-action="new-file"><span>＋</span>Add file…</button>
        </div>
      </section>
      <section class="card side-card">
        <div class="card-heading"><h3>Project details</h3></div>
        <div class="side-detail"><span>Language</span><strong>${esc(current.language)}</strong></div>
        <div class="side-detail"><span>Class</span><strong>${esc(current.class_name)}</strong></div>
        <div class="side-detail"><span>Owner</span><strong>${esc(state.students.find(s=>s.id===current.owner_student_id)?.name||'Teacher workspace')}</strong></div>
        <div class="side-detail"><span>Updated</span><strong>${prettyDate(current.updated_at)}</strong></div>
        <button class="btn btn-sm" style="width:100%;margin-top:12px" data-page="versions">View Git history →</button>
      </section>
      <section class="card side-card">
        <div class="card-heading"><h3>Arena capabilities</h3></div>
        <div class="side-detail"><span>Console I/O</span><strong>Active (Stdin/Stdout)</strong></div>
        <div class="side-detail"><span>Turtle Canvas</span><strong>Vector Animator</strong></div>
        <div class="side-detail"><span>Tkinter GUI</span><strong>Simulated Reactive</strong></div>
        <div class="side-detail"><span>Pygame 2D</span><strong>60 FPS Game Loop</strong></div>
        <button class="btn btn-sm" style="width:100%;margin-top:12px" data-action="show-editors">Compare Standalone Editors →</button>
      </section>
      <section class="callout">
        <span>ⓘ</span>
        <div><strong>Safe execution</strong>Console outputs and GUI interactions run safely isolated. Toggle tabs anytime to inspect terminal logs or graphics.</div>
      </section>
    </aside>
  </div>
  <p class="data-footnote">The Coding Arena provides interactive execution with console and visual graphics telemetry. Git repository checkpointing records versions non-destructively.</p>`;

  const editor=$('#codeEditor');
  editor?.addEventListener('input',()=>{
    const el=$('#saveStatus');
    if(el)el.textContent='Unsaved changes';
    clearTimeout(state.editorTimer);
    state.editorTimer=setTimeout(()=>saveCurrentFile(true),900);
  });
  editor?.addEventListener('keydown',e=>{
    if(e.key==='Tab'){
      e.preventDefault();
      const a=editor.selectionStart,b=editor.selectionEnd;
      editor.setRangeText('    ',a,b,'end');
      editor.dispatchEvent(new Event('input'));
    }
  });

  attachArenaOutputHandlers();
}

async function saveCurrentFile(silent=false){
  const editor=$('#codeEditor');
  if(!editor)return;
  try{
    await api(`/api/projects/${state.currentProjectId}/files/${encodeURIComponent(state.currentFile)}`,{method:'PUT',body:{content:editor.value}});
    const status=$('#saveStatus');
    if(status)status.textContent='Saved to local project';
    if(!silent)toast('File saved to the local project.','success');
    return true;
  }catch(e){
    toast(`Save failed: ${e.message}`,'error');
    return false;
  }
}

async function runCurrentCode(){
  const editor=$('#codeEditor');
  if(!editor)return;
  await saveCurrentFile(true);
  const duration=$('#runDuration');
  const language=state.currentLanguage;
  const code=editor.value;
  const stdinVal=$('#stdinInput')?.value || state.stdinValue || '';

  if(language==='HTML/CSS/JS'){
    state.hasGui = true;
    state.latestRun = {
      status: "succeeded",
      mode: "gui",
      gui_target: "web",
      gui_payload: { type: "web", html: code },
      output: "HTML preview rendered in sandboxed iframe.",
      duration_ms: 0
    };
    state.consoleOutput = "HTML/CSS/JS preview rendered in sandboxed browser iframe.";
    state.arenaTab = "gui";
    renderWorkspaceOutput();
    if(duration) duration.textContent = 'Browser sandbox';
    toast('HTML preview rendered in sandboxed iframe.','success');
    return;
  }

  stopActiveAnimations();
  state.consoleOutput = 'Starting isolated execution in Coding Arena…';
  if(duration) duration.textContent = 'Queued…';
  renderWorkspaceOutput();

  try{
    const result = await api('/api/arena/run',{
      method:'POST',
      body:{
        language,
        code,
        stdin: stdinVal,
        project_id: state.currentProjectId,
        mode: "auto",
        gui_target: "auto"
      }
    });

    state.latestRun = result;
    state.consoleOutput = result.output || result.stdout || (result.status === 'succeeded' ? 'Program completed with no output.' : 'Execution failed.');

    if(result.gui_payload){
      state.hasGui = true;
      state.arenaTab = 'gui';
    }

    if(duration) duration.textContent = result.duration_ms ? `${result.duration_ms} ms` : (result.status === 'unavailable' ? 'Runner not configured' : result.status);

    renderWorkspaceOutput();

    if(result.status==='succeeded'){
      const modeLabel = result.gui_target && result.gui_target !== 'none' ? ` (${result.gui_target.toUpperCase()})` : '';
      toast(`Program completed successfully${modeLabel}.`,'success');
    } else if(result.status==='unavailable'){
      toast('Runner container not configured for this language.','error');
    } else {
      toast(`Execution ${result.status}.`,'');
    }
  }catch(e){
    state.consoleOutput = `Error: ${e.message}`;
    if(duration) duration.textContent = 'Error';
    renderWorkspaceOutput();
    toast(`Run failed: ${e.message}`,'error');
  }
}
async function renderVersions(){const project=state.projects.find(p=>p.id===state.currentProjectId)||state.projects[0];const data=await api(`/api/projects/${project.id}/versions`);state.versions=data.items;$("#app").innerHTML=`${heading("Every meaningful change, recoverable.","Git-backed commit history for the selected local project. Restores are recorded as new commits so prior history stays available.",`<button class="btn" data-page="workspace">← Back to workspace</button><button class="btn btn-primary" data-action="commit">⎇ Save version</button>`)}
<section class="card card-pad"><div class="card-heading"><div><h3>${esc(project.title)}</h3><p>${esc(project.language)} · ${esc(project.class_name)}</p></div><span class="tag purple">Git repository</span></div>${state.versions.length?`<div class="versions-list">${state.versions.map(v=>`<div class="version-row"><div class="version-glyph">⎇</div><div><strong>${esc(v.message)}</strong><small>${esc(v.author)} · ${prettyDate(v.date)} · ${esc(v.date?.replace('T',' ').replace('Z','')||'')}</small></div><div style="display:flex;align-items:center;gap:9px"><span class="hash">${esc(v.short_hash)}</span><button class="btn btn-sm" data-action="restore-version" data-hash="${esc(v.hash)}">Restore</button></div></div>`).join('')}</div>`:`<div class="empty-state"><div class="empty-icon">⎇</div><h3>No versions yet</h3><p>Save a version in the workspace to create the first checkpoint.</p><button class="btn btn-primary" data-page="workspace">Open workspace</button></div>`}</section><div class="callout" style="margin-top:13px"><span>ⓘ</span><div><strong>Safe restore behaviour</strong>Restoring a commit copies its project tree into the current working branch and creates a new commit; it does not hard-reset or erase later commit history.</div></div>`;}

function openModal(title,subtitle,body,buttons=''){const root=$('#modalRoot');root.innerHTML=`<div class="modal-backdrop" data-action="backdrop-close"><section class="modal" role="dialog" aria-modal="true" aria-label="${esc(title)}"><header class="modal-head"><div><h2>${esc(title)}</h2><p>${esc(subtitle)}</p></div><button type="button" class="modal-close" data-action="close-modal" aria-label="Close">×</button></header><div class="modal-body">${body}</div>${buttons?`<footer class="modal-foot">${buttons}</footer>`:''}</section></div>`;}
function closeModal(){$('#modalRoot').innerHTML='';}
async function showStudent(id){try{const s=await api(`/api/students/${id}`);state.currentStudent=s;openModal(s.name,`${s.grade} · ${s.class_name} · ${s.teacher}`,`
<div class="student-profile-top"><div class="person-avatar ${avatarClass(s.name)}">${initials(s.name)}</div><div style="flex:1"><h2>${esc(s.name)}</h2><p>${relativeDate(s.last_active)} · ${s.streak_days} day learning streak</p></div>${riskTag(s.risk)}</div><div class="profile-metrics"><div class="profile-metric"><small>Concept mastery</small><strong>${s.mastery}%</strong></div><div class="profile-metric"><small>Completion</small><strong>${s.completion}%</strong></div><div class="profile-metric"><small>Recent change</small><strong style="color:${s.mastery_delta<0?'var(--red)':'var(--green)'}">${s.mastery_delta>0?'+':''}${s.mastery_delta}</strong></div></div><div class="profile-layout"><div class="profile-section"><h3>Concept profile</h3>${conceptRows(Object.entries(s.concepts||{}).map(([name,score])=>({name,score})).sort((a,b)=>a.score-b.score))}</div><div class="profile-section"><h3>Recent assignments</h3>${s.submissions?.length?`<div class="data-list">${s.submissions.slice(0,5).map(x=>`<div class="data-row"><div class="row-copy"><strong>${esc(x.assignment)}</strong><small>${prettyDate(x.submitted_at)} · ${x.tests_passed}/${x.tests_total} checks</small></div><strong class="row-value">${Math.round(x.score)}%</strong></div>`).join('')}</div>`:`<p class="soft-label">No submissions yet.</p>`}</div></div><div class="profile-section" style="margin-top:13px"><div class="card-heading"><h3>Teacher follow-ups</h3><button class="btn-text" data-action="new-note-for-student" data-id="${s.id}">＋ Add follow-up</button></div>${s.notes?.length?s.notes.map(n=>`<div class="data-row"><div class="row-copy"><strong>${esc(n.title)}</strong><small>${esc(n.owner)} · ${statusTag(n.status)}</small></div><button class="table-link" data-action="open-collab-note" data-id="${n.id}">Open</button></div>`).join(''):`<p class="soft-label">No teacher follow-ups recorded for this learner.</p>`}</div><p class="data-footnote">Sample learner profile. Use context and teacher judgement before acting on analytics.</p>`,`<button class="btn" data-action="close-modal">Close</button><button class="btn btn-primary" data-action="new-note-for-student" data-id="${s.id}">＋ Create follow-up</button>`); }catch(e){toast(e.message,'error');}}
function noteForm(note=null, studentId=null){const editing=!!note;const students=state.students?.length?state.students:[];const selectedStudent=studentId??note?.student_id??'';const fields=`<form id="noteForm" data-edit-id="${note?.id||''}"><div class="form-grid"><div class="field full"><label for="noteTitle">Follow-up title *</label><input id="noteTitle" name="title" required maxlength="200" value="${esc(note?.title||'')}" placeholder="e.g. Revisit loops with a worked example"></div><div class="field full"><label for="noteBody">Context and suggested next step</label><textarea id="noteBody" name="body" maxlength="6000" placeholder="What did you notice? What action should the teacher try next?">${esc(note?.body||'')}</textarea></div><div class="field"><label for="noteStudent">Linked learner</label><select id="noteStudent" name="student_id"><option value="">Class-level follow-up</option>${students.map(s=>`<option value="${s.id}" ${String(selectedStudent)===String(s.id)?'selected':''}>${esc(s.name)}</option>`).join('')}</select></div><div class="field"><label for="noteClass">Class</label><select id="noteClass" name="class_name"><option>Python Foundations</option><option>Creative Coding</option></select></div><div class="field"><label for="noteOwner">Assigned teacher</label><select id="noteOwner" name="owner">${['Priya Sharma','Rahul Verma','Anika Rao','Unassigned'].map(x=>`<option ${x===(note?.owner||'Priya Sharma')?'selected':''}>${x}</option>`).join('')}</select></div><div class="field"><label for="notePriority">Priority</label><select id="notePriority" name="priority">${['low','medium','high','urgent'].map(x=>`<option value="${x}" ${x===(note?.priority||'medium')?'selected':''}>${x[0].toUpperCase()+x.slice(1)}</option>`).join('')}</select></div><div class="field"><label for="noteDue">Target date</label><input id="noteDue" name="due_date" type="date" value="${esc(note?.due_date||'')}"></div></div></form>`;openModal(editing?'Edit follow-up':'Create teacher follow-up',editing?'Update the owner, context or next step.':'Capture an actionable teaching handoff that a colleague can pick up.',fields,`<button class="btn" data-action="close-modal">Cancel</button><button class="btn btn-primary" data-action="submit-note">${editing?'Save changes':'Create follow-up'}</button>`);}
function assignmentForm(){const body=`<form id="assignmentForm"><div class="form-grid"><div class="field full"><label for="assTitle">Assignment title *</label><input id="assTitle" name="title" required maxlength="200" placeholder="e.g. Debug the Robot"></div><div class="field"><label for="assLanguage">Language</label><select id="assLanguage" name="language">${['Python','Java','C++','HTML/CSS/JS'].map(l=>`<option>${l}</option>`).join('')}</select></div><div class="field"><label for="assClass">Class</label><select id="assClass" name="class_name"><option>Python Foundations</option><option>Creative Coding</option></select></div><div class="field"><label for="assDue">Due date</label><input id="assDue" name="due_date" type="date"></div><div class="field"><label for="assOwner">Created by</label><select id="assOwner" name="created_by"><option>Priya Sharma</option><option>Rahul Verma</option><option>Anika Rao</option></select></div><div class="field full"><label for="assDesc">Instructions and learning objective</label><textarea id="assDesc" name="description" maxlength="3000" placeholder="What should the learner practise, and what does success look like?"></textarea></div></div></form>`;openModal('Create assignment','Write a clear task with an observable learning outcome.',body,`<button class="btn" data-action="close-modal">Cancel</button><button class="btn btn-primary" data-action="submit-assignment">Create assignment</button>`);}
function projectForm(){const body=`<form id="projectForm"><div class="form-grid"><div class="field full"><label for="projectTitle">Project name *</label><input id="projectTitle" name="title" required maxlength="200" placeholder="e.g. Loops & Patterns Lab"></div><div class="field"><label for="projectLanguage">Starter language</label><select id="projectLanguage" name="language">${['Python','Java','C++','HTML/CSS/JS'].map(l=>`<option>${l}</option>`).join('')}</select></div><div class="field"><label for="projectClass">Class</label><select id="projectClass" name="class_name"><option>Python Foundations</option><option>Creative Coding</option></select></div><div class="field full"><label for="projectOwner">Link learner (optional)</label><select id="projectOwner" name="owner_student_id"><option value="">Teacher workspace</option>${state.students.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select></div></div></form>`;openModal('Create coding project','A new local Git repository will be created with a runnable starter file.',body,`<button class="btn" data-action="close-modal">Cancel</button><button class="btn btn-primary" data-action="submit-project">Create project</button>`);}
function aboutModal(){openModal('About this standalone pilot','A locally runnable product prototype with a real local database and Git repository storage.',`<div class="data-list"><div class="data-row"><div class="action-symbol blue">DB</div><div class="row-copy"><strong>Persistent local data</strong><small>SQLite stores demo learners, assignments, follow-ups, comments and run metadata.</small></div></div><div class="data-row"><div class="action-symbol">⎇</div><div class="row-copy"><strong>Real local Git</strong><small>Each project is stored in a local Git repository. Save version and restore use Git commits.</small></div></div><div class="data-row"><div class="action-symbol red">⚙</div><div class="row-copy"><strong>Isolated execution</strong><small>Python, Java and C++ use a Docker runner if installed and built; otherwise nothing is executed. HTML preview runs in a sandboxed iframe.</small></div></div><div class="data-row"><div class="action-symbol blue">ⓘ</div><div class="row-copy"><strong>Not connected to Codingal production</strong><small>Demo learner identities and scores are fictional. There is no production authentication or shared multi-user collaboration.</small></div></div></div><div class="integration-notice" style="margin-top:14px">Do not expose this local pilot publicly. Production release requires authentication, role-based access controls, hardened runner isolation, deployment security and privacy review.</div>`,`<button class="btn btn-primary" data-action="close-modal">Got it</button>`);}

async function handleClick(e){const page=e.target.closest('[data-page]');if(page){if(state.page==='workspace' && page.dataset.page!=='workspace' && $('#codeEditor'))await saveCurrentFile(true);navigate(page.dataset.page);return;}const el=e.target.closest('[data-action]');if(!el)return;const action=el.dataset.action;try{
if(action==='close-modal'||action==='backdrop-close'){if(action==='backdrop-close'&&e.target!==el)return;closeModal();return;}
if(action==='retry'){navigate(state.page);return;}
if(action==='student-detail'){showStudent(Number(el.dataset.id));return;}
if(action==='student-filter'){state.studentFilter=el.dataset.value;const d=await api(`/api/students?risk=${encodeURIComponent(state.studentFilter)}&search=${encodeURIComponent(state.studentSearch)}`);state.students=d.items;renderLearners();return;}
if(action==='export-learners'){const csv=[['Name','Grade','Class','Mastery','Mastery delta','Completion','Support signal','Last active'],...state.students.map(s=>[s.name,s.grade,s.class_name,s.mastery,s.mastery_delta,s.completion,s.risk,s.last_active])].map(row=>row.map(x=>`"${String(x??'').replaceAll('"','""')}"`).join(',')).join('\n');downloadText('codingal-learner-view.csv',csv,'text/csv');toast('Learner view exported as CSV.','success');return;}
if(action==='new-note'){if(!state.students.length)state.students=(await api('/api/students')).items;noteForm();return;}
if(action==='new-note-for-student'){const id=Number(el.dataset.id);closeModal();if(!state.students.length)state.students=(await api('/api/students')).items;noteForm(null,id);return;}
if(action==='edit-note'){const n=state.notes.find(n=>n.id===Number(el.dataset.id))||await api(`/api/notes?status=all`).then(d=>d.items.find(n=>n.id===Number(el.dataset.id)));if(n){if(!state.students.length)state.students=(await api('/api/students')).items;noteForm(n);}return;}
if(action==='submit-note'){const form=$('#noteForm');if(!form.reportValidity())return;const fd=new FormData(form);const student=fd.get('student_id');const payload={title:fd.get('title'),body:fd.get('body'),student_id:student?Number(student):null,class_name:fd.get('class_name'),owner:fd.get('owner'),priority:fd.get('priority'),due_date:fd.get('due_date'),author:'Priya Sharma'};const editId=form.dataset.editId;if(editId)await api(`/api/notes/${editId}`,{method:'PATCH',body:payload});else await api('/api/notes',{method:'POST',body:payload});closeModal();toast(editId?'Follow-up updated.':'Follow-up created and saved.','success');await navigate(state.page);return;}
if(action==='note-filter'){state.noteFilter=el.dataset.value;state.notes=(await api(`/api/notes?status=${encodeURIComponent(state.noteFilter)}`)).items;if(!state.notes.some(n=>n.id===state.selectedNoteId))state.selectedNoteId=state.notes[0]?.id||null;renderCollaboration();return;}
if(action==='select-note'){state.selectedNoteId=Number(el.dataset.id);renderCollaboration();return;}
if(action==='note-status'){await api(`/api/notes/${el.dataset.id}`,{method:'PATCH',body:{status:el.dataset.status}});state.notes=(await api(`/api/notes?status=${encodeURIComponent(state.noteFilter)}`)).items;if(!state.notes.some(n=>n.id===state.selectedNoteId))state.selectedNoteId=state.notes[0]?.id||null;toast('Follow-up status updated.','success');renderCollaboration();return;}
if(action==='open-collab-note'){state.selectedNoteId=Number(el.dataset.id);closeModal();state.noteFilter='all';navigate('collaboration');return;}
if(action==='new-assignment'){assignmentForm();return;}
if(action==='submit-assignment'){const form=$('#assignmentForm');if(!form.reportValidity())return;const fd=new FormData(form);await api('/api/assignments',{method:'POST',body:Object.fromEntries(fd.entries())});closeModal();toast('Assignment created and saved.','success');state.assignments=(await api('/api/assignments')).items;renderAssignments();return;}
if(action==='assignment-filter'){state.assignmentFilter=el.dataset.value;renderAssignments();return;}
if(action==='assignment-status'){await api(`/api/assignments/${el.dataset.id}`,{method:'PATCH',body:{status:el.dataset.status}});state.assignments=(await api('/api/assignments')).items;toast('Assignment status updated.','success');renderAssignments();return;}
if(action==='new-project'){state.students=(await api('/api/students')).items;projectForm();return;}
if(action==='submit-project'){const form=$('#projectForm');if(!form.reportValidity())return;const fd=new FormData(form);const owner=fd.get('owner_student_id');const payload={title:fd.get('title'),language:fd.get('language'),class_name:fd.get('class_name'),owner_student_id:owner?Number(owner):null};const p=await api('/api/projects',{method:'POST',body:payload});closeModal();state.currentProjectId=p.id;state.currentFile=Object.keys(starterFiles[p.language])[0];toast('Git-backed project created.','success');await navigate('workspace');return;}
if(action==='save-file'){await saveCurrentFile(false);return;}
if(action==='commit'){await saveCurrentFile(true);const message=prompt('Name this version / commit:','Teacher checkpoint');if(message===null)return;if(message.trim().length<2){toast('Please enter a commit message of at least 2 characters.','error');return;}const result=await api(`/api/projects/${state.currentProjectId}/commit`,{method:'POST',body:{message:message.trim(),author:'Priya Sharma'}});if(result.unchanged){toast(result.message);return;}toast(`Version saved · ${result.short_hash}`,'success');if(state.page==='versions'){await renderVersions();}return;}
if(action==='open-file'){await saveCurrentFile(true);await loadEditorFile(el.dataset.file);return;}
if(action==='new-file'){const filename=prompt('New file name (letters, numbers, dots, hyphens and underscores):','notes.txt');if(filename===null)return;if(!/^[A-Za-z0-9_.-]{1,80}$/.test(filename)||filename.startsWith('.')||filename==='.git'||filename==='..'){toast('That filename is not allowed.','error');return;}await api(`/api/projects/${state.currentProjectId}/files/${encodeURIComponent(filename)}`,{method:'PUT',body:{content:''}});await loadWorkspace();renderWorkspace();await loadEditorFile(filename);toast('File added to the project.','success');return;}
if(action==='run-code'){await runCurrentCode();return;}
if(action==='switch-tab'){state.arenaTab=el.dataset.tab;renderWorkspaceOutput();return;}
if(action==='show-editors'){showEditorsModal();return;}
if(action==='send-stdin'){state.stdinValue=$('#stdinInput')?.value||'';await runCurrentCode();return;}
if(action==='load-template-sample'){
  const tmpl=(state.arenaTemplates||[]).find(t=>t.id==='python_turtle_star')||state.arenaTemplates?.[1];
  if(tmpl){
    const ed=$('#codeEditor');if(ed)ed.value=tmpl.code;
    state.currentLanguage=tmpl.language;
    const lSel=$('#languageSelect');if(lSel)lSel.value=tmpl.language;
    await saveCurrentFile(true);
    await runCurrentCode();
  }
  return;
}
if(action==='turtle-toggle'){
  state.turtleState.isPlaying=!state.turtleState.isPlaying;
  const btn=$('#btnTurtlePlay');
  if(btn)btn.textContent=state.turtleState.isPlaying?'⏸ Pause':'▶ Play';
  if(state.turtleState.isPlaying && state.latestRun?.gui_payload){
    setupTurtlePlayback(state.latestRun.gui_payload);
  }
  return;
}
if(action==='turtle-instant'){
  state.turtleState.speed=999;
  if(state.latestRun?.gui_payload){
    setupTurtlePlayback(state.latestRun.gui_payload);
  }
  return;
}
if(action==='turtle-grid'){
  state.turtleState.showGrid=!state.turtleState.showGrid;
  el.textContent=state.turtleState.showGrid?'Hide grid':'Show grid';
  if(state.latestRun?.gui_payload){
    setupTurtlePlayback(state.latestRun.gui_payload);
  }
  return;
}
if(action==='turtle-reset'){
  if(state.latestRun?.gui_payload){
    state.turtleState.currentStep=0;
    setupTurtlePlayback(state.latestRun.gui_payload);
  }
  return;
}
if(action==='turtle-export'){
  const c=$('#turtleCanvas');
  if(c){
    const a=document.createElement('a');
    a.download='codingal-turtle-art.png';
    a.href=c.toDataURL('image/png');
    a.click();
    toast('Turtle drawing exported as PNG.','success');
  }
  return;
}
if(action==='tkinter-reset'){
  state.tkinterState={count:0,greeting:"",logs:[]};
  if(state.latestRun?.gui_payload){
    renderWorkspaceOutput();
    toast('Tkinter application reset.','success');
  }
  return;
}
if(action==='pygame-toggle'){
  state.pygameState.isPlaying=!state.pygameState.isPlaying;
  const btn=$('#btnPygamePlay');
  if(btn)btn.textContent=state.pygameState.isPlaying?'⏸ Pause':'▶ Play';
  if(state.pygameState.isPlaying && state.latestRun?.gui_payload){
    setupPygameEngine(state.latestRun.gui_payload);
  }
  return;
}
if(action==='pygame-restart'){
  if(state.latestRun?.gui_payload){
    setupPygameEngine(state.latestRun.gui_payload);
    toast('Pygame game loop restarted.','success');
  }
  return;
}
if(action==='clear-output'){
  stopActiveAnimations();
  state.consoleOutput='Output cleared. Run the program to populate this panel.';
  state.latestRun=null;
  state.hasGui=false;
  renderWorkspaceOutput();
  const duration=$('#runDuration');if(duration)duration.textContent='';
  return;
}
if(action==='restore-version'){if(!confirm('Restore this commit as a new commit? Later history will be preserved.'))return;await api(`/api/projects/${state.currentProjectId}/restore`,{method:'POST',body:{commit_hash:el.dataset.hash,author:'Priya Sharma'}});toast('Snapshot restored as a new Git commit.','success');await loadWorkspace();await renderVersions();return;}
if(action==='help'){aboutModal();return;}
}catch(err){toast(err.message||'Something went wrong.','error');}}
function downloadText(filename,text,type){const blob=new Blob([text],{type});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;a.click();URL.revokeObjectURL(url);}

async function boot(){document.addEventListener('click',handleClick);$("#mobileMenu").addEventListener('click',()=>$("#sidebar").classList.toggle('mobile-open'));$("#helpButton").addEventListener('click',aboutModal);$("#profileButton").addEventListener('click',aboutModal);document.addEventListener('submit',async e=>{if(e.target.id==='commentForm'){e.preventDefault();const fd=new FormData(e.target);const body=String(fd.get('body')||'').trim();if(!body)return;await api(`/api/notes/${e.target.dataset.noteId}/comments`,{method:'POST',body:{author:'Priya Sharma',body}});state.notes=(await api(`/api/notes?status=${encodeURIComponent(state.noteFilter)}`)).items;toast('Comment added to the handoff.','success');renderCollaboration();}});
$("#app").addEventListener('change',async e=>{
  if(e.target.id==='projectSelect'){await saveCurrentFile(true);state.currentProjectId=Number(e.target.value);const p=state.projects.find(x=>x.id===state.currentProjectId);state.currentLanguage=p.language;state.currentFile=Object.keys(starterFiles[p.language])[0];await navigate('workspace');}
  if(e.target.id==='languageSelect'){const lang=e.target.value;await saveCurrentFile(true);const filename=Object.keys(starterFiles[lang])[0];const existing=(await api(`/api/projects/${state.currentProjectId}/files`)).items;if(!existing.some(f=>f.name===filename)){await api(`/api/projects/${state.currentProjectId}/files/${encodeURIComponent(filename)}`,{method:'PUT',body:{content:starterFiles[lang][filename]}});}state.currentLanguage=lang;state.currentFile=filename;state.projectFiles=(await api(`/api/projects/${state.currentProjectId}/files`)).items;renderWorkspace();}
  if(e.target.id==='arenaTemplateSelect'){
    const tmplId=e.target.value;
    if(!tmplId)return;
    const tmpl=(state.arenaTemplates||[]).find(t=>t.id===tmplId);
    if(!tmpl)return;
    const ed=$('#codeEditor');
    if(ed)ed.value=tmpl.code;
    state.currentLanguage=tmpl.language;
    const lSel=$('#languageSelect');
    if(lSel)lSel.value=tmpl.language;
    await saveCurrentFile(true);
    toast(`Loaded template: ${tmpl.title}`,'success');
    await runCurrentCode();
  }
});
try{const h=await api('/api/health');$('#serverStatus').textContent='API and database connected';$('#serverStatus').closest('.stack-status')?.querySelector('.status-led')?.style.setProperty('background','#3cb775');}catch(e){$('#serverStatus').textContent='Service unavailable';$('#serverStatus').closest('.stack-status')?.querySelector('.status-led')?.style.setProperty('background','#d24f4f');}
await navigate('overview');}
boot();
