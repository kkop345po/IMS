const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('brain-selector.zh-TW.html','utf8');
const decode=s=>s.replace(/&quot;/g,'"').replace(/&#x27;/g,"'").replace(/&amp;/g,'&');
function el(dataset={}){const classes=new Set();return {dataset,textContent:'',style:{},checked:false,classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),contains:x=>classes.has(x),toggle(x,v){if(v===undefined)v=!classes.has(x);v?classes.add(x):classes.delete(x)}},events:{},addEventListener(k,f){this.events[k]=f},getBoundingClientRect(){return {top:400}}};}
const inputs=[...source.matchAll(/<input\b([^>]+)>/g)].map(m=>{const d={};for(const a of m[1].matchAll(/data-([\w-]+)="([^"]*)"/g))d[a[1]]=decode(a[2]);return el(d)});
const modes=['Facilitator','Creative Partner','Ideate for me'].map(mode=>el({mode}));
const goals=['feature','novel','strategy','planning','diagnosis','personal','unstuck'].map(goal=>el({goal}));
const steps=['rand','inv','ai'].map(step=>el({step,d:'1'}));
const labels=inputs.map(input=>Object.assign(el(),{querySelector:()=>input}));
const ids={};let copied='';let theme='light';
const document={documentElement:{getAttribute:()=>theme,setAttribute:(k,v)=>theme=v},getElementById:id=>ids[id]??=el(),querySelector:()=>({offsetHeight:200}),querySelectorAll:q=>({'input[type=checkbox]':inputs,'.mode':modes,'[data-step]':steps,'.chip':[],section:[],'.goal':goals,'label.tech':labels}[q]||[])};
const context={document,localStorage:{getItem:()=>null,setItem(){}},window:{matchMedia:()=>({matches:false}),scrollTo(){}},navigator:{clipboard:{writeText(t){copied=t;return Promise.resolve()}}},setTimeout(){}};
const scripts=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];scripts.forEach(m=>vm.runInNewContext(m[1],context));
(async()=>{
 assert.match(ids.modehint.textContent,/提問/); assert.match(ids.total.textContent,/共 0 項/);
 inputs[0].checked=true;inputs[0].events.change();assert.equal(ids.pickN.textContent,1);
 const twin=inputs.find((b,i)=>i>0&&b.dataset.name===inputs[0].dataset.name);twin.checked=true;twin.events.change();assert.equal(ids.pickN.textContent,1);
 for(const s of steps)s.events.click();assert.match(ids.total.textContent,/共 4 項/);
 goals[0].events.click();assert(labels.some(l=>l.classList.contains('hidden')));
 modes[1].events.click();assert.match(ids.modehint.textContent,/一起/);
 ids.theme.events.click();assert.equal(theme,'dark');
 ids.copy.events.click();await Promise.resolve();assert.match(copied,/全程使用繁體中文/);assert.match(copied,/引導模式：創意夥伴/);assert.match(copied,/肯定與延伸/);assert.match(copied,/即興自創 1 種全新技巧/);assert.match(copied,/再挑選 1 種/);assert.match(ids.banner.innerHTML,/已複製/);
 console.log('PASS: initialization, selection deduplication, counters, goal filter, modes, theme, Chinese prompt and clipboard feedback');
})();
