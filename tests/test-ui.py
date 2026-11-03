"""Chromium popup UI smoke test. Chrome APIs are mocked, not a real store install."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading, functools

ROOT=Path(__file__).resolve().parent.parent
mock = r'''
window.__startedDownloads=[];
const mockAssets = [
 {type:'image',url:'https://assets.example.com/hero-portrait.webp',name:'Editorial hero artwork'},
 {type:'image',url:'https://assets.example.com/dashboard.png',name:'Dashboard preview'},
 {type:'image',url:'https://assets.example.com/stag.png',name:'Stag logo'},
 {type:'video',url:'https://assets.example.com/showreel.mp4',name:'Brand motion showreel'},
 {type:'document',url:'https://assets.example.com/portfolio.pdf',name:'Portfolio PDF'},
 {type:'document',url:'https://assets.example.com/specification.docx',name:'Specification document'}
];
window.chrome={
 storage:{local:{get:async()=>({language:'en'}),set:async()=>{}}},
 tabs:{query:async()=>[{id:7,url:'https://example.com/work'}]},
 scripting:{executeScript:async()=>[{result:{title:'Portfolio',domain:'example.com',pageUrl:'https://example.com/work',assets:mockAssets,truncated:false}}]},
 downloads:{download:async(data)=>{window.__startedDownloads.push(data);return window.__startedDownloads.length;},
   search:async({id})=>[{id,state:'complete'}],onChanged:{addListener:()=>{}}},
 runtime:{sendNativeMessage:(host,msg,cb)=>{if(cb)cb({action:'pong',version:'0.5.0'});}}
};
'''
handler=functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT))
server=ThreadingHTTPServer(('127.0.0.1',0),handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':465,'height':680},device_scale_factor=1)
    errs=[]
    page.on('pageerror',lambda error: errs.append(str(error)))
    page.add_init_script(mock)
    page.goto(f'http://127.0.0.1:{server.server_port}/popup.html')
    page.locator('#totalCount').get_by_text('06').wait_for(timeout=10000)
    assert page.locator('.asset').count()==6
    page.locator('[data-filter="video"]').click()
    assert page.locator('.asset').count()==1
    page.locator('[data-filter="all"]').click()
    page.locator('#search').fill('dashboard')
    assert page.locator('.asset').count()==1
    page.locator('#search').fill('')
    page.locator('.asset').first.locator('input').check()
    assert page.locator('#downloadBtn').is_enabled()
    page.locator('#downloadBtn').click()
    page.wait_for_function('window.__startedDownloads.length === 1')
    assert page.evaluate('window.__startedDownloads[0].filename') == 'KNOuX-GrabFlow/example.com/hero-portrait.webp'
    page.locator('#clearSelection').click()
    page.locator('#langBtn').click()
    assert page.locator('html').get_attribute('dir') == 'rtl'
    assert page.locator('#downloadBtn').get_by_text('تحميل المحدد').count()==1
    page.locator('#langBtn').click()
    page.locator('#search').fill('')
    page.screenshot(path=str(ROOT.parent/'KNOUX-GrabFlow-preview.png'),full_page=True)
    print('PASS browser UI: count, filters, search, select, download API interaction, Arabic RTL, English, screenshot')
    if errs: raise AssertionError(f'JavaScript page errors: {errs}')
    print('PASS no popup JavaScript page errors')
    browser.close()

server.shutdown()
