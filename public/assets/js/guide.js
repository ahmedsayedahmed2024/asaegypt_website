/* Reference guide pages (templates/guide.html): contents with scroll-spy and reading progress (sticky column on
   desktop, sheet on tablet and phone), "Find an institution", section links, reference chips and back links,
   back to top, and the figure 3 path that lights up once. Everything works without it except the finder. */
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

  // ---------- find an institution ----------
  var box=root.querySelector('.g-find'),input=document.getElementById('g-find-in'),list=document.getElementById('g-find-list'),
      st=root.querySelector('.g-find-st'),data=JSON.parse(document.getElementById('g-find-data').textContent);
  var AR={'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ة':'ه','ؤ':'و','ئ':'ي'};
  function norm(s){  // as in site search: lower case, no tashkeel/tatweel, one alef/yaa/haa form, Latin accents off
    return s.toLowerCase().replace(/[ً-ٰٟۖ-ۭـ]/g,'')
      .replace(/[أإآٱىةؤئ]/g,function(c){return AR[c]}).normalize('NFKD').replace(/[̀-ͯ]/g,'')
      .replace(/[&().,:;'’\-–—]/g,' ');
  }
  function words(s){return norm(s).split(/\s+/).filter(Boolean).map(function(w){var m=w.match(/^(?:[وفبك]?ال|لل)(..+)$/);return m?m[1]:w})}
  data.items.forEach(function(d){d.k=norm(d.a).replace(/\s+/g,'');d.w=words(d.a+' '+d.n+' '+d.m)});
  var shown=[],sel=-1;
  function score(d,q,qw){
    var qk=q.replace(/\s+/g,'');
    if(d.k===qk)return 1000;
    if(qk.length>=1&&d.k.indexOf(qk)===0)return 600-d.k.length;
    var s=0;
    for(var i=0;i<qw.length;i++){
      var best=0;
      for(var j=0;j<d.w.length;j++){var w=d.w[j];if(w===qw[i]){best=3;break}if(w.indexOf(qw[i])===0)best=Math.max(best,2);else if(qw[i].length>=3&&w.indexOf(qw[i])>0)best=Math.max(best,1)}
      if(!best)return 0;s+=best;
    }
    return 100+s*10;
  }
  function esc(s){return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function render(){
    var q=norm(input.value).trim();
    if(!q){close();return}
    var qw=words(q);
    shown=data.items.map(function(d){return {d:d,s:score(d,q,qw)}}).filter(function(x){return x.s>0})
      .sort(function(a,b){return b.s-a.s||a.d.a.localeCompare(b.d.a)}).slice(0,8).map(function(x){return x.d});
    sel=shown.length?0:-1;
    list.innerHTML=shown.length?shown.map(function(d,i){
      var name=rtl?(d.m||d.n):d.n;
      return '<li role="option" id="g-opt-'+i+'" data-i="'+i+'" aria-selected="'+(i===sel)+'"><span class="hxs cat-'+d.c+'" aria-hidden="true"></span><b dir="ltr">'+esc(d.a)+'</b><span>'+esc(name)+'</span></li>'
    }).join(''):'<li class="none" role="option" aria-disabled="true">'+esc(data.none)+'</li>';
    list.hidden=false;input.setAttribute('aria-expanded','true');
    input.setAttribute('aria-activedescendant',sel>=0?'g-opt-0':'');
    st.textContent=shown.length?shown.length+'':data.none;
  }
  function close(){list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');shown=[];sel=-1}
  function mark(){
    [].forEach.call(list.children,function(li,i){li.setAttribute('aria-selected',i===sel)});
    if(sel>=0){input.setAttribute('aria-activedescendant','g-opt-'+sel);var li=list.children[sel];li&&li.scrollIntoView({block:'nearest'})}
  }
  function choose(i){
    var d=shown[i];if(!d)return;
    var t=document.getElementById(d.t);close();input.value=d.a;
    if(t){history.pushState(null,'','#'+d.t);go(t,true)}
  }
  input.addEventListener('input',render);
  input.addEventListener('focus',function(){if(input.value)render()});
  input.addEventListener('keydown',function(e){
    if(e.key==='ArrowDown'){if(list.hidden)render();else if(shown.length){sel=(sel+1)%shown.length;mark()}e.preventDefault()}
    else if(e.key==='ArrowUp'){if(shown.length){sel=(sel-1+shown.length)%shown.length;mark()}e.preventDefault()}
    else if(e.key==='Enter'){if(sel>=0){e.preventDefault();choose(sel)}}
    else if(e.key==='Escape'){if(!list.hidden){e.stopPropagation();close()}}
  });
  list.addEventListener('mousedown',function(e){e.preventDefault()}); // keep focus in the input
  list.addEventListener('click',function(e){var li=e.target.closest('li[data-i]');if(li)choose(+li.getAttribute('data-i'))});
  document.addEventListener('click',function(e){if(!box.contains(e.target))close()});

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
