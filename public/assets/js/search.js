/* ASA site search: the header panel (every page) and the search page (/search/, /ar/search/).
   The index (assets/search/<lang>.json) is built from the site data by src/search.py and loaded on first use.
   Everything runs in the browser: no external service, no tracking, no CDN. */
(function(){
  var panel=document.getElementById('site-search');
  if(!panel)return;
  var cfg=JSON.parse(panel.getAttribute('data-cfg')),S=cfg.s;
  var GROUPS=['insights','briefing','next','services','pages'];
  var PER_GROUP=5,MIN_CHARS=2;
  var WEIGHT={t:100,c:10,m:10,b:1};          // title > summary (and category) > body
  var WORD=/[\p{L}\p{N}\p{M}ـ]+/gu;     // a word in the original text (keeps Arabic marks inside the word)
  var store=function(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}};

  // ---------- normalisation (index and query) ----------
  var AR={'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ة':'ه','ؤ':'و','ئ':'ي'};
  function norm(s){
    return s.toLowerCase()
      .replace(/[ً-ٰٟۖ-ۭـ]/g,'')            // tashkeel and tatweel
      .replace(/[أإآٱىةؤئ]/g,function(c){return AR[c]})
      .replace(/[٠-٩]/g,function(d){return String.fromCharCode(d.charCodeAt(0)-0x0630)}) // ٠-٩ → 0-9
      .normalize('NFKD').replace(/[̀-ͯ]/g,'');                  // é → e
  }
  var isAr=function(w){return /[؀-ۿ]/.test(w)};
  var isNum=function(w){return /^\d+$/.test(w)};
  // Arabic: also index the word without «ال» (and و/ف/ب/ك + «ال», «لل»), or without a leading و/ف/ب/ل
  function variants(w){
    var out=[w];
    if(isAr(w)){
      var m=w.match(/^(?:[وفبك]?ال|لل)(..+)$/);
      if(m)out.push(m[1]);
      else if(w.length>=4&&/^[وفبل]/.test(w))out.push(w.slice(1));
    }
    return out;
  }
  // Arabic: a light "skeleton" so «ضريبة», «ضريبي» and «الضرائب» meet: drop a common ending, then the long vowels
  function skel(w){
    var t=w.replace(/(?:ات|ون|ين|ان|يه|ه)$/,'');
    if(t.length<3)t=w;
    return t.charAt(0)+t.slice(1).replace(/[اوي]/g,'');
  }
  // optimal string alignment distance, stops early above max
  function dist(a,b,max){
    if(Math.abs(a.length-b.length)>max)return max+1;
    var d=[],i,j;
    for(i=0;i<=a.length;i++){d[i]=[i]}
    for(j=1;j<=b.length;j++)d[0][j]=j;
    for(i=1;i<=a.length;i++){
      var low=max+1;
      for(j=1;j<=b.length;j++){
        var c=a[i-1]===b[j-1]?0:1;
        d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+c);
        if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])d[i][j]=Math.min(d[i][j],d[i-2][j-2]+1);
        if(d[i][j]<low)low=d[i][j];
      }
      if(low>max)return max+1;
    }
    return d[a.length][b.length];
  }

  // ---------- index ----------
  var loaded={};
  function load(lang){
    if(!loaded[lang]){
      var url=lang===cfg.lang?cfg.idx:cfg.idx2;
      loaded[lang]=fetch(url+'?v='+cfg.v).then(function(r){if(!r.ok)throw new Error(r.status);return r.json()}).then(function(list){
        var vocab=new Map();
        list.forEach(function(d,i){
          d.lang=lang;d.i=i;d.f={};
          ['t','c','m','b'].forEach(function(k){
            var set=new Set();
            (norm(d[k]||'').match(WORD)||[]).forEach(function(w){variants(w).forEach(function(v){set.add(v);vocab.set(v,1)})});
            d.f[k]=set;
          });
        });
        return {docs:list,vocab:vocab};
      });
      loaded[lang].catch(function(){delete loaded[lang]});
    }
    return loaded[lang];
  }

  // query → terms; each term gets the index words it matches, with a quality (1 = exact/prefix, .6 = fuzzy)
  function terms(q){
    // a query word drops «ال» (and و/ف/ب/ك + «ال», «لل»); the index holds both forms
    var ws=(norm(q).match(WORD)||[]).map(function(w){var m=isAr(w)&&w.match(/^(?:[وفبك]?ال|لل)(..+)$/);return m?m[1]:w});
    var long=ws.filter(function(w){return w.length>1||isNum(w)});
    return long.length?long:ws;
  }
  function matchTerm(t,vocab){
    var hits=new Map(),ar=isAr(t),num=isNum(t),sk=ar&&t.length>=4?skel(t):null,typo=!ar&&!num&&t.length>=5;
    vocab.forEach(function(_,w){
      var q=0;
      if(w===t)q=1;
      else if(num)q=0;
      else if(w.lastIndexOf(t,0)===0)q=1;                                    // prefix: "consol" → "consolidation"
      else if(sk&&sk.length>=3&&isAr(w)){var ws=skel(w);if(ws===sk||(sk.length>=4&&ws.lastIndexOf(sk,0)===0))q=.6}
      else if(typo&&!isAr(w)&&w.length>=4&&(dist(t,w,1)<=1||(t.length>=6&&w.length>t.length&&dist(t,w.slice(0,t.length),1)<=1)))q=.6;
      if(q)hits.set(w,q);
    });
    return hits;
  }
  function search(q,idxs){
    var ts=terms(q);if(!ts.length)return {list:[],words:new Set()};
    var vocab=new Map();idxs.forEach(function(x){x.vocab.forEach(function(v,k){vocab.set(k,1)})});
    var hits=ts.map(function(t){return matchTerm(t,vocab)}),words=new Set();
    hits.forEach(function(h){h.forEach(function(_,w){words.add(w)})});
    var out=[];
    idxs.forEach(function(x){x.docs.forEach(function(d){
      var score=0,fields={};
      for(var n=0;n<hits.length;n++){
        var best=0,bestK=null;
        for(var k in WEIGHT){var set=d.f[k];hits[n].forEach(function(qq,w){if(qq*WEIGHT[k]>best&&set.has(w)){best=qq*WEIGHT[k];bestK=k}})}
        if(!best)return;                                                     // every word must match
        score+=best;fields[bestK]=1;
      }
      out.push({d:d,score:score,fields:fields});
    })});
    out.sort(function(a,b){return b.score-a.score||(b.d.d||'').localeCompare(a.d.d||'')||(a.d.lang===cfg.lang?0:1)-(b.d.lang===cfg.lang?0:1)||a.d.i-b.d.i});
    return {list:out,words:words};
  }

  // ---------- rendering ----------
  function esc(s){return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function isHit(word,words){return variants(norm(word)).some(function(v){return words.has(v)})}
  function hl(text,words){
    var out='',last=0;
    text.replace(WORD,function(w,i){out+=esc(text.slice(last,i))+(isHit(w,words)?'<mark>'+esc(w)+'</mark>':esc(w));last=i+w.length});
    return out+esc(text.slice(last));
  }
  function snippet(r,words){
    var d=r.d,src=r.fields.m||r.fields.c||!r.fields.b?d.m:d.b,at=-1;
    src.replace(WORD,function(w,i){if(at<0&&isHit(w,words))at=i});
    if(at<0||at<60)return hl(src.length>180?src.slice(0,180).replace(/\s+\S*$/,'')+'…':src,words);
    var start=src.lastIndexOf(' ',at-40);start=start<0?0:start+1;
    var piece=src.slice(start,start+180).replace(/\s+\S*$/,'');
    return '…'+hl(piece,words)+(start+180<src.length?'…':'');
  }
  function date(iso){if(!iso)return '';var p=iso.split('-');return (+p[2])+' '+cfg.months[+p[1]-1]+' '+p[0]}
  function item(r,words,id){
    var d=r.d,other=d.lang!==cfg.lang,la=other?' lang="'+d.lang+'" dir="'+(d.lang==='ar'?'rtl':'ltr')+'"':'';
    var meta=[d.c,date(d.d)].filter(Boolean).map(esc);
    if(other)meta.push('<span class="sp-lang">'+esc(S.other)+'</span>');
    return '<a class="sp-item" href="'+esc(d.u)+'"'+(id?' id="'+id+'" role="option" aria-selected="false"':'')+'>'+
      '<span class="sp-t"'+la+'>'+hl(d.t,words)+'</span><span class="sp-s"'+la+'>'+snippet(r,words)+'</span>'+
      (meta.length?'<span class="sp-meta">'+meta.join(' · ')+'</span>':'')+'</a>';
  }
  function groups(res,limit,opt){
    var html='',n=0;
    GROUPS.forEach(function(g){
      var rs=res.list.filter(function(r){return r.d.g===g});if(!rs.length)return;
      html+='<div class="sp-group" role="group" aria-label="'+esc(S.groups[g])+'"><p class="sp-ghead" aria-hidden="true"><span class="sp-badge sp-b-'+g+'"'+(g==='next'?' dir="ltr" lang="en"':'')+'>'+esc(S.groups[g])+'</span><span class="sp-gcount">'+rs.length+'</span></p>';
      rs.slice(0,limit||rs.length).forEach(function(r){html+=item(r,res.words,opt?'sp-o'+(n++):'')});
      html+='</div>';
    });
    return html;
  }
  function empty(q,opt){
    return '<div class="sp-empty"><p class="sp-none">'+esc(S.none)+' <b>«'+esc(q)+'»</b></p><p class="sp-try">'+esc(S.try_)+'</p><ul>'+
      cfg.links.map(function(l,i){return '<li><a class="sp-sugg" href="'+esc(l[1])+'"'+(opt?' id="sp-s'+i+'" role="option" aria-selected="false"':'')+'>'+esc(l[0])+'</a></li>'}).join('')+'</ul></div>';
  }
  function pageUrl(q){return cfg.page+'?q='+encodeURIComponent(q)}

  // ---------- "also search the other language" switch (remembered in this browser) ----------
  var ALSO_KEY='asaSearchAlso';
  function alsoOn(){return store(ALSO_KEY)==='1'}
  function wireAlso(btn,run){
    if(!btn)return;btn.hidden=false;btn.setAttribute('aria-checked',alsoOn());
    btn.addEventListener('click',function(){var on=btn.getAttribute('aria-checked')!=='true';store(ALSO_KEY,on?'1':'0');
      document.querySelectorAll('.sp-also').forEach(function(b){b.setAttribute('aria-checked',on)});run()});
  }
  function indexes(){return Promise.all(alsoOn()?[load(cfg.lang),load(cfg.other)]:[load(cfg.lang)])}

  // ---------- header panel ----------
  var header=document.querySelector('.site-header'),scrim=document.querySelector('.search-scrim');
  var input=panel.querySelector('.sp-input'),box=panel.querySelector('.sp-results'),status=panel.querySelector('.sp-status');
  var openers=document.querySelectorAll('[data-open-search]'),back=null,active=-1,seq=0;
  function isOpen(){return !panel.hidden}
  function open(){
    if(isOpen()){input.focus();return}
    back=document.activeElement;
    panel.hidden=false;scrim.hidden=false;
    header.classList.add('search-open','solid');document.body.classList.add('search-lock');
    openers.forEach(function(b){b.setAttribute('aria-expanded','true')});
    input.focus();input.select();
    load(cfg.lang);if(alsoOn())load(cfg.other);
    run();
  }
  function close(){
    if(!isOpen())return;
    panel.hidden=true;scrim.hidden=true;
    header.classList.remove('search-open');document.body.classList.remove('search-lock');
    window.dispatchEvent(new Event('scroll'));                                // header colour back to normal
    openers.forEach(function(b){b.setAttribute('aria-expanded','false')});
    if(back&&back.focus&&document.contains(back))back.focus();
  }
  function options(){return box.querySelectorAll('[role="option"]')}
  function setActive(i){
    var os=options();active=os.length?(i+os.length)%os.length:-1;
    os.forEach(function(o,j){o.setAttribute('aria-selected',j===active);o.classList.toggle('on',j===active)});
    if(active>=0){input.setAttribute('aria-activedescendant',os[active].id);os[active].scrollIntoView({block:'nearest'})}
    else input.removeAttribute('aria-activedescendant');
  }
  function run(){
    var q=input.value.trim(),my=++seq;
    active=-1;input.removeAttribute('aria-activedescendant');
    if(q.length<MIN_CHARS){box.innerHTML='<p class="sp-hint">'+esc(S.hint)+'</p>';input.setAttribute('aria-expanded','false');status.textContent='';return}
    if(!box.firstChild||!box.querySelector('.sp-group,.sp-empty'))box.innerHTML='<p class="sp-hint">'+esc(S.loading)+'</p>';
    indexes().then(function(idx){
      if(my!==seq)return;
      var res=search(q,idx);
      if(!res.list.length){box.innerHTML=empty(q,true);status.textContent=S.none+' «'+q+'»'}
      else{box.innerHTML=groups(res,PER_GROUP,true)+'<a class="sp-all" id="sp-all" role="option" aria-selected="false" href="'+esc(pageUrl(q))+'">'+esc(S.all)+' ('+res.list.length+') <span aria-hidden="true">'+(cfg.lang==='ar'?'←':'→')+'</span></a>';
        status.textContent=res.list.length+' '+S.count}
      input.setAttribute('aria-expanded','true');
    }).catch(function(){if(my===seq)box.innerHTML=empty(q,true)});
  }
  var timer;
  input.addEventListener('input',function(){clearTimeout(timer);timer=setTimeout(run,90)});
  input.addEventListener('keydown',function(e){
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();var n=options().length;if(!n)return;setActive(active<0?(e.key==='ArrowDown'?0:n-1):active+(e.key==='ArrowDown'?1:-1))}
    else if(e.key==='Enter'){var os=options();if(active>=0&&os[active]){e.preventDefault();window.location.href=os[active].href}}
  });
  panel.querySelector('.sp-form').addEventListener('submit',function(e){if(input.value.trim().length<MIN_CHARS)e.preventDefault()});
  openers.forEach(function(b){b.addEventListener('click',function(){isOpen()?close():open()})});
  document.querySelectorAll('[data-close-search]').forEach(function(b){b.addEventListener('click',close)});
  document.addEventListener('mousedown',function(e){if(isOpen()&&!panel.contains(e.target)&&!e.target.closest('[data-open-search]'))close()});
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'&&isOpen()){e.preventDefault();close();return}
    var t=e.target,typing=t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    if((e.key==='k'||e.key==='K')&&(e.ctrlKey||e.metaKey)&&!e.altKey){e.preventDefault();open();return}
    if(e.key==='/'&&!typing&&!e.ctrlKey&&!e.metaKey&&!e.altKey){e.preventDefault();open()}
  });
  wireAlso(panel.querySelector('.sp-also'),function(){if(isOpen())run();if(page)runPage()});

  // ---------- search page (/search/?q=...) ----------
  var page=document.querySelector('[data-search-page]'),runPage=function(){};
  if(page){
    var pin=page.querySelector('.sp-input'),pbox=page.querySelector('.sp-results'),pcount=page.querySelector('.sp-count'),pseq=0;
    runPage=function(){
      var q=pin.value.trim(),my=++pseq;
      try{history.replaceState(null,'',q?pageUrl(q):cfg.page)}catch(e){}
      if(q.length<MIN_CHARS){pbox.innerHTML=q?'<p class="sp-hint">'+esc(S.hint)+'</p>':'';pcount.textContent='';return}
      indexes().then(function(idx){
        if(my!==pseq)return;
        var res=search(q,idx);
        pbox.innerHTML=res.list.length?groups(res,0,false):empty(q,false);
        pcount.textContent=res.list.length?res.list.length+' '+S.count:'';
      }).catch(function(){if(my===pseq)pbox.innerHTML=empty(q,false)});
    };
    var q0='';try{q0=new URLSearchParams(location.search).get('q')||''}catch(e){}
    pin.value=q0;
    var ptimer;pin.addEventListener('input',function(){clearTimeout(ptimer);ptimer=setTimeout(runPage,120)});
    page.querySelector('.sp-form').addEventListener('submit',function(e){e.preventDefault();runPage()});
    wireAlso(page.querySelector('.sp-also'),function(){runPage();if(isOpen())run()});
    if(q0)runPage();else pin.focus();
  }
})();
