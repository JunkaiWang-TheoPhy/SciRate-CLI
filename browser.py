"""Use a user's open Chrome/Safari SciRate tab without exporting cookies."""
import json
import subprocess
import sys
import re

def run_javascript(script, browser='Chrome'):
    if sys.platform != 'darwin':
        raise ValueError('browser_bridge_requires_macos')
    if browser == 'Chrome':
        apple = '''on run argv
tell application "Google Chrome"
repeat with w in windows
repeat with t in tabs of w
if URL of t starts with "https://scirate.com/" then
return execute t javascript (item 1 of argv)
end if
end repeat
end repeat
end tell
error "Open a SciRate tab in Chrome first"
end run'''
    elif browser == 'Safari':
        apple = '''on run argv
tell application "Safari"
repeat with w in windows
repeat with t in tabs of w
if URL of t starts with "https://scirate.com/" then
return do JavaScript (item 1 of argv) in t
end if
end repeat
end repeat
end tell
error "Open a SciRate tab in Safari first"
end run'''
    else:
        raise ValueError('unsupported_browser')
    result = subprocess.run(['osascript', '-e', apple, script], text=True, capture_output=True, timeout=20)
    if result.returncode:
        raise ValueError('browser_bridge_unavailable: ' + result.stderr.strip())
    return result.stdout.strip()

def snapshot(browser='Chrome'):
    result = json.loads(run_javascript('JSON.stringify({url:location.href,html:document.documentElement.outerHTML})', browser))
    if not result['url'].startswith('https://scirate.com/'):
        raise ValueError('unexpected_browser_origin')
    return result

def status(browser='Chrome'):
    return json.loads(run_javascript('JSON.stringify({url:location.href,logged_in:!!document.querySelector("a[href=\\"/logout\\"]"),challenge:!!document.querySelector("#challenge-running") || document.title.includes("Just a moment")})', browser))

def action(name, target, content=None, browser='Chrome'):
    """Start one requested official operation and return an asynchronous ticket."""
    paths = {'scite': '/api/scite/', 'unscite': '/api/unscite/', 'subscribe': '/api/subscribe/', 'unsubscribe': '/api/unsubscribe/', 'reply': '/comments/', 'comment': '/comments'}
    if name not in paths:
        raise ValueError('unsupported_action')
    if name in ('scite', 'unscite', 'comment'):
        from scirate import ID
        if not ID.fullmatch(str(target)):
            raise ValueError('invalid_arxiv_id')
    if name in ('subscribe', 'unsubscribe') and not re.fullmatch(r'[A-Za-z][A-Za-z0-9.-]*', str(target)):
        raise ValueError('invalid_category')
    if name == 'reply' and not str(target).isdigit():
        raise ValueError('invalid_comment_id')
    path = paths[name]
    fields = {}
    if name == 'reply':
        path += str(target) + '/reply'
        fields['content'] = content
    elif name == 'comment':
        fields = {'comment[paper_uid]': target, 'comment[content]': content}
    else:
        from urllib.parse import quote
        path += quote(str(target), safe='/')
    if name in ('comment', 'reply') and not content:
        raise ValueError('empty_comment')
    payload = json.dumps({'path': path, 'fields': fields})
    script = '''(()=>{const p=PAYLOAD; const token=document.querySelector('meta[name="csrf-token"]')?.content;
if(!token || !document.querySelector('a[href="/logout"]')) throw Error('login_required');
if(window.__sciratePending) throw Error('operation_pending');
const ticket=crypto.randomUUID();window.__sciratePending=ticket;
window.__scirateResults=window.__scirateResults||{};
window.__scirateResults[ticket]={status:'pending'};
const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),25000);
fetch(p.path,{method:'POST',signal:controller.signal,credentials:'same-origin',headers:{'X-CSRF-Token':token,'X-Requested-With':'XMLHttpRequest','Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(p.fields)})
.then(async r=>{window.__scirateResults[ticket]={status:r.status,url:r.url,body:await r.text()};})
.catch(e=>{window.__scirateResults[ticket]={error:String(e)};})
.finally(()=>{clearTimeout(timeout);window.__sciratePending=null;});
return JSON.stringify({ticket,status:'pending'});})()'''.replace('PAYLOAD', payload)
    return json.loads(run_javascript(script, browser))

def receipt(ticket, browser='Chrome'):
    script = 'JSON.stringify((window.__scirateResults||{})[' + json.dumps(ticket) + ']||{status:"unknown_ticket"})'
    result = json.loads(run_javascript(script, browser))
    if 'body' in result:
        # HTTP success alone does not establish that a comment was accepted.
        result['verification'] = 'response_received; inspect response and refresh the target page to confirm state'
    return result
