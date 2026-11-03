"""Browser UI integration with Chrome API mock. In-memory page, not real extension install."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'popup.html').read_text()
import base64
icon = base64.b64encode((ROOT / 'icons/icon128.png').read_bytes()).decode('ascii')
html = html.replace('src="icons/icon128.png"', f'src="data:image/png;base64,{icon}"')
html = html.replace('<link rel="stylesheet" href="popup.css" />', '')
html = html.replace('<script src="asset-utils.js"></script>', '')
html = html.replace('<script src="scan-page.js"></script>', '')
html = html.replace('<script src="popup.js"></script>', '')
mock = r'''
window.__downloads = [];
window.__clip = '';
Object.defineProperty(navigator, 'clipboard', {configurable:true,value:{writeText: async (s) => {window.__clip=s;}}});
window.chrome = {
  storage: {local:{get:async()=>({language:'en'}),set:async()=>{}}},
  tabs: {query:async()=>[{id:7,url:'https://example.com/work'}]},
  scripting: {executeScript:async()=>[{result:{
    title:'Portfolio',domain:'example.com',pageUrl:'https://example.com/work',truncated:false,assets:[
      {type:'image',url:'https://assets.example.com/hero.webp',name:'Hero',width:2100,height:1200,source:'image'},
      {type:'image',url:'https://assets.example.com/logo.png',name:'Logo',width:200,height:200,source:'image'},
      {type:'video',url:'https://assets.example.com/showreel.mp4',name:'Showreel',source:'video'},
      {type:'audio',url:'https://assets.example.com/podcast.mp3',name:'Podcast',source:'audio'},
      {type:'document',url:'https://assets.example.com/manual.pdf',name:'Manual',source:'link'}
    ]
  }}]},
  downloads:{download:async(data)=>{window.__downloads.push(data);return window.__downloads.length;}}
};
'''
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':460,'height':690},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda err: errors.append(str(err)))
    page.set_content(html,wait_until='load')
    page.add_style_tag(content=(ROOT/'popup.css').read_text())
    page.evaluate(mock)
    for js in ('asset-utils.js','scan-page.js','popup.js'):
        page.add_script_tag(content=(ROOT/js).read_text())
    page.locator('.asset').first.wait_for()
    assert page.locator('.asset').count()==5
    assert page.locator('#totalCount').inner_text()=='05'
    page.locator('#largeImages').check()
    assert page.locator('.asset').count()==4
    page.locator('#largeImages').uncheck()
    page.locator('#sortMode').select_option('name')
    assert page.locator('.asset-name').first.inner_text()=='Hero'
    page.locator('[data-filter="audio"]').click()
    assert page.locator('.asset').count()==1
    page.locator('[data-filter="image"]').click()
    assert page.locator('.asset').count()==2
    page.locator('[data-filter="all"]').click()
    page.locator('#search').fill('showreel')
    assert page.locator('.asset').count()==1
    page.locator('#search').fill('')
    page.locator('#csvBtn').click()
    page.wait_for_function('window.__clip.includes("type,name,url")')
    page.locator('.asset').first.locator('input').check()
    page.locator('#downloadBtn').click()
    page.wait_for_function('window.__downloads.length === 1')
    assert page.evaluate('window.__downloads[0].filename') == 'KNOuX-GrabFlow/example.com/hero.webp'
    page.locator('#langBtn').click()
    assert page.locator('html').get_attribute('dir')=='rtl'
    assert page.locator('#downloadBtn').get_by_text('تحميل المحدد').count()==1
    page.locator('#langBtn').click()
    page.screenshot(path=str(ROOT.parent/'KNOuX-GrabFlow-v0.3.0-preview.png'),full_page=True)
    if errors: raise AssertionError(errors)
    print('PASS In-memory Chromium popup: filtering, sorting, large-only, CSV, downloads API mock, RTL, no JS errors')
    print('IMPORTANT: No real extension installation, no live download/network runtime verified.')
    browser.close()
