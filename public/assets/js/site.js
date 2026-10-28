(function(){
  var h=document.querySelector('.site-header');
  var forceSolid=h&&h.hasAttribute('data-solid');
  function onScroll(){ if(!h)return; if(forceSolid||h.classList.contains('search-open')||window.scrollY>40){h.classList.add('solid')}else{h.classList.remove('solid')} }
  onScroll(); window.addEventListener('scroll',onScroll,{passive:true});

  var mn=document.querySelector('.mobile-nav');
  document.querySelectorAll('[data-open-menu]').forEach(function(b){b.addEventListener('click',function(){mn.classList.add('open');document.body.style.overflow='hidden';b.setAttribute('aria-expanded','true')})});
  document.querySelectorAll('[data-close-menu]').forEach(function(b){b.addEventListener('click',function(){mn.classList.remove('open');document.body.style.overflow='';})});

  // "Services" menu: the label is a link to /services/; the chevron button toggles the dropdown (click, Enter/Space),
  // the dropdown also opens on hover (desktop); Escape and a click elsewhere close it. aria-expanded follows what is shown.
  // .shut keeps it closed under the pointer after the chevron or Escape closed it, until the pointer leaves.
  // A click on the chevron while the dropdown is open by hover keeps it open; the next click closes it.
  document.querySelectorAll('.nav .has-dd').forEach(function(li){
    var t=li.querySelector('.dd-tgl');if(!t)return;
    var set=function(o){li.classList.toggle('open',o);li.classList.toggle('shut',!o&&li.matches(':hover'));t.setAttribute('aria-expanded',o)};
    var shown=function(){return li.classList.contains('open')||(li.matches(':hover')&&!li.classList.contains('shut'))};
    t.addEventListener('click',function(){set(!li.classList.contains('open'))}); // opened by hover: the click keeps it open
    li.addEventListener('mouseenter',function(){if(!li.classList.contains('shut'))t.setAttribute('aria-expanded','true')});
    li.addEventListener('mouseleave',function(){li.classList.remove('shut');t.setAttribute('aria-expanded',li.classList.contains('open'))});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&shown()){var f=li.contains(document.activeElement);set(false);if(f)t.focus()}});
    li.addEventListener('focusout',function(e){if(li.classList.contains('open')&&!li.contains(e.relatedTarget))set(false)});
  });
  document.addEventListener('click',function(e){document.querySelectorAll('.nav .has-dd.open').forEach(function(li){if(!li.contains(e.target)){li.classList.remove('open');li.querySelector('.dd-tgl').setAttribute('aria-expanded','false')}})});
  // mobile menu: the chevron next to "Services" shows / hides the list of services
  document.querySelectorAll('.mn-tgl').forEach(function(t){
    t.addEventListener('click',function(){var o=t.getAttribute('aria-expanded')!=='true';t.setAttribute('aria-expanded',o);document.getElementById(t.getAttribute('aria-controls')).hidden=!o});
  });

  var els=document.querySelectorAll('.rv');
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(en){en.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{rootMargin:'0px 0px -8% 0px',threshold:.08});
    els.forEach(function(el){io.observe(el)});
  } else { els.forEach(function(el){el.classList.add('in')}); }

  document.querySelectorAll('.faq button').forEach(function(b){b.addEventListener('click',function(){var o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',!o);b.nextElementSibling.hidden=o;})});

  // homepage "ASA Briefing" hexagon: the active bar's fill animation (6s) drives the rotation,
  // so pausing the animation (hover / keyboard focus) also pauses the rotation
  var br=document.getElementById('brief');
  if(br){
    var slides=br.querySelectorAll('.brief-slide'),bars=br.querySelectorAll('.bar'),live=br.querySelector('.brief-slides'),cur=0;
    var auto=!br.classList.contains('still');
    live.setAttribute('aria-live',auto?'off':'polite');
    // item images (.brief-pic, one per item that has an image): only the current and the next one are loaded;
    // the current one fades in once it has loaded. Items without an image show the logo background.
    var pics={};
    var load=function(i){
      var p=pics[(i+slides.length)%slides.length],im=p&&p.querySelector('img');
      if(!im||!im.hasAttribute('data-src'))return;
      if(im.hasAttribute('data-srcset'))im.srcset=im.getAttribute('data-srcset');
      im.src=im.getAttribute('data-src');im.removeAttribute('data-src');
    };
    var paint=function(){for(var k in pics){var im=pics[k].querySelector('img');pics[k].classList.toggle('on',+k===cur&&im.complete&&im.naturalWidth>0)}};
    br.querySelectorAll('.brief-pic').forEach(function(p){pics[p.getAttribute('data-i')]=p;p.querySelector('img').addEventListener('load',paint)});
    load(0);paint();
    var pre=function(){load(cur+1)}; // the next image, after the page has finished loading
    if(document.readyState==='complete')pre();else window.addEventListener('load',pre);
    var show=function(i){
      cur=(i+slides.length)%slides.length;
      load(cur);load(cur+1);paint();
      slides.forEach(function(s,j){s.classList.toggle('on',j===cur)});
      bars.forEach(function(b,j){b.classList.remove('on');if(j===cur){b.setAttribute('aria-current','true')}else{b.removeAttribute('aria-current')}});
      void br.offsetWidth; // restart the fill animation
      bars[cur].classList.add('on');
    };
    bars.forEach(function(b,j){b.addEventListener('click',function(){show(j)})});
    // previous / next: arrows, left/right keys while the hexagon has focus, and swipe on touch screens.
    // show() restarts the 6s fill animation, so the timer restarts too. In Arabic "next" is to the left.
    var rtl=document.documentElement.dir==='rtl';
    br.querySelectorAll('.brief-arrow').forEach(function(a){a.addEventListener('click',function(){show(cur+(+a.getAttribute('data-step')))})});
    br.addEventListener('keydown',function(e){
      if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight'||e.altKey||e.ctrlKey||e.metaKey)return;
      e.preventDefault();show(cur+((e.key==='ArrowRight')!==rtl?1:-1));
    });
    var tx=null,ty=0;
    br.addEventListener('touchstart',function(e){if(e.touches.length===1){tx=e.touches[0].clientX;ty=e.touches[0].clientY}else{tx=null}},{passive:true});
    br.addEventListener('touchend',function(e){
      if(tx===null)return;var t=e.changedTouches[0],dx=t.clientX-tx,dy=t.clientY-ty;tx=null;
      if(Math.abs(dx)<40||Math.abs(dx)<Math.abs(dy)*1.2)return;
      show(cur+((dx<0)!==rtl?1:-1));
    },{passive:true});
    // summary: at most 2 lines, cut at a whole word with "…" (CSS line-clamp is the no-JS fallback)
    var sums=br.querySelectorAll('.brief-sum');
    var fit=function(){sums.forEach(function(el){
      var full=el.getAttribute('data-full');if(full===null){full=el.textContent.trim();el.setAttribute('data-full',full)}
      el.classList.add('fit');el.textContent=full;
      if(!el.offsetHeight)return; // hidden on small screens
      var max=2*parseFloat(getComputedStyle(el).lineHeight)+1,words=full.split(/\s+/);
      while(el.scrollHeight>max&&words.length>1){words.pop();el.textContent=words.join(' ').replace(/[\s,،;:.\-—–]+$/,'')+'…'}
    })};
    fit();
    var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(fit,150)});
    if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit);
    if(auto){
      br.addEventListener('animationend',function(e){if(e.animationName==='bFill'&&br.classList.contains('run'))show(cur+1)});
      setTimeout(function(){br.classList.add('run')},br.classList.contains('intro')?3850:800);
      var hover=false,focus=false,upd=function(){br.classList.toggle('paused',hover||focus)};
      br.addEventListener('mouseenter',function(){hover=true;upd()});
      br.addEventListener('mouseleave',function(){hover=false;upd()});
      br.addEventListener('focusin',function(e){var fv=true;try{fv=e.target.matches(':focus-visible')}catch(x){}focus=fv;upd()});
      br.addEventListener('focusout',function(e){if(!br.contains(e.relatedTarget)){focus=false;upd()}});
    }
  }

  // ASA NEXT quiz: answers are visible without JS; with JS they are hidden until "Show answer"
  document.querySelectorAll('.nx-quiz-btn').forEach(function(b){
    var a=document.getElementById(b.getAttribute('aria-controls'));if(!a)return;
    a.hidden=true;b.hidden=false;
    b.addEventListener('click',function(){var o=a.hidden;a.hidden=!o;b.setAttribute('aria-expanded',o);b.textContent=o?b.dataset.hide:b.dataset.show});
  });

  // phones: the floating buttons (WhatsApp, back to top) step aside while the page scrolls down, so they never sit
  // over the text being read; they come back when scrolling up, at the top and at the end of the page
  var fabMq=window.matchMedia('(max-width: 767px)'),fabY=window.scrollY,fabT;
  function fab(){
    var y=window.scrollY,end=y+window.innerHeight>=document.documentElement.scrollHeight-160,away=document.body.classList.contains('fab-away');
    if(!fabMq.matches||y<80||end)away=false;
    else if(y>fabY+6)away=true;
    else if(y<fabY-6)away=false;
    document.body.classList.toggle('fab-away',away);fabY=y;
    clearTimeout(fabT);
    if(!away&&fabMq.matches&&y>=80&&!end)fabT=setTimeout(function(){document.body.classList.add('fab-away')},2500); // back out of the way after a pause
  }
  window.addEventListener('scroll',fab,{passive:true});

  var y=document.querySelectorAll('[data-year]');y.forEach(function(e){e.textContent=new Date().getFullYear()});

  // language switch (English / العربية): the other language opens at the same place. On click, the element at the
  // reading line (just under the header) that has an id is noted with its ancestors that have one, how far into it the
  // line is, and how far down the page we are. The other page goes to the first of these ids it also has (passage ids
  // "<section>-p<n>" only when that section has as many passages in both languages), else to the same percentage.
  // Near the top of the page, or with a modifier key, the link works as a normal link. No highlight, no address change.
  // Positions come from the layout (offsetTop), not the screen, so the reveal animation (.rv) does not shift them.
  var LKEY='asaLangPos';
  function topOf(el){var t=0;for(;el;el=el.offsetParent)t+=el.offsetTop;return t}
  function shown(el){return el.offsetParent!==null&&el.offsetHeight>0&&!el.closest('nav,aside,.g-toc,[hidden]')}
  function pcount(id){var m=/^(.+)-p\d+$/.exec(id);if(!m)return 0;var n=0,re=new RegExp('^'+m[1].replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'-p\\d+$');
    document.querySelectorAll('main [id]').forEach(function(e){if(re.test(e.id))n++});return n}
  document.querySelectorAll('a.lang').forEach(function(a){a.addEventListener('click',function(e){
    if(e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||window.scrollY<120)return;
    var hd=document.querySelector('.site-header'),line=window.scrollY+(hd?hd.offsetHeight:0)+12,best=null,below=null;
    document.querySelectorAll('main [id]').forEach(function(el){
      if(!(el instanceof HTMLElement)||!shown(el))return;                          // hidden (closed answers, other tabs)
      var t=topOf(el),h=el.offsetHeight;
      if(t<=line&&t+h>line){if(!best||h<=best.h)best={el:el,h:h}}                   // the smallest one at the line
      else if(t>line&&(!below||t<below.t))below={el:el,t:t};                         // else the first one below it
    });
    var at=best||below,chain=[];
    for(var el=at&&at.el;el&&el.tagName!=='MAIN';el=el.parentElement){
      if(!el.id||!shown(el))continue;var t=topOf(el);
      chain.push({id:el.id,n:pcount(el.id),f:t<line?(line-t)/el.offsetHeight:0,o:t-window.scrollY});
    }
    var max=document.documentElement.scrollHeight-window.innerHeight;
    try{sessionStorage.setItem(LKEY,JSON.stringify({to:a.pathname,t:Date.now(),c:chain,l:line-window.scrollY,pct:max>0?window.scrollY/max:0}))}catch(x){}
  })});
  (function(){
    var s=null;try{s=JSON.parse(sessionStorage.getItem(LKEY));sessionStorage.removeItem(LKEY)}catch(x){}
    if(!s||s.to!==location.pathname||Date.now()-s.t>15000||location.hash||/[?&]hl=/.test(location.search))return;
    var place=function(){
      for(var i=0;i<s.c.length;i++){
        var c=s.c[i],el=document.getElementById(c.id);
        if(!el||!el.closest('main')||!shown(el)||(c.n&&pcount(c.id)!==c.n))continue;
        var t=topOf(el);
        return window.scrollTo({top:c.f>0?t+c.f*el.offsetHeight-s.l:t-Math.max(c.o,s.l),behavior:'instant'});
      }
      var max=document.documentElement.scrollHeight-window.innerHeight;
      window.scrollTo({top:s.pct*max,behavior:'instant'});
    };
    place();
    var y0=window.scrollY;   // images and fonts can move things: place again on load unless the reader has scrolled
    window.addEventListener('load',function(){if(Math.abs(window.scrollY-y0)<4)place()},{once:true});
  })();
})();
