/* Reference guide pages (templates/guide.html): contents with scroll-spy and reading progress (sticky column on
   desktop, sheet on tablet and phone), "Find an institution" (the site search engine on this page, with a find bar),
   section links, reference chips and back links, back to top, and the figure 3 path that lights up once.
   Everything works without it except the finder. */
(function(){
  var root=document.getElementById('guide');
  if(!root)return;
  var rtl=document.documentElement.dir==='rtl';
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  var desk=window.matchMedia('(min-width: 1100px)');
  var toc=document.getElementById('g-toc'),bar=root.querySelector('.g-bar'),barBtn=root.querySelector('.g-bar-btn'),
      barNow=root.querySelector('.g-bar-now'),scrim=root.querySelector('.g-scrim'),body=root.querySelector('.g-body');
  var links=[].slice.call(toc.querySelectorAll('a[data-s]'));
  var secs=links.map(function(a){return document.getElementById(a.getAttribute('data-s'))});
  var prog=toc.querySelector('.g-prog'),barProg=root.querySelector('.g-bar-prog i'),tocList=toc.querySelector('.g-toc-scroll');
  var topBtn=document.querySelector('.g-top');

  function offset(){return (desk.matches?72:122)+24}
  function go(el,flash){
    if(!el)return;
    el.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'});
    if(el.hasAttribute('tabindex'))el.focus({preventScroll:true});
    if(flash){el.classList.remove('g-flash');void el.offsetWidth;el.classList.add('g-flash');setTimeout(function(){el.classList.remove('g-flash')},2300)}
  }

  // ---------- scroll-spy, progress, back to top ----------
  var cur=-1,ticking=false;
  function update(){
    ticking=false;
    var y=offset()+8,i=0;
    for(var k=0;k<secs.length;k++){if(secs[k]&&secs[k].getBoundingClientRect().top<=y)i=k}
    if(i!==cur){
      if(cur>=0)links[cur].removeAttribute('aria-current');
      links[i].setAttribute('aria-current','true');cur=i;
      barNow.textContent=links[i].querySelector('.g-tl').textContent;
      if(desk.matches&&tocList.scrollHeight>tocList.clientHeight){ // keep the current entry in view inside the column
        var a=links[i],top=a.offsetTop-tocList.clientHeight/3;
        tocList.scrollTop=Math.max(0,top); // instant: a second smooth scroll would cancel the page's own (Chrome)
      }
    }
    var r=body.getBoundingClientRect(),h=r.height-window.innerHeight+offset();
    var p=Math.min(1,Math.max(0,(offset()-r.top)/(h>0?h:1)));
    prog.style.setProperty('--p',p);prog.setAttribute('aria-valuenow',Math.round(p*100));
    if(barProg)barProg.style.setProperty('--p',p);
    if(topBtn)topBtn.hidden=window.scrollY<window.innerHeight;
  }
  function onScroll(){if(!ticking){ticking=true;requestAnimationFrame(update)}}
  window.addEventListener('scroll',onScroll,{passive:true});
  window.addEventListener('resize',onScroll);
  update();

  // ---------- contents sheet (tablet and phone) ----------
  var lastFocus=null;
  function openSheet(){
    lastFocus=document.activeElement;
    toc.classList.add('open');scrim.hidden=false;barBtn.setAttribute('aria-expanded','true');
    document.body.style.overflow='hidden';
    toc.setAttribute('role','dialog');toc.setAttribute('aria-modal','true');
    setTimeout(function(){(links[cur]||links[0]).focus()},50);
  }
  function closeSheet(restore){
    if(!toc.classList.contains('open'))return;
    toc.classList.remove('open');scrim.hidden=true;barBtn.setAttribute('aria-expanded','false');
    document.body.style.overflow='';toc.removeAttribute('role');toc.removeAttribute('aria-modal');
    if(restore&&lastFocus)lastFocus.focus();
  }
  barBtn.addEventListener('click',openSheet);
  scrim.addEventListener('click',function(){closeSheet(true)});
  toc.querySelector('.g-toc-close').addEventListener('click',function(){closeSheet(true)});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeSheet(true)});
  desk.addEventListener&&desk.addEventListener('change',function(){closeSheet(false);onScroll()});
  links.forEach(function(a){a.addEventListener('click',function(e){
    var t=document.getElementById(a.getAttribute('data-s'));if(!t)return;
    e.preventDefault();closeSheet(false);
    history.pushState(null,'','#'+t.id);
    setTimeout(function(){go(t)},toc.classList.contains('open')?0:10);
  })});

  // ---------- section links: copy the address ----------
  root.querySelectorAll('.g-anchor').forEach(function(a){a.addEventListener('click',function(e){
    var id=a.getAttribute('href').slice(1),t=document.getElementById(id);
    e.preventDefault();history.replaceState(null,'','#'+id);go(t);
    var url=location.href.split('#')[0]+'#'+id;
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(function(){
      a.classList.add('copied');setTimeout(function(){a.classList.remove('copied')},1600)},function(){})}
  })});

  // ---------- references: chips open the list, highlight the cited references; back links return ----------
  var refs=document.getElementById('g-refs');
  function openRefs(){if(refs&&!refs.open)refs.open=true}
  root.querySelectorAll('.g-chip').forEach(function(c){c.addEventListener('click',function(e){
    e.preventDefault();openRefs();
    var a=+c.getAttribute('data-a'),z=+c.getAttribute('data-z');
    for(var n=a;n<=z;n++){
      var li=document.getElementById('ref-'+n);if(!li)continue;
      var back=li.querySelector('.g-back');if(back)back.setAttribute('href','#'+c.id);
      if(n!==a){li.classList.remove('g-flash');void li.offsetWidth;li.classList.add('g-flash')}
    }
    history.pushState(null,'','#ref-'+a);
    go(document.getElementById('ref-'+a),true);
  })});
  root.querySelectorAll('.g-back').forEach(function(b){b.addEventListener('click',function(e){
    var t=document.getElementById(b.getAttribute('href').slice(1));if(!t)return;
    e.preventDefault();history.pushState(null,'','#'+t.id);go(t,true);t.focus({preventScroll:true});
  })});
  function fromHash(){
    var id=decodeURIComponent(location.hash.slice(1));if(!id)return;
    var t=document.getElementById(id);if(!t)return;
    if(refs&&refs.contains(t)&&!refs.open){openRefs();setTimeout(function(){go(t,true)},30)}
  }
  window.addEventListener('hashchange',fromHash);fromHash();

  // ---------- find in this article: the site search engine (search.js, window.ASASearch) on this page only ----------
  // Two groups: "Institutions" (an institution's own card or table row, for its acronym, name or alias) and
  // "In this article" (every other passage that matches, in page order). Choosing one opens the find bar
  // ("2 of 5 ↑ ↓ ✕") to step through all matches.
  var fbox=root.querySelector('.g-find'),input=document.getElementById('g-find-in'),list=document.getElementById('g-find-list'),
      st=root.querySelector('.g-find-st'),T=JSON.parse(document.getElementById('g-find-data').textContent);
  var here=location.pathname,X=null,shown=[],sel=-1,all=[],fcur=-1,lastQ='',bar=null;
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function engine(){
    if(!window.ASASearch)return Promise.reject(new Error('search'));
    return window.ASASearch.load().then(function(x){X=x;return x});
  }
  function entOf(h){  // the institution of a card or row that the query names (a card can hold several)
    var A=window.ASASearch,vs=h.v.ts.join(' '),pre=null;
    for(var n=0;n<h.P.ents.length;n++){
      var e=h.P.ents[n],keys=[e.a,e.n,e.m].filter(Boolean).map(function(x){return A.terms(x).join(' ')});
      if(keys.indexOf(vs)>=0)return e;
      if(!pre&&keys.some(function(k){return h.v.ts.every(function(t){return k.split(' ').some(function(w){return w.lastIndexOf(t,0)===0})})}))pre=e;
    }
    return pre||h.P.ents[0];
  }
  function render(){
    var q=input.value.trim();
    if(!q){closeList();return}
    if(!X){list.innerHTML='<p class="g-fl-none">'+esc(T.loading)+'</p>';open();engine().then(render,function(){});return}
    var A=window.ASASearch,res=A.run(q,X,{page:here,finder:true}),hits=res.pages[0]?res.pages[0].hits:[];
    var inst=hits.filter(function(h){return h.score>=10000&&h.P.ents.length});
    var rest=hits.filter(function(h){return inst.indexOf(h)<0}).sort(function(a,b){return a.P.i-b.P.i});
    shown=inst.concat(rest);lastQ=q;A.texts(shown,X);
    all=shown.slice().sort(function(a,b){return a.P.i-b.P.i});
    sel=shown.length?0:-1;
    var html='',k=0;
    function item(h,body){return '<div class="g-fl-o" role="option" id="g-opt-'+k+'" data-i="'+(k++)+'" aria-selected="false">'+body+'</div>'}
    if(inst.length){
      html+='<div class="g-fl-g" role="group" aria-labelledby="g-fl-h1"><p class="g-fl-h" id="g-fl-h1" role="presentation">'+esc(T.inst)+'</p>';
      inst.forEach(function(h){
        var e=entOf(h),name=rtl?(e.m||e.n):e.n;
        html+=item(h,'<span class="hxs cat-'+esc(e.c)+'" aria-hidden="true"></span><b dir="ltr">'+esc(e.a)+'</b><span class="g-fl-n">'+esc(name)+'</span>'+
          (h.label&&h.label!==name?'<i class="g-fl-alias">'+esc(h.label)+'</i>':''));
      });
      html+='</div>';
    }
    if(rest.length){
      html+='<div class="g-fl-g" role="group" aria-labelledby="g-fl-h2"><p class="g-fl-h" id="g-fl-h2" role="presentation">'+esc(T.here)+' <span>'+rest.length+'</span></p>';
      rest.forEach(function(h){
        var parts=X.crumbs[h.P.ci].s.split(' › '),crumb=(parts.length>1?parts.slice(1):parts).join(' · ');
        html+=item(h,'<span class="g-fl-sec">'+esc(crumb)+'</span><span class="g-fl-s">'+A.snippet(h.show,h.v.words,110)+'</span>');
      });
      html+='</div>';
    }
    list.innerHTML=html||'<p class="g-fl-none">'+esc(T.none)+'</p>';
    open();mark();
    st.textContent=shown.length?shown.length+' '+T.count:T.none;
  }
  function open(){list.hidden=false;input.setAttribute('aria-expanded','true')}
  function closeList(){list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');sel=-1}
  function opts(){return list.querySelectorAll('[role="option"]')}
  function mark(){
    var os=opts();
    [].forEach.call(os,function(o,i){o.setAttribute('aria-selected',i===sel)});
    if(sel>=0&&os[sel]){input.setAttribute('aria-activedescendant','g-opt-'+sel);os[sel].scrollIntoView({block:'nearest'})}
    else input.removeAttribute('aria-activedescendant');
  }
  function show(i){
    var h=all[i];if(!h)return;fcur=i;
    window.ASASearch.go(lastQ,h.P.id,{extra:h.v.ts,hold:1,quiet:1});
    history.replaceState(null,'','#'+h.P.id);
    findbar();
  }
  function choose(i){
    var h=shown[i];if(!h)return;
    closeList();
    show(all.indexOf(h));
  }
  function findbar(){
    if(!bar){
      bar=document.createElement('div');bar.className='g-fbar';bar.setAttribute('role','region');bar.setAttribute('aria-label',T.bar);bar.tabIndex=-1;
      bar.innerHTML='<span class="g-fbar-q"></span><span class="g-fbar-n" aria-live="polite"></span>'+
        '<button type="button" class="g-fbar-b" data-d="-1" aria-label="'+esc(T.prev)+'" title="'+esc(T.prev)+'">↑</button>'+
        '<button type="button" class="g-fbar-b" data-d="1" aria-label="'+esc(T.next)+'" title="'+esc(T.next)+'">↓</button>'+
        '<button type="button" class="g-fbar-x" aria-label="'+esc(T.close)+'" title="'+esc(T.close)+'">✕</button>';
      document.body.appendChild(bar);
      bar.addEventListener('click',function(e){
        var b=e.target.closest('button');if(!b)return;
        if(b.classList.contains('g-fbar-x')){hideBar();return}
        step(+b.getAttribute('data-d'));
      });
    }
    bar.querySelector('.g-fbar-q').textContent=lastQ;
    bar.querySelector('.g-fbar-n').textContent=(fcur+1)+' '+T.of+' '+all.length;
    bar.hidden=false;document.body.classList.add('g-fbar-on');
  }
  function step(d){if(all.length)show((fcur+d+all.length)%all.length)}
  function hideBar(){if(bar){bar.hidden=true;document.body.classList.remove('g-fbar-on');window.ASASearch&&window.ASASearch.clear()}fcur=-1}
  document.addEventListener('keydown',function(e){
    if(!bar||bar.hidden)return;
    var t=e.target,inBar=bar.contains(t);
    if(e.key==='Escape'&&(inBar||!/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))){hideBar();return}
    if(e.key!=='Enter'||(t.tagName==='BUTTON'&&inBar))return;
    if(t===document.body||inBar||t.hasAttribute('data-p')||t.id===(all[fcur]&&all[fcur].P.id)){e.preventDefault();step(e.shiftKey?-1:1)}
  });
  input.addEventListener('input',render);
  input.addEventListener('focus',function(){engine().then(function(){if(input.value)render()},function(){})});
  input.addEventListener('keydown',function(e){
    var n=opts().length;
    if(e.key==='ArrowDown'){if(list.hidden)render();else if(n){sel=(sel+1)%n;mark()}e.preventDefault()}
    else if(e.key==='ArrowUp'){if(n){sel=(sel-1+n)%n;mark()}e.preventDefault()}
    else if(e.key==='Enter'){if(sel>=0&&!list.hidden){e.preventDefault();choose(sel)}else if(all.length&&input.value.trim()===lastQ){e.preventDefault();step(e.shiftKey?-1:1)}}
    else if(e.key==='Escape'){if(!list.hidden){e.stopPropagation();closeList()}}
  });
  list.addEventListener('mousedown',function(e){e.preventDefault()}); // keep focus in the input
  list.addEventListener('click',function(e){var o=e.target.closest('[data-i]');if(o)choose(+o.getAttribute('data-i'))});
  document.addEventListener('click',function(e){if(!fbox.contains(e.target))closeList()});

  // ---------- figure 3: the four cells light up one after another, once ----------
  var path=root.querySelector('.g-path-wrap');
  if(path&&!reduce&&'IntersectionObserver' in window){
    var r0=path.getBoundingClientRect();
    if(r0.top>window.innerHeight*.8){  // only when it is still below the screen
      path.classList.add('pre');
      var io=new IntersectionObserver(function(en){en.forEach(function(x){
        if(x.isIntersecting){path.classList.add('go');io.disconnect()}
      })},{threshold:.45});
      io.observe(path);
    }
  }
})();
